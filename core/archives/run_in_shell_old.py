import subprocess, shlex, logging, time, pathlib, sys, os, signal, traceback, json, datetime, tempfile, pickle
import threading
from abc import ABC, abstractmethod
from typing import Union

project_dir = str(pathlib.Path(__file__).resolve().parents[0])
sys.path.append(project_dir)

from logger import getLogger
from utils import try_except, get_uuid, DictStorage, get_time_diff
from rabbitmq_service import PikaPubSub
from registry_manager import RegistryManager
from data_models import ModuleStatus, ModuleRegistry, Stdout
from mogodb_service import MongodbService
from file_handlers import LocalFileHandler

logger = getLogger(__file__)



class RunInShell(ABC):
    def __init__(self,module, tool, publish=True,shell_command="ls") -> None:

        self.token = get_uuid(size=8)
        self.channel = f"/task/{self.token}"
        self.logs_channel = f"/task/{self.token}/logs"

        ## Set instance parameters
        self.module = module
        self.tool = tool
        self.shell_command = shell_command
        self.publish = publish
        self.pika_pub_sub = None
        self.pika_log_pub = None
        self.process = None
      
        self.listen_event = threading.Event()
        self.register_event = threading.Event()
        self.registry_manager = RegistryManager()
        
        

         ## Initialize runtime parameters
        self.reset()
            
        
        self.is_waiting = False
        
        # Storage
        self.mongodb_client = MongodbService(table_name="tasks")        
        self.local_file_handler = LocalFileHandler(destination_prefix=self.file_storage_prefix)
        
       

        
    def reset(self):
        
        self.task_id = get_uuid(size=8)
        self.is_process_running = False
        
        self.status = self.update_status(status=ModuleStatus.waiting)
        self.run_parameters = {}
        self.stdout_storage = []
        self.process = None
        

        self.file_storage_prefix = f"{self.module}/{self.tool}/{self.task_id}"
        if self.publish: 
            if self.pika_pub_sub is not None:
                self.pika_pub_sub.close_connection()
            self.pika_pub_sub = PikaPubSub(queue_name=self.channel)

            if self.pika_log_pub is not None:
                self.pika_log_pub.close_connection()
            self.pika_log_pub = PikaPubSub(queue_name=self.logs_channel)
            

    def save(self):
        task_data = {}
        task_data["stdout"] = self.stdout_storage
        task_data["parameters"] = self.run_parameters
        task_data.update(self.status)
        try:
            self.mongodb_client.insert(data=task_data)
        except:
            logger.exception("mongodb inserting task data")
            dir_path = os.path.join(self.local_file_handler.get_data_dir(), self.file_storage_prefix)
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, "session_data.pickle")
            pickle.dump(task_data, open(file_path,mode='wb'))

    @try_except(logger=logger)
    def listen(self):
        self.is_waiting = True
        
        registry_scheduler =threading.Thread(target=self.register_on_schedule)
        registry_scheduler.start()

        while True:
            if self.listen_event.is_set():
                break
            try:
                logger.info(f"Waiting for  {self.channel}")
                self.pika_pub_sub.subscribe(self.consume)
            except KeyboardInterrupt:
                self.is_waiting = False
                break
            except BaseException:
                logger.exception("from RunInShell")
                self.is_waiting = False
                break
                
    def register_on_schedule(self,seconds=10):
        while True:
            if self.register_event.is_set():
                break
            try:
                self.__register_status()
                time.sleep(seconds)
            except KeyboardInterrupt:
                self.is_waiting = False
                break

    def __register_status(self):
        ## Update just the timestamp
        self.update_status(
            status=self.status["status"],
            info=self.status["info"],
            result=self.status["result"]
        )
        self.registry_manager.register_module(module_registry_message=self.status)

    def consume(self, ch, method, properties, body):
        print(" [x] Received %r" % body)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

        if body is not None: 
            message = json.loads(body)
            logger.info("received meassge: "+ str(message))
            if type(message) is dict:
                timestamp = message.get("timestamp","")
                minutes, secs = get_time_diff(timestamp)
                if int(minutes)==0 and secs<2:
                    command = message.get("cmd","")

                    if command == 'start':
                        self.run_parameters.update(message)
                        self.update_status(status=ModuleStatus.started)
                        self.process_input(parameters=self.run_parameters)
                        self.shell_command = self.run_command(parameters=self.run_parameters)
                        self.start()
                        self.__register_status()
                        self.pika_log_pub.publish(message=self.status)

                    elif command == 'pause':
                        self.pause()
                        message = self.update_status(status=ModuleStatus.paused)
                        self.__register_status()
                        self.pika_log_pub.publish(message=message)

                    elif command == 'resume':
                        self.resume()
                        message = self.update_status(status=ModuleStatus.resumed)
                        self.__register_status()
                        self.pika_log_pub.publish(message=message)

                    elif command == 'terminate':
                        self.terminate()
                        message = self.update_status(status=ModuleStatus.terminated)
                        self.__register_status()
                        self.pika_log_pub.publish(message=message)

                    elif command == 'status':
                        message = self.status
                        self.__register_status()
                        self.pika_log_pub.publish(message=message)

                    elif command == "close_client":   
                        message = self.update_status(status=ModuleStatus.terminated)
                        self.__register_status()
                        self.pika_log_pub.publish(message=message)
                        self.close()
                        sys.exit(0)
                else:
                    logger.info(f"Message obsolete {str(message)}")
        return

    def update_status(self, status:ModuleStatus, info="", result="") -> dict:
        self.status = ModuleRegistry(
            token=self.token,
            task_id=self.task_id, 
            module=self.module, 
            tool=self.tool, 
            last_seen=datetime.datetime.now().isoformat(), 
            is_running=self.is_process_running, 
            status=status if type(status) == str else status.value,
            info=info,
            result=result
        ).dict()
        return self.status

   

    def start(self):
        shell_command_args = shlex.split(self.shell_command)

        logger.info('Subprocess: "' + self.shell_command + '"')

        try:
            logger.info(self.channel + ":" +'starting process')
    
            if self.publish:
                self.update_status(status=ModuleStatus.running, info='starting process')
                self.pika_log_pub.publish( message=self.status)

            self.process = subprocess.Popen(
                shell_command_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            ) 
         
            stdout_thread = threading.Thread(target=self.__capture_stdout, args=(self.process,))
            stdout_thread.start()
            logger.info(self.channel + ":" +'start succeded!')
            if self.publish:
                self.update_status(status=ModuleStatus.running, info='start succeded!')
                self.pika_log_pub.publish( message={'info': self.status})
            return True
       
        except BaseException:
            error = traceback.format_exc()
            self.on_failure(error=error, process_name="starting")

        return False
       
    def terminate(self):
        try:
            if self.process is not None:
                logger.info(self.channel + ":" +'terminating process')
                if self.publish:
                    self.pika_log_pub.publish( message={'info': 'terminating process'})

                self.process.terminate()
                if self.process.poll() is None:
                    self.process.kill()
                    # os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                logger.info(self.channel + ":" +'terminate succeded!')
                if self.publish:
                    self.pika_log_pub.publish( message={'info': 'terminate succeded!'})
                self.is_process_running = False
                return True

        except BaseException:
            error = traceback.format_exc()
            self.on_failure(error=error, process_name="terminating")
       
        return False

    def pause(self):
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    logger.info(self.channel + ":" +'pausing process')
    
                    if self.publish:
                        self.pika_log_pub.publish( message={'info': 'pausing process'})

                    self.process.send_signal(signal.SIGSTOP)

                    logger.info(self.channel + ":" +'pause succeded!')
                    if self.publish:
                        self.pika_log_pub.publish( message={'info': 'pause succeded!'})
                    self.is_process_running = False
                    return True
        except BaseException:
            error = traceback.format_exc()
            self.on_failure(error=error, process_name="pausing")
       
        return False

    def resume(self):
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    logger.info(self.channel + ":" +'resuming process')
    
                    if self.publish:
                        self.pika_log_pub.publish( message={'info': 'resuming process'})

                    self.process.send_signal(signal.SIGCONT)
                    os.kill(self.process.pid, signal.SIGCONT)
                    

                    logger.info(self.channel + ":" +'resume succeded!')
                    if self.publish:
                        self.pika_log_pub.publish( message={'info': 'resume succeded!'})
                    self.is_process_running = True
                    return True

        except BaseException:
            error = traceback.format_exc()
            self.on_failure(error=error, process_name="resuming")
       
        return False
        
    def close(self):
        self.terminate()
        if self.pika_log_pub is not None:
            self.pika_log_pub.close_connection()
        if self.pika_pub_sub is not None:
            self.pika_pub_sub.close_connection()
        self.listen_event.set()
        self.register_event.set()
        self.registry_manager.close()
        
    def __capture_stdout(self, process: subprocess.Popen):
        self.is_process_running = True
       
        try:
            while process.poll() is None:
                output = process.stdout.read1().decode('utf-8')
                for i, line in enumerate(output.strip().split('\n')):
                    self.stdout_storage.append(line)
                    if len(line.strip())>0:
                        if self.publish:
                            message = self.make_stdout(line_number=i,line=line)
                            self.pika_log_pub.publish( message=message)
                        logger.info(str(message))
                    # save on interval here - update mongodb task storage
                    # ---------------

                time.sleep(0.1)
            self.is_process_running = False
            if self.publish:
                status = self.update_status(status=ModuleStatus.success, info='Task succeded! Now processing the output...')
                self.pika_log_pub.publish( message=status)
            self.on_success()

        except BaseException:
            error = traceback.format_exc()
            self.is_process_running = False
            self.on_failure(error=error, process_name="capturing stdout from")
        finally:
            self.is_process_running = False

    def on_success(self):
        return_data = self.process_output(self.run_parameters)
        # NOTE maybe handle results here?
        
        message = self.update_status(status=ModuleStatus.success, info="result available", result=return_data)
        logger.info(str(message))

        if self.publish:
            self.__register_status()
            self.pika_log_pub.publish( message=message)

        self.save()
        self.listen_event.set()
        self.reset()
        time.sleep(1)
        self.listen_event.clear()
        self.listen()

    def on_failure(self, error, process_name):
        info = f'Exception occured while {process_name} subprocess: \n' + str(error)
        status = self.update_status(status=ModuleStatus.failed, info=info)
        logger.exception((str(status)))
        if self.publish:
            self.__register_status()
            self.pika_log_pub.publish( message=status)
        
        self.save()
        self.listen_event.set()
        self.reset()
        time.sleep(1)
        self.listen_event.clear()
        self.listen()

    def make_stdout(self, line_number, line ):
        percent, loglevel, message = self.parse_stdout(line)
        return Stdout(
            task_id=self.task_id, 
            percent=percent, level=loglevel,
            line_number=line_number,
            message=message
        ).dict()

    @abstractmethod 
    def run_command(self, parameters:dict) -> str:
        """
        Pass in arguments based on the recived parameters if needed
        Otherwise just return the original shell command
        """
        return self.shell_command

    @abstractmethod  
    def parse_stdout(self, line:str) -> Union[int, str, str]:
        """
        Parse to the stdout line to extract 
        1) progress percentage
        2) log level
        3) clean message
        """
        percent = 10
        loglevel = "info"
        message = line
        return percent, loglevel, message
    
    @abstractmethod
    def process_input(self, parameters:dict) -> None:
        data_directory = self.local_file_handler.get_data_dir()
        # Read point cloud from .las
        # ....
        # Write point cloud to .pb
        # .....
        temp = tempfile.NamedTemporaryFile(suffix='.pb')
        temp.write("test content .....")

        ## copy to local / shared  storage
        input_file_path = self.local_file_handler.copy_to_shared_folder(source_file_path=temp.name)
        parameters['input_file_path'] = input_file_path

        temp.close()
        

    @abstractmethod    
    def process_output(self, parameters:dict) -> str:
        # Return path to the result extracted from stdout or parameters
        ## example: output = ",".join(self.stdout_storage[-3:])
        # print(parameters['input_file_path'])
        output = self.stdout_storage[-1]
        return output

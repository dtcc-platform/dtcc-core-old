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



class PubSubBase(ABC):
    def __init__(self,module, tool, publish=True) -> None:

        self.token = get_uuid(size=8)
        self.channel = f"/task/{self.token}"
        self.logs_channel = f"/task/{self.token}/logs"

        ## Set instance parameters
        self.module = module
        self.tool = tool
   
        self.publish = publish
        self.pika_pub_sub = None
        self.pika_log_pub = None
        self.process = None
      
        self.listen_event = threading.Event()
        self.register_event = threading.Event()
        if publish:
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
            self.pika_pub_sub = PikaPubSub(queue_name=self.channel)
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
                        self.start()
                        
                    elif command == 'pause':
                        self.pause()
                        self.update_status(status=ModuleStatus.paused)

                    elif command == 'resume':
                        self.resume()
                        self.update_status(status=ModuleStatus.resumed)

                    elif command == 'stop':
                        self.stop()
                        self.update_status(status=ModuleStatus.stopped)

                    elif command == "terminate":   
                        self.update_status(status=ModuleStatus.terminated, info="closed client loop for the tool")
                        self.__register_status()
                        self.pika_log_pub.publish(message=message)
                        self.close()
                        sys.exit(0)
                    
                    self.__register_status()
                    self.pika_log_pub.publish(message=self.status)
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

   
        
    def close(self):
        if self.pika_log_pub is not None:
            self.pika_log_pub.close_connection()
        if self.pika_pub_sub is not None:
            self.pika_pub_sub.close_connection()
        self.listen_event.set()
        self.register_event.set()
        self.registry_manager.close()
        

    def on_success(self,result:str):
        # NOTE maybe handle results here?
        
        message = self.update_status(status=ModuleStatus.success, info="result available", result=result)
        logger.info(str(message))

        if self.publish:
            self.__register_status()
            self.pika_log_pub.publish(message=message)

        self.save()
        self.listen_event.set()
        self.reset()
        time.sleep(1)
        self.listen_event.clear()
        if self.publish:
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
        if self.publish:
            self.listen()

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def resume(self):
        pass

    @abstractmethod
    def stop(self):
        pass


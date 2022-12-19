import subprocess, shlex, logging, time, pathlib, sys, os, signal, traceback, json, datetime, tempfile, pickle
import threading
from abc import ABC, abstractmethod
from typing import Union

project_dir = str(pathlib.Path(__file__).resolve().parents[0])
sys.path.append(project_dir)

from logger import getLogger
from data_models import ModuleStatus, Stdout
from pub_sub_base import PubSubBase

logger = getLogger(__file__)



class RunInShell(PubSubBase):
    def __init__(self,module, tool, publish=True) -> None:

        PubSubBase.__init__(self,
            module=module,
            tool=tool,
            publish=publish
        )

        self.shell_command = ""
   

    def start(self):
        
        try:
            self.update_status(status=ModuleStatus.processing_input)
            self.process_input(parameters=self.run_parameters)
            self.shell_command = self.run_command(parameters=self.run_parameters)
            shell_command_args = shlex.split(self.shell_command)

            logger.info('Subprocess: "' + self.shell_command + '"')
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
       
    def stop(self):
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


  
        
    def __capture_stdout(self, process: subprocess.Popen):
        self.is_process_running = True
       
        try:
            line_number = 0
            while process.poll() is None:
                output = process.stdout.read1().decode('utf-8')
                for i, line in enumerate(output.strip().split('\n')):
                    self.stdout_storage.append(line)
                    if len(line.strip())>0:
                        message = self.make_stdout(line_number=line_number,line=line)
                        if self.publish:
                            self.pika_log_pub.publish( message=message)
                        logger.info(str(message))
                        line_number += 1
                    # TODO save on interval here - update mongodb task storage
                    # ---------------

                time.sleep(0.01)
            self.is_process_running = False
            if self.publish:
                status = self.update_status(status=ModuleStatus.success, info='Task succeded! Now processing the output...')
                self.pika_log_pub.publish( message=status)

            self.update_status(status=ModuleStatus.processing_output)
            result = self.process_output(self.run_parameters)
            self.on_success(result=result)

        except BaseException:
            error = traceback.format_exc()
            self.is_process_running = False
            self.on_failure(error=error, process_name="capturing stdout from")
        finally:
            self.is_process_running = False


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

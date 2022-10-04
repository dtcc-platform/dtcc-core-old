import os, pathlib, sys, json, time
import subprocess, shlex, logging, time, pathlib, sys, os, threading, signal, traceback, json

from abc import ABC, abstractmethod

project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from src.common.utils import get_uuid, try_except, timer
from src.common.logger import getLogger
from src.common.rabbitmq_service import PikaPublisher
from src.common.redis_service import RedisPubSub

logger = getLogger(__file__)



class TaskRunnerSubscriberInterface(ABC):

    def __init__(self, task_name:str, shell_command:str, publish:bool) -> None:
        self.channel = task_name
        self.publish = publish
        self.logs_channel = self.channel + "/logs"
        if publish: 
            self.rps = RedisPubSub()
            self.pika_pub = PikaPublisher(queue_name=self.logs_channel)

        self.shell_command = shell_command

    @try_except(logger=logger)
    def run_subscriber(self):
        while True:
            logger.info(f"Waiting for  {self.channel}")
            raw_message = self.rps.subscribe_one(channel=self.channel,wait_forever=True)

            if raw_message is not None: 
                message = json.loads(raw_message)
                logger.info("received meassge: ", message)
                if type(message) is dict:
                    command = message.get("cmd","")

                    if command == 'start':
                        updated_shell_command = self.process_arguments_on_start(message=message)
                        self.__start(
                            command=updated_shell_command
                        )
                        message = {'status':'started'}
                        self.rps.publish(channel=self.channel, message=json.dumps(message))

                    elif command == 'pause':
                        self.pause()
                        message = {'status':'paused'}
                        self.rps.publish(channel=self.channel, message=json.dumps(message))

                    elif command == 'resume':
                        self.resume()
                        message = {'status':'resumed'}
                        self.rps.publish(channel=self.channel, message=json.dumps(message))

                    elif command == 'terminate':
                        self.terminate()
                        message = {'status':'terminated'}
                        self.rps.publish(channel=self.channel, message=json.dumps(message))

                    elif command == "close_client_loop":   
                        message = {'status':'closed_client_loop'}
                        self.rps.publish(channel=self.channel, message=json.dumps(message))
                        self.task_runner.close()
                        break

    def start(self):
        updated_shell_command = self.process_arguments_on_start(message={})
        return self.__start(
                    command=updated_shell_command
                )

    def __start(self, command:str):
        command_args = shlex.split(command)

        logger.info('Subprocess: "' + command + '"')

        try:
            logger.info(self.channel + ":" +'starting process')
    
            if self.publish:
                self.pika_pub.publish( message={'info': 'starting process'})

            self.process = subprocess.Popen(
                command_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ) 
         
            stdout_thread = threading.Thread(target=self.__capture_stdout, args=(self.process,))
            stdout_thread.start()
            logger.info(self.channel + ":" +'start succeded!')
            if self.publish:
                self.pika_pub.publish( message={'info': 'start succeded!'})
            return True
       
        except BaseException:
            error = traceback.format_exc()
            logger.exception(self.channel + ":" +'Exception occured while starting subprocess')
            if self.publish:
                self.pika_pub.publish( message={'error': 'Exception occured while starting subprocess: \n' + str(error)})
            return False
       
    def terminate(self):
        try:
            if self.process is not None:
                logger.info(self.channel + ":" +'terminating process')
                if self.publish:
                    self.pika_pub.publish( message={'info': 'terminating process'})

                self.process.terminate()
                if self.process.poll() is None:
                    self.process.kill()
                    # os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                logger.info(self.channel + ":" +'terminate succeded!')
                if self.publish:
                    self.pika_pub.publish( message={'info': 'terminate succeded!'})
                return True

        except BaseException:
            error = traceback.format_exc()
            logger.exception(self.channel + ":" +'Exception occured while terminating subprocess')
    
            if self.publish:
                self.pika_pub.publish( message={'error': 'Exception occured while terminating subprocess: \n  ' + error})
       
        return False

    def pause(self):
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    logger.info(self.channel + ":" +'pausing process')
    
                    if self.publish:
                        self.pika_pub.publish( message={'info': 'pausing process'})

                    self.process.send_signal(signal.SIGSTOP)

                    logger.info(self.channel + ":" +'pause succeded!')
                    if self.publish:
                        self.pika_pub.publish( message={'info': 'pause succeded!'})
                    return True
        except BaseException:
            error = traceback.format_exc()
            logger.exception(self.channel + ":" +'Exception occured while pausing subprocess')
    
            if self.publish:
                self.pika_pub.publish( message={'error': 'Exception occured while pausing subprocess: \n  ' + error})
       
        return False

    def resume(self):
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    logger.info(self.channel + ":" +'resuming process')
    
                    if self.publish:
                        self.pika_pub.publish( message={'info': 'resuming process'})

                    self.process.send_signal(signal.SIGCONT)
                    os.kill(self.process.pid, signal.SIGCONT)
                    

                    logger.info(self.channel + ":" +'resume succeded!')
                    if self.publish:
                        self.pika_pub.publish( message={'info': 'resume succeded!'})
                    return True

        except BaseException:
            error = traceback.format_exc()
            logger.exception(self.channel + ":" +'Exception occured while resuming subprocess')
    
            if self.publish:
                self.pika_pub.publish( message={'error': 'Exception occured while resuming subprocess: \n  ' + error})
        
       
        return False
        
    def close(self):
        self.terminate()
        if self.pika_pub is not None:
            self.pika_pub.close_connection()
        
    def __capture_stdout(self, process: subprocess.Popen):
       
        try:
            while process.poll() is None:
                output = process.stdout.read1().decode('utf-8')
                for i, line in enumerate(output.strip().split('\n')):
                    if len(line.strip())>0:
                        if self.publish:
                            self.pika_pub.publish( message={'log':line})
                        logger.info(self.channel + ": " +line)
                time.sleep(0.1)
            if self.publish:
                self.pika_pub.publish( message={'info': 'Task succeded!'})
            self.on_success()

        except BaseException:
            error = traceback.format_exc()
            logger.exception(self.channel + ":" +'Exception occured while capturing stdout from subprocess')

            self.on_failure()
            if self.publish:
                self.pika_pub.publish( message={'error': 'Exception occured while capturing stdout from subprocess: \n  ' + error})
    

    def on_success(self):
        return_data = self.process_return_data()
        # NOTE maybe handle results here?
        
        message = json.dumps({'status':'success', 'data':return_data})
        logger.info(self.channel + message)

        if self.publish:
            self.rps.publish(channel=self.channel, message=message)
    

  
    def on_failure(self):
        logger.info(self.channel + ": Failed!")
        message = json.dumps({'status':'failed'})
        if self.publish:
            self.rps.publish(channel=self.channel, message=message)

    @abstractmethod    
    def process_return_data(self):
        return "dummy result"

    
    @abstractmethod
    def process_arguments_on_start(self, message:dict) -> str:
        """
        Pass in arguments based on the recived message if needed
        Otherwise just return the original shell command
        """
        return self.shell_command


# Examples and tests
# ------------------

class SamplePythonProcessRunner(TaskRunnerSubscriberInterface):
    def __init__(self, publish=False) -> None:
        sample_logger_path = os.path.join(project_dir, "src/tests/sample_logging_process.py")
        command=f'python3 {sample_logger_path}'

        TaskRunnerSubscriberInterface.__init__(self,
            task_name="run_sample_python_process",
            publish=publish,
            shell_command=command
        )

    def process_arguments_on_start(self, message:dict):
        return self.shell_command

    def process_return_data(self):
        return "dummy result"


def test_run_from_terminal():
    sample_process_runner = SamplePythonProcessRunner()
    sample_process_runner.start()
    time.sleep(1)

    if sample_process_runner.pause():
        for i in range(5):
            print(i)
            time.sleep(1)

    if sample_process_runner.resume():
        for i in range(2):
            print(i)
            time.sleep(1)

    if sample_process_runner.pause():
        for i in range(5):
            print(i)
            time.sleep(1)

    sample_process_runner.terminate()


def test_run_from_dtcc_core():
    sample_process_runner = SamplePythonProcessRunner(publish=True)
    sample_process_runner.run_subscriber()

if __name__ == '__main__':
    test_run_from_dtcc_core()
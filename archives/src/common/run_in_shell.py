import subprocess, shlex, logging, time, pathlib, sys, os, threading, signal, traceback, json

from abc import ABC, abstractmethod

project_dir = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(project_dir)

from src.common.logger import getLogger
from src.common.rabbitmq_service import PikaPublisher
from src.common.redis_service import RedisPubSub

logger = getLogger(__file__)



class RunInShell(ABC):
    def __init__(self,channel="/", publish=True) -> None:
        self.channel = channel
        self.logs_channel 
        self.publish = publish
        if publish: 
            self.pika_pub = PikaPublisher(queue_name=channel)
        self.process = None
        self.rps = RedisPubSub()
        

    def start(self, command:str, on_success_callback=None, on_failure_callback=None):
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
         
            # stdout_thread = threading.Thread(target=self.__capture_stdout, args=(self.process,on_success_callback,on_failure_callback))
            # stdout_thread.start()
            self.__capture_stdout(self.process, on_success=on_success_callback, on_failure=on_failure_callback)
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
            #if on_success is not None:
            self.on_success()

        except BaseException:
            error = traceback.format_exc()
            logger.exception(self.channel + ":" +'Exception occured while capturing stdout from subprocess')

            self.on_failure()
            if self.publish:
                self.pika_pub.publish( message={'error': 'Exception occured while capturing stdout from subprocess: \n  ' + error})
    

    def on_success(self):
        logger.info("###################### on success called !!!!!!")
        return_data = self.process_return_data()
        # NOTE maybe handle results here?
        
        message = json.dumps({'status':'success', 'data':return_data})
        logger.info(self.channel + message)

        if self.publish:
            self.rps.publish(channel=self.channel, message=message)
    

  
    def on_failure(self):
        # NOTE maybe handle results here?
        logger.info(self.channel + ": Failed!")
        message = json.dumps({'status':'failed'})
        if self.publish:
            self.rps.publish(channel=self.channel, message=message)

    @abstractmethod    
    def process_return_data(self):
        return "dummy result"
    

def test_run_in_shell(publish=False):
    sample_logger_path = os.path.join(project_dir, "src/tests/sample_logging_process.py")
    command=f'python3 {sample_logger_path}'

    run_in_shell = RunInShell(channel='test',publish=publish)

    run_in_shell.start(command=command)
    time.sleep(1)

    if run_in_shell.pause():
        for i in range(3):
            print(i)
            time.sleep(1)

    if run_in_shell.resume():
        for i in range(2):
            print(i)
            time.sleep(1)

    run_in_shell.terminate()


if __name__=="__main__":
    test_run_in_shell(publish=False)
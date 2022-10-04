import os, pathlib, sys, json, time

from abc import ABC, abstractmethod

project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from src.common.utils import get_uuid, try_except, timer
from src.common.logger import getLogger
from src.common.redis_service import RedisPubSub
from src.common.run_in_shell import RunInShell

logger = getLogger(__file__)



class TaskRunnerSubscriberInterface(ABC):

    def __init__(self, task_name:str, shell_command:str, publish:bool) -> None:
        self.channel = task_name
        self.logs_channel = self.channel + "/logs"
        self.rps = RedisPubSub()

        self.task_runner = RunInShell(channel=self.logs_channel, publish=publish)

        self.shell_command = shell_command

    @try_except(logger=logger)
    def run(self):
        while True:
            logger.info(f"Waiting for  {self.channel}")
            raw_message = self.rps.subscribe_one(channel=self.channel,wait_forever=True)

            message = json.loads(raw_message)
            logger.info("received meassge: ", message)

            command = message['cmd']

            if command == 'start':
                updated_shell_command = self.process_arguments_on_start(message=message)
                self.task_runner.start(
                    command=updated_shell_command, 
                    on_success_callback=self.on_success,
                    on_failure_callback=self.on_failure
                )

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
        updated_command = self.process_arguments_on_start(message=message)
        return self.task_runner.start(command=updated_command)

    def pause(self):
        return self.task_runner.pause()

    def resume(self):
        return self.task_runner.resume()

    def terminate(self):
        return self.task_runner.terminate()

    @abstractmethod    
    @try_except
    def process_return_data(self):
        return ""

    @try_except
    def on_success(self):
        return_data = self.process_return_data()
        # NOTE maybe handle results here?
        logger.info(self.channel + ": Success!")
        message = {'status':'success', 'data':return_data}
        self.rps.publish(channel=self.channel, message=json.dumps(message))
    

    @try_except
    def on_failure(self):
        # NOTE maybe handle results here?
        logger.info(self.channel + ": Falied!")
        message = {'status':'failed'}
        self.rps.publish(channel=self.channel, message=message)

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
    sample_process_runner.run()

if __name__ == '__main__':
    test_run_from_dtcc_core()
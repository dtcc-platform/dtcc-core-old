import sys,os
import pathlib

project_dir = str(pathlib.Path(__file__).resolve().parents[3])
print(project_dir)
sys.path.append(project_dir)

from task_runner_subscriber import TaskRunnerSubscriberInterface

class GenerateTest(TaskRunnerSubscriberInterface):
    def __init__(self, publish=False) -> None:
        command = f'./ls_out.sh'
        
        TaskRunnerSubscriberInterface.__init__(self,
            task_name="/task/dtcc/generate-test",
            publish=publish,
            shell_command=command
        )

    def process_return_data(self):
        with open("./ls_out.txt",'r') as src:
            data = src.readlines()
        return data[-1]
    def process_arguments_on_start(self, message:dict):
        return f'{self.shell_command}'

if __name__ == '__main__':
    gtest = GenerateTest(publish=True)
    gtest.run()
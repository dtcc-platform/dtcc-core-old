project_dir = str(pathlib.Path(__file__).resolve().parents[3])
print(project_dir)
sys.path.append(project_dir)

from task_runner_subscriber import TaskRunnerSubscriberInterface

class GenerateTest(TaskRunnerSubscriberInterface):
    def __init__(self, publish=False) -> None:
        command = f'ls'
        

        TaskRunnerSubscriberInterface.__init__(self,
            task_name="generate-test",
            publish=publish,
            shell_command=command
        )

    def process_return_data(self):
        with open("ls_out.txt",'r') as src:
            data = src.readlines()
        return data[-1]
    def process_arguments_on_start(self, message:dict):

        return f'{self.shell_command}   |tee ls_out.txt'
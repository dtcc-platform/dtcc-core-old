#!/usr/bin/python3 

from task_runner_subscriber import TaskRunnerSubscriberInterface

class GenerateMesh(TaskRunnerSubscriberInterface):
    def __init__(self, publish=False) -> None:
        command = f'bin/dtcc-generate-mesh'
        

        TaskRunnerSubscriberInterface.__init__(self,
            task_name="/task/dtcc/generate-mesh",
            publish=publish,
            shell_command=command
        )

    def process_arguments_on_start(self, message:dict):
        self.outputDirectory = message.get("OutputDirectory")
        self.inputDirectory = message.get("InputDirectory","")
        if self.outputDirectory is None:
            self.outputDirectory = self.inputDirectory
        return f'self.shell_command {self.inputDirectory}'


if __name__ == '__main__':
    gmesh = GenerateMesh(publish=True)
    gmesh.run_subscriber()
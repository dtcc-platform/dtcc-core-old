from task_runner_subscriber import TaskRunnerSubscriberInterface

class DtccGenerateCitymodel(TaskRunnerSubscriberInterface):
    def __init__(self, publish=False) -> None:
        command = f'bin/dtcc-generate-citymodel'
        

        TaskRunnerSubscriberInterface.__init__(self,
            task_name="dtcc-generate-citymodel",
            publish=publish,
            shell_command=command
        )

    def process_arguments_on_start(self, message:dict):
        return self.shell_command

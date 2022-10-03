from task_runner_subscriber import TaskRunnerSubscriberInterface

class DtccGenerateMesh(TaskRunnerSubscriberInterface):
    def __init__(self, publish=False) -> None:
        command = f'bin/dtcc-generate-mesh'
        

        TaskRunnerSubscriberInterface.__init__(self,
            task_name="dtcc-generate-mesh",
            publish=publish,
            shell_command=command
        )

    def process_arguments_on_start(self, message:dict):
        return self.shell_command

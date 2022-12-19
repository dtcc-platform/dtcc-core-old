import time, pathlib, sys, os, tempfile
from typing import Union

project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from run_in_shell import RunInShell



class SamplePythonProcessRunner(RunInShell):
    def __init__(self, publish=False) -> None:
        

        RunInShell.__init__(self,
            module="run_sample_python_process",
            tool="test",
            publish=publish
        )

    def run_command(self, parameters:dict) -> str:
        """
        Pass in arguments based on the recived parameters if needed
        Otherwise just return the original shell command
        """
        sample_logger_path = os.path.join(project_dir, "tests/sample_logging_process.py")
        self.shell_command = f'python3 {sample_logger_path}'
        return self.shell_command
 
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
    
    def process_input(self, parameters:dict) -> str:
        data_directory = self.local_file_handler.get_data_dir()
        # Read point cloud from .las
        # ....
        # Write point cloud to .pb
        # .....
        temp = tempfile.NamedTemporaryFile(suffix='.pb')
        temp.write("test content .....".encode())
        ## copy to local / shared  storage
        # input_file_path = self.local_file_handler.copy_to_shared_folder(source_file_path=temp.name)

        temp.close()
        
   
    def process_output(self, parameters:dict) -> str:
        # Return path to the result extracted from stdout or parameters
        output = ",".join(self.stdout_storage[-3:])
        return output


if __name__=='__main__':
    sample_process = SamplePythonProcessRunner(publish=True)
    sample_process.listen()

    # sample_process = SamplePythonProcessRunner(publish=False)
    # sample_process.start()
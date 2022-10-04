import sys, os
import pathlib
datamodelio_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../../../dtcc-model/datamodel_io"))
sys.path.append(datamodelio_path)
from cityModel import loadCityModelJson

#print(sys.path[-1])
project_dir = str(pathlib.Path(__file__).resolve().parents[3])
print(project_dir)
sys.path.append(project_dir)
#test
from task_runner_subscriber import TaskRunnerSubscriberInterface

#/api/tasks/dtcc-generate-citymodel
#/api/tasks/dtcc/generate-citymodel

class GenerateCitymodel(TaskRunnerSubscriberInterface): 
    def __init__(self, publish=False) -> None:
        command = f'ls -l'

        TaskRunnerSubscriberInterface.__init__(self,
            task_name="dtcc-generate-citymodel",
            publish=publish,
            shell_command=command
        )

    def process_return_data(self):
        jsonPath = os.path.join(self.outputDirectory,"CityModel.json")
        citymodelString = loadCityModelJson(jsonPath,True)
        outputPath = os.path.join(self.outputDirectory,"CityModel.json.pb")
        with (os.path.join(self.outputDirectory,"CityModel.json.pb"), 'wb') as dst:
            dst.write(citymodelString)
        return outputPath
        

    def process_arguments_on_start(self, message:dict):
        self.outputDirectory = message.get("OutputDirectory")
        self.inputDirectory = message.get("InputDirectory","")
        if self.outputDirectory is None:
            self.outputDirectory = self.inputDirectory
        #return f'self.shell_command {self.inputDirectory}'
        return f'{self.shell_command}'

if __name__ == '__main__':
    gcm = GenerateCitymodel()
    gcm.start()
#/usr/bin/python3

import sys, os
import pathlib
datamodelio_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../../../dtcc-model/datamodel_io"))
sys.path.append(datamodelio_path)
from cityModel import loadCityModelJson
import uuid
import shutil

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
        command = f'/home/dtcc/dtcc-core/dtcc-builder/bin/dtcc-generate-citymodel'

        TaskRunnerSubscriberInterface.__init__(self,
            task_name="dtcc-generate-citymodel",
            publish=publish,
            shell_command=command
        )

    def process_arguments_on_start(self, message:dict):
        self.outputDirectory = message.get("OutputDirectory")
        self.inputDirectory = '/home/dtcc/dtcc-core/dtcc-builder/data/HelsingborgResidential2022' #message.get("InputDirectory","")
        if self.outputDirectory is None:
            self.outputDirectory = self.inputDirectory
        #return f'self.shell_command {self.inputDirectory}'
        return f'{self.shell_command} {self.inputDirectory}'

    def process_return_data(self):
        jsonPath = os.path.join(self.outputDirectory,"CityModel.json")
        citymodelString = loadCityModelJson(jsonPath,True)
        outputPath = os.path.join(self.outputDirectory,"CityModel.json.pb")
        with (outputPath, 'wb') as dst:
            dst.write(citymodelString)
        serveFileFrom = pathlib.Path('static') / str(uuid.uuid4())
        serveFileFrom.mkdir(exist_ok=True)
        shutil.copy(outputPath, serveFileFrom / 'CityModel.json.pb')
        return '/' + str(serveFileFrom / 'CityModel.json.pb')
        # "/static/1290-msd4-hjsd-s32d/CityModel.json.pb"

if __name__ == '__main__':
    gcm = GenerateCitymodel(publish=True)
    gcm.run_subscriber()
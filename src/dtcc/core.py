# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License

import os

from dtcc.model import *
import dtcc.json

# FIXME: Reading from the file system for now
DATA_DIRECTORY = '../data'

class Core:

    def __init__(self):
        'Constructor'
        pass

    #---------- API calls ----------

    def GetProjects(self):
        'Return a list of all available projects'
        return os.listdir(DATA_DIRECTORY)

    def GetDataSets(self, project):
        'Return a list of all datasets for given project'
        fileNames = os.listdir('%s/%s' % (DATA_DIRECTORY, project))
        dataSets = [f.split('.json')[0] for f in fileNames if f.endswith('.json')]
        return dataSets

    def GetData(self, project, dataSet):
        'Return given dataset for project'

        # Read from JSON file
        fileName = '%s/%s/%s.json' % (DATA_DIRECTORY, project, dataSet)
        object = dtcc.json.Read(fileName)

        # Serialize to protobuf
        pb = object.SerializeToString()

        return pb

    def GenerateData(self, project, dataSet):
        'Generate given dataset for project'

        print('GenerateData: Not implemented')

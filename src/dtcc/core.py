# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License

import os

from dtcc.model import *
from dtcc.logging import *
from dtcc.builder import *
from dtcc.iboflow import *

# FIXME: Reading from the file system for now
DATA_DIRECTORY = '../data'

class Core:
    """DTCC Core is the central component of DTCC Platform. Core relays
    messages between the various data sources, data generators and data
    visualization components that together form the platmform.
    """

    def __init__(self):
        'Constructor'

        # Create generators
        self.generators = [Builder(), IBOFlow()]

        # Generate maps to generators and class names
        self.generatorMap = {}
        self.classMap = {}
        for generator in self.generators:
            for name, cls in generator.GetDataSets():
                self.generatorMap[name] = generator
                self.classMap[name] = cls

    #---------- API calls ----------

    def GetProjects(self):
        'Return a list of all available projects'
        return Success(os.listdir(DATA_DIRECTORY), 'Returned list of available projects')

    def GetDataSetNames(self):
        'Return a list of all datasets that can be generated'
        names = []
        for generator in self.generators:
            names += [name for (name, cls) in generator.GetDataSets()]
        return Success(names, 'Returned list of datasets that can be generated')

    def GetGeneratedDataSetNames(self, project):
        'Return a list of all generated datasets for project'
        fileNames = os.listdir('%s/%s' % (DATA_DIRECTORY, project))
        names = [f.split('.pb')[0] for f in fileNames if f.endswith('.pb')]
        return Success(names, 'Returned list of generated datasets')

    def GetDataSet(self, project, name):
        'Return given dataset for project'

        # Check if dataset exists
        if not name in self.GetGeneratedDataSetNames(project):
            return Error('Unable to return dataset; dataset %s has not been generated for project %s' % (name, project))

        # Read data
        fileName = '%s/%s/%s.pb' % (DATA_DIRECTORY, project, name)
        with open(fileName, 'rb') as fileName:
            pb = f.read()

        return Success(pb, 'Returned dataset %s for project %s' % (name, project))

    def GenerateDataSet(self, project, name):
        'Generate dataset with given name for given project'

        # Check if generator exists
        if not name in self.generatorMap:
            return Error('Unable to generate dataset; no known generator for dataset %s' % name)

        # Get generator
        generator = self.generatorMap[name]

        # Generate data
        generator.GenerateDataSet(project, name)

        return Success(0, 'DTCC Core: Generated dataset %s for project %s' % (name, project))

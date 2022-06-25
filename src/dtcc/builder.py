# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License

from dtcc.model import *
from dtcc.logging import *

DATA_SETS = [('CityModel', CityModel),
             ('GroundSurface', Surface3D),
             ('BuildingdSurface', Surface3D),
             ('CitySurface', Surface3D)]

class Builder():
    'Interface to DTCC Builder'

    def __init__(self):
        'Constructor'
        pass

    def GetDataSets(self):
        'Return a list of all datasets that can be generated'
        return DATA_SETS

    def GenerateDataSet(self, project, name):
        'Generate dataset with given name for given project'
        Info('DTCC Builder: Generating dataset %s for project %s...' % (name, project))

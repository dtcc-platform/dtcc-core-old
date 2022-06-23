# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License

from dtcc.model import *
from dtcc.logging import *

DATA_SETS = [('VelocitySurface', SurfaceVectorField3D),
             ('PressureSurface', SurfaceField3D)]

class IBOFlow():
    'Interface to IBOFLow'

    def __init__(self):
        'Constructor'
        pass

    def GetDataSets(self):
        'Return a list of all datasets that can be generated'
        return DATA_SETS

    def GenerateDataSet(self, project, name):
        'Generate dataset with given name for given project'
        Info('DTCC Builder: Generating dataset %s for project %s...' % (name, project))
        pass

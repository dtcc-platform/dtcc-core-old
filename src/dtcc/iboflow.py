# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License

import h5py, numpy

from dtcc.model import *
from dtcc.logging import *
import dtcc.hdf5
import dtcc.protobuf

DATA_SETS = [('VelocitySurface', SurfaceVectorField3D),
             ('PressureSurface', SurfaceField3D),
             ('VelocityMagnitudeSurface', SurfaceField3D)]

class IBOFlow():
    'Interface to IBOFLow'

    def __init__(self):
        'Constructor'
        pass

    def GetDataSets(self):
        'Return a list of all datasets that can be generated'
        return DATA_SETS

    def GenerateDataSet(self, project, name, dataDirectory):
        'Generate dataset with given name for given project'
        Info('DTCC IBOFlow: Generating dataset %s for project %s...' % (name, project))

        # FIXME: Temporary implementation, just converting prebaked data

        # Read HDF5
        inFileName = '%s/%s/PostProcessedSurface.h5' % (dataDirectory, project)
        with h5py.File(inFileName, 'r') as f:

            # Get vertices
            h5Vertices = f['Geometry'][:]
            vertices = []
            for i in range(len(h5Vertices)):
                vertex = Vector3D()
                vertex.x = h5Vertices[i][0]
                vertex.y = h5Vertices[i][1]
                vertex.z = h5Vertices[i][2]
                vertices.append(vertex)

            # Get faces
            h5Faces = f['Topology'][:]
            faces = []
            for i in range(len(h5Faces)):
                face = Simplex2D()
                face.v0 = h5Faces[i][0]
                face.v1 = h5Faces[i][1]
                face.v2 = h5Faces[i][2]
                faces.append(face)

            # Get values
            if name == 'VelocitySurface':
                dataSet = SurfaceVectorField3D()
                values = f['Node']['VelocityFluid'][:].flatten()
            elif name == 'PressureSurface':
                dataSet = SurfaceField3D()
                values = f['Node']['PressureFluid'][:]
            elif name == 'VelocityMagnitudeSurface':
                dataSet = SurfaceField3D()
                v = f['Node']['VelocityFluid'][:]
                values = numpy.sum(numpy.abs(v)**2, axis=-1)**0.5
            else:
                # FIXME: How to pass this back as return code to core.py?
                Error('DTCC IBOFlow: Unknown data set %s' % name)

            # Set data
            dataSet.surface.vertices.extend(vertices)
            dataSet.surface.faces.extend(faces)
            dataSet.values.extend(values)

        # Write Protobuf
        outFileName = '%s/%s/%s.pb' % (dataDirectory, project, name)
        dtcc.protobuf.Write(dataSet, outFileName)

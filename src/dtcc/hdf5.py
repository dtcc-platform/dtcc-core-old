# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License
def ReadHDF5(fileName):
    'Read from HDF5 file'
    print('Reading JSON data from %s...' % fileName)

    # FIXME: Experimenting with reading HDF5
    with h5py.File(fileName, 'r') as f:
        print(f.keys())
        print(f['Geometry'])
        print(f['Cell'].keys())
        print(f['Cell']['VelocityFluid'])
        u = f['Cell']['VelocityFluid']
        print(u[100])

    # FIXME: This is a temporary hack to generate some data for the viewer
    surfaceField = SurfaceField3D()
    with open('GroundSurface.pb', 'rb') as f:
        surfaceField.surface.ParseFromString(f.read())
    n = len(surfaceField.surface.vertices)
    for i in range(n):
        z = surfaceField.surface.vertices[i].z
        surfaceField.surface.vertices[i].z = z + 10.0
    x = numpy.zeros(n)
    y = numpy.zeros(n)
    for i in range(n):
        x[i] = surfaceField.surface.vertices[i].x
        y[i] = surfaceField.surface.vertices[i].y
    x = (x - numpy.min(x)) / (numpy.max(x) - numpy.min(x))
    y = (y - numpy.min(y)) / (numpy.max(y) - numpy.min(y))
    r = numpy.sqrt((x - 0.5)**2 + (y - 0.5)**2)
    values = numpy.cos(25*r) / (1 + 3*r)
    surfaceField.values.extend(values)
    return surfaceField

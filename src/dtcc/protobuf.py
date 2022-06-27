# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License

from dtcc.model import *

def Write(object, fileName):
    'Write object to Protobuf file'
    print('Writing Protobuf data to %s...' % fileName)
    with open(fileName, 'wb') as f:
        pb = object.SerializeToString()
        f.write(pb)

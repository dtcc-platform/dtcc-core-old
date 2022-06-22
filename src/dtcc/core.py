# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License

from dtcc.model import *

def GetData():
    'Testing...'

    # Read some test data, figure out where it should be stored
    with open('FlowField.pb', 'rb') as f:
        pb = f.read()

    return pb

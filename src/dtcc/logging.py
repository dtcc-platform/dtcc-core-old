# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License

def Info(message=''):
    'Print message'
    print(str(message))

def Success(data, description, code=200, name='OK'):
     'Return success data structure'

     # Wrap return value
     output = {'code': code, 'name': name, 'description': description, 'data': data}

     # Print to stdout
     Info('Success: %s' % str(description))

     return output

def Error(description, code=400, name='Bad Request'):
    'Return error data structure'

    # Wrap return value
    output = {'code': code, 'name': name, 'description': description, 'data': {}}

    # Print to stdout
    Info('*** Error: %s' % str(description))

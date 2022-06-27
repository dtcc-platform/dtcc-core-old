# Copyright (C) 2022 Anders Logg
# Licensed under the MIT License

import json

from dtcc.model import *

def Read(fileName):
    'Read data from JSON file and return Protobub object'
    print('Reading JSON data from %s...' % fileName)

    # Read data from file
    with open(fileName, 'r') as f:
        jsonData = json.load(f)

    # Check for type information
    if not 'Type' in jsonData:
        Error('JSON data has missing type information')
    elif jsonData['Type'] == 'CityModel':
        print('Creating CityModel object...')
        cityModel = CityModel()
        buildings = []
        for jsonBuilding in jsonData['Buildings']:
            building = Building()
            building.uuid = jsonBuilding['UUID']
            building.height = jsonBuilding['Height']
            building.groundHeight = jsonBuilding['GroundHeight']
            vertices = []
            for jsonVertex in jsonBuilding['Footprint']:
                vertex = Vector2D()
                vertex.x = jsonVertex['x']
                vertex.y = jsonVertex['y']
                vertices.append(vertex)
            building.footPrint.shell.vertices.extend(vertices)
            buildings.append(building)
        cityModel.buildings.extend(buildings)
        return cityModel
    elif jsonData['Type'] == 'Surface3D':
        print('Creating Surface3D object...')
        surface = Surface3D()
        jsonVertices = jsonData['Vertices']
        vertices = []
        for i in range(0, len(jsonVertices), 3):
            v = Vector3D()
            v.x = jsonVertices[i]
            v.y = jsonVertices[i + 1]
            v.z = jsonVertices[i + 2]
            vertices.append(v)
        surface.vertices.extend(vertices)
        jsonFaces = jsonData['Faces']
        faces = []
        for i in range(0, len(jsonFaces), 3):
            f = Simplex2D()
            f.v0 = jsonFaces[i]
            f.v1 = jsonFaces[i + 1]
            f.v2 = jsonFaces[i + 2]
            faces.append(f)
        surface.faces.extend(faces)
        jsonNormals = jsonData['Normals']
        normals = []
        for i in range(0, len(jsonNormals), 3):
            n = Vector3D()
            n.x = jsonNormals[i]
            n.y = jsonNormals[i + 1]
            n.z = jsonNormals[i + 2]
            normals.append(n)
        surface.normals.extend(normals)
        return surface
    elif jsonData['Type'] == 'GridField2D':
        print('Creating GridField2D object...')
        gridField = GridField2D()
        jsonGrid = jsonData['Grid']
        gridField.grid.boundingBox.p.x = jsonGrid['BoundingBox']['P']['x']
        gridField.grid.boundingBox.p.y = jsonGrid['BoundingBox']['P']['y']
        gridField.grid.boundingBox.q.x = jsonGrid['BoundingBox']['Q']['x']
        gridField.grid.boundingBox.q.y = jsonGrid['BoundingBox']['Q']['y']
        gridField.values.extend(jsonData['Values'])
        return gridField
    else:
        Error('Unknown data type %s' % jsonData['Type'])

# Copyright (C) 2022 Dag Wästberg
# Licensed under the MIT License

#%%
import fiona
from dtcc.dtcc_pb2 import Polygon, Building, LinearRing, Vector2D, CityModel

#%%
def buildLinearRing(coords):
    lr = LinearRing()
    vertices = []
    for c in coords:
        v = Vector2D()
        v.x = c[0]
        v.y = c[1]
        vertices.append(v)
    lr.vertices.extend(vertices)
    return lr

def buildPolygon(geom_coords):
    polygon = Polygon()
    shell = geom_coords.pop(0)
    shell = buildLinearRing(shell)
    polygon.shell.CopyFrom(shell)
    if len(geom_coords)> 0:
        holes = []
        for hole in geom_coords:
            hole = buildLinearRing(hole)
            holes.append(hole)
        polygon.holes.extend(holes)
    return polygon


def LoadBuildings(filename,uuid_field = 'id'):
    cityModel = CityModel()
    buildings = []
    with fiona.open(filename) as src:
        for s in src:
            geom_type = s['geometry']['type']
            if geom_type == 'Polygon':
                building = Building()
                if uuid_field in s['properties']:
                    building.uuid = s['properties'][uuid_field]
                footprint = buildPolygon(s['geometry']['coordinates'])
                building.footPrint.CopyFrom(footprint)
                buildings.append(building)
            if geom_type == 'MultiPolygon':
                
                for idx, polygon in enumerate(s['geometry']['coordinates']):
                    building = Building()
                    if uuid_field in s['properties']:
                        uuid = s['properties'][uuid_field] + f"-{idx}"
                        building.uuid = uuid
                    footprint = buildPolygon(polygon)
                    building.footPrint.CopyFrom(footprint)
                    buildings.append(building)
    cityModel.buildings.extend(buildings)
    return cityModel


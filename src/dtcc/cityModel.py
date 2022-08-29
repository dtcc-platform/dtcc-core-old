# Copyright (C) 2022 Dag Wästberg
# Licensed under the MIT License

#%%
from distutils.command.build_py import build_py
import fiona
import shapely.geometry
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

def pbFootprint2Shapely(pb_footprint):
    shell = []
    holes = []
    for vert in pb_footprint.shell.vertices:
        shell.append((vert.x,vert.y))
    for h in pb_footprint.holes:
        hole = []
        for vert in h.vertices:
            hole.append((vert.x,vert.y))
        if len(hole) > 0:
            holes.append(hole)
    poly = shapely.geometry.Polygon(shell, holes = holes)
    return poly

def loadBuildings(filename,uuid_field = 'id', height_field = '', return_serialized=False):
    cityModel = CityModel()
    buildings = []
    has_height_field = len(height_field) == 0
    with fiona.open(filename) as src:
        for s in src:
            geom_type = s['geometry']['type']
            if geom_type == 'Polygon':
                building = Building()
                if uuid_field in s['properties']:
                    building.uuid = str(s['properties'][uuid_field])
                if has_height_field and height_field in s['properties'] and s['properties'][height_field]:
                    try:
                        building.height = float(s['properties'][height_field])
                    except ValueError:
                        print(f"Error cannot parse height field: {s['properties'][height_field]}")
                footprint = buildPolygon(s['geometry']['coordinates'])
                building.footPrint.CopyFrom(footprint)
                buildings.append(building)
            if geom_type == 'MultiPolygon':
                for idx, polygon in enumerate(s['geometry']['coordinates']):
                    building = Building()
                    if uuid_field in s['properties']:
                        uuid = str(s['properties'][uuid_field]) + f"-{idx}"
                        building.uuid = uuid
                    if has_height_field and height_field in s['properties'] and s['properties'][height_field]:
                        try:
                            building.height = float(s['properties'][height_field])
                        except ValueError:
                            print(f"Error cannot parse height field: {s['properties'][height_field]}")
                    footprint = buildPolygon(polygon)
                    building.footPrint.CopyFrom(footprint)
                    buildings.append(building)
    cityModel.buildings.extend(buildings)
    if return_serialized:
        return cityModel.SerializeToString()
    else:
        return cityModel

def writeCityModel(city_model, out_file, output_format = ".shp"):
    if not output_format.startswith('.'):
        output_format = '.' + output_format
    if not output_format in ['.shp','.json','.geojson','.gpkg']:
        print(f"Error! Format {output_format} not recognized")
        return None
    driver = {
        '.shp': 'ESRI Shapefile',
        '.json':'GeoJSON',
        '.geojson': 'GeoJSON',
        '.gpkg': 'GPKG'
    }

    schema = {
        'geometry':'Polygon',
        'properties':{
            'id':'str',
            'height':'float',
            'ground_height': 'float'
        }
    }
    with fiona.open(out_file,'w',driver[output_format],schema) as dst:
        for building in city_model.buildings:
            shapely_footprint = pbFootprint2Shapely(building.footPrint)
            dst.write({
                'geometry': shapely.geometry.mapping(shapely_footprint),
                'properties':{
                    'id': building.uuid,
                    'height': building.height,
                    'ground_height':building.groundHeight
                }
            })
        
        


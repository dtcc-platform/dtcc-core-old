from dtcc.pointCloud import loadLAS
from dtcc.cityModel import loadBuildings, writeCityModel
from dtcc.dtcc_pb2 import PointCloud, CityModel
from google.protobuf.message import DecodeError

import numpy as np
import fiona
import laspy

from enum import Enum, auto
from pathlib import Path
import sys
import glob
import argparse

class DTCCModels(Enum):
    BUILDINGS = auto()
    POINTCLOUD = auto()

    PROTOBUF = auto()

def create_pb(filename: Path, model_type:DTCCModels, args=None):
    if model_type == DTCCModels.BUILDINGS:
        return loadBuildings(filename,uuid_field=args.uuid_field, height_field =args.height_field, return_serialized=True)
    if model_type == DTCCModels.POINTCLOUD:
        return loadLAS(filename)
    return None

def write_pb(pb_data, input_file: Path) -> None:
    outputfile = Path(str(input_file) + '.pb')
    with open (outputfile,'wb') as dst:
        dst.write(pb_data)

def detectModelType(filename: Path):
    ext = filename.suffix.lower()
    if ext in ['.pb','.pb2']:
        return DTCCModels.PROTOBUF
    if ext in ['.shp','.json','.gpkg','.geojson']:
        try: 
            o = fiona.open(filename)
        except:
            fiona.errors.DriverError
            return None
        else:
            o.close()
        return DTCCModels.BUILDINGS
    if ext in ['.las','.laz']:
        return DTCCModels.POINTCLOUD
    return None

def loadPB(pb_string: str, pb_type: DTCCModels):
    pb = None
    try:
        if pb_type == DTCCModels.POINTCLOUD:
            pb = PointCloud()
            pb.ParseFromString(pb_string)
        elif pb_type == DTCCModels.BUILDINGS:
            pb = CityModel()
            pb.ParseFromString(pb_string)
    except DecodeError:
        print("Cannot parse point cloud")
        return (None,None)
    return (pb,pb_type)
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert geodata to/from dtcc protobuf')
    parser.add_argument('--model-type', default='', help = "type of protobuf being passed")
    parser.add_argument('--uuid-field', default='id', help= "field containing uuid (where applicable). Default 'id'")
    parser.add_argument('--height-field',default='', help="field containing building height (optional)")
    parser.add_argument('infiles',nargs=argparse.REMAINDER, help="files to convert")

    args = parser.parse_args()

    model_types = {
        'las': DTCCModels.POINTCLOUD,
        'pointcloud': DTCCModels.POINTCLOUD,
        'buildings': DTCCModels.BUILDINGS,
        'citymodel': DTCCModels.BUILDINGS
    }

    input_files = []
    for f in args.infiles:
        expanded = list(Path.cwd().glob(f))
        if len(expanded)>0:
            input_files += expanded
        else:
            print(f"Warning! Could not find {f}")
    if len(input_files) == 0:
        print("Error: found no files to process")
        sys.exit(1)
    print(input_files)

    for f in input_files:
        if not f.is_file():
            print(f"Error! {f} is not a file")
            continue
        mt = detectModelType(f)
        if mt is None:
            print(f"Error! cannot detect type of {f}")
            continue
        if mt != DTCCModels.PROTOBUF:
            pb = create_pb(f,mt,args)
    
            if pb is not None:
                write_pb(pb,f)
        elif mt == DTCCModels.PROTOBUF:

            mt = model_types.get(args.model_type.lower())
            if mt is None:
                print(f"Error! unknown dtcc model type {args.model_type}")
                sys.exit(1)
            with open(f,'rb') as src:
                pb_string = src.read()
            
            pb_object, pb_type = loadPB(pb_string, mt)
            if pb_object is None:
                print ("unknown protobuf")
                sys.exit(1)
            if pb_type == DTCCModels.BUILDINGS:
                writeCityModel(pb_object, Path(str(f) + '.shp'))
            
                     














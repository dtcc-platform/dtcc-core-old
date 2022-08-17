from dtcc.pointCloud import loadLAS
from dtcc.cityModel import loadBuildings

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

def create_pb(filename: Path, model_type:DTCCModels):
    if model_type == DTCCModels.BUILDINGS:
        return loadBuildings(filename,uuid_field=args.uuid_field, return_serialized=True)
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
    if ext in ['.shp','.json','.gpkg','geojson']:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert geodata to/from dtcc protobuf')
    parser.add_argument('--model', default='', help = "type of data being passed (autodetects if left blank)")
    parser.add_argument('-uuid-field', default='id', help= "field containing uuid (where applicable). Default 'id'")
    parser.add_argument('infiles',nargs=argparse.REMAINDER, help="files to convert")

    args = parser.parse_args()

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
        pb = create_pb(f,mt)
        if pb is not None:
            write_pb(pb,f)













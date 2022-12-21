import time, pathlib, sys, datetime, threading, json, os, shutil, wget, tempfile
from functools import lru_cache
import minio
project_dir = str(pathlib.Path(__file__).resolve().parents[0])
sys.path.append(project_dir)

from logger import getLogger
from utils import file_exists, find_all_files_in_folder, try_except


logger = getLogger(__file__)

data_dir = os.path.join("./", "data")
os.makedirs(data_dir,exist_ok=True)

shared_data_dir = os.environ.get('SHARED_DATA_DIR', data_dir)

class LocalFileHandler:
    def __init__(self,destination_prefix="") -> None:
        if destination_prefix == '/':
            raise Exception("destination prefix cannot be /")
        self.shared_data_dir = shared_data_dir
        self.destination_prefix= destination_prefix
        self.dst_folder_path = os.path.join(shared_data_dir,self.destination_prefix)
        
    @try_except(logger=logger)
    def get_data_dir(self) -> str:
        return self.dst_folder_path

    @try_except(logger=logger)
    def list(self, extention=""):
        return find_all_files_in_folder(self.dst_folder_path, extension=extention)

    def copy_to_shared_folder(self,source_file_path, replace=False) -> str:
        if file_exists(source_file_path, allow_empty_files=True):
            
            os.makedirs(self.dst_folder_path,exist_ok=True)
            dst_file_path = os.path.join(self.dst_folder_path, os.path.split(source_file_path)[1])
            
            if file_exists(dst_file_path, allow_empty_files=True):
                if replace:
                    os.remove(dst_file_path)
                else:
                    logger.error(f"{source_file_path} already exists in destination folder {self.dst_folder_path}")
                    return dst_file_path
      

            shutil.copy(source_file_path, dst_file_path)
    
            logger.info(f"Copied {source_file_path} to {dst_file_path} ")
            return dst_file_path

        else:
            raise Exception(f"{source_file_path}  path does not exist ")

    @try_except(logger=logger)
    def download_file_from_url(self, url:str, output_file_path:str=None, replace=False) -> str:
        def bar_custom(current, total, width=80):
            ## TODO Maybe publish download progress via rmq logpub channel
            logger.info("Downloading: %d%% [%d / %d] bytes" % (current / total * 100, current, total))

        if output_file_path is None:
            file_name  = wget.detect_filename(url=url)
            print(file_name)
            output_file_path = os.path.join(self.dst_folder_path, file_name)

        if file_exists(output_file_path):
            if replace:
                os.remove(output_file_path)
            else:
                logger.error(f"{output_file_path} already exists in destination folder {self.dst_folder_path}")
                return output_file_path
        
        dst_file_path = wget.download(url, bar=bar_custom, out=output_file_path)
        logger.info(f"Downloaded to {dst_file_path}")
        return dst_file_path



HOST =   os.environ.get("MINIO_HOST", "localhost")
ACCESS_KEY = os.environ.get('MINIO_USER', 'dtcc_admin')
SECRET_KEY = os.environ.get('MINIO_PASSWORD', 'dtcc_minio')
URI = f"http://{HOST}:9000"



class MinioFileHandler:
    def __init__(self, bucketname="test_bucket") -> None:
        self.bucketname = bucketname
        self.connect()

    def connect(self):
        try:
            self.client = minio.Minio(URI, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)
            self.make_bucket()
        except:
            logger.exception("Error while connecting to minio")

    def list_buckets(self):
        return self.client.list_buckets()

    def list_objects(self, prefix="modulename/toolname/task_id"):
        objects = self.client.list_objects(self.bucketname, prefix=prefix)
        return objects

    def make_bucket(self):
        found = self.client.bucket_exists(self.bucketname)
        if not found:
            self.client.make_bucket(self.bucketname)
            logger.error(f"Bucket: {self.bucketname} created!")
        else:
            logger.error(f"Bucket: {self.bucketname} already exists")

    def upload_file(self, local_file_path:str, prefix="modulename/toolname/task_id",progress_callback=None ):
        def upload_progress(chunk):
            progress_callback + chunk # Notice! No len()
            progress_callback.show_progress()

        file_name = os.path.split(local_file_path)[1]
        print(file_name)
        object_name = prefix + '/' + file_name
        self.client.fput_object(self.bucketname, object_name,local_file_path,progress=upload_progress)
        logger.info("It is successfully uploaded to bucket")

    def download_file(self, local_file_path:str, prefix="modulename/toolname/task_id",progress_callback=None):
        def download_progress(chunk):
            progress_callback + chunk # Notice! No len()
            progress_callback.show_progress()

        file_name = os.path.split(local_file_path)[1]
        print(file_name)
        object_name = prefix + '/' + file_name
        self.client.fget_object(self.bucketname, object_name,local_file_path,progress=download_progress)
        logger.info("It is successfully uploaded to bucket")




def test_local_file_handler_copy():
    local_file_handler = LocalFileHandler(destination_prefix="helloworld/test")
    data_directory = local_file_handler.get_data_dir()

    print(local_file_handler.list(extention=".json"))
   

    temp = tempfile.NamedTemporaryFile(suffix='.pb')
    temp.write("test content .....".encode())
    temp.flush()
    ## copy to local / shared  storage
    input_file_path = local_file_handler.copy_to_shared_folder(source_file_path="/Users/sidkas/workspace/dtcc/dtcc-modules/dtcc-buildmodule-dtcc-builder.sh", replace=True)
    print(input_file_path)

    temp.close()


def test_local_file_handler_download_url():
    local_file_handler = LocalFileHandler(destination_prefix="helloworld/test")

    dst_path = local_file_handler.download_file_from_url(
        url="https://gitlab.com/dtcc-platform/dtcc-modules/-/raw/main/dtcc-modules-conf.json",
        replace=False
    )
    print(dst_path)



if __name__=='__main__':
    test_local_file_handler_download_url()
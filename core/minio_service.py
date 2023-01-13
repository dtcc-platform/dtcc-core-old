import time, pathlib, sys, datetime, threading, json, os, shutil, wget, tempfile
from functools import lru_cache
import minio
project_dir = str(pathlib.Path(__file__).resolve().parents[0])
sys.path.append(project_dir)

from logger import getLogger
from utils import try_except, get_size_mb
from minio_progress import AnimatedProgress
from data_models import MinioObject


logger = getLogger(__file__)


HOST =   os.environ.get("MINIO_HOST", "localhost")
ACCESS_KEY = os.environ.get('MINIO_USER', 'dtcc_admin')
SECRET_KEY = os.environ.get('MINIO_PASSWORD', 'dtcc_minio')
URI = f"{HOST}:9000"



class MinioFileHandler:
    def __init__(self, bucketname="test_bucket", make_bucket=False) -> None:
        self.bucketname = bucketname
        self.connect()
        if make_bucket:
            self.make_bucket()
        else:
            if not self.client.bucket_exists(self.bucketname):
                raise Exception(f"{bucketname} does not exist in minio!")

    def connect(self):
        try:
            self.client = minio.Minio(URI, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)
        except:
            logger.exception("Error while connecting to minio")

    def make_bucket(self):
        found = self.client.bucket_exists(self.bucketname)
        if not found:
            self.client.make_bucket(self.bucketname)
            logger.info(f"Bucket: {self.bucketname} created!")
        else: 
            logger.info(f"Bucket: {self.bucketname} already exists!")

    def list_buckets(self):
        return self.client.list_buckets()

   
    def list_objects(self, prefix="/"):
        """
        prefix: /modulename/toolname/task_id (if root then prefix = "/")
        """
        objects = self.client.list_objects(self.bucketname, prefix=prefix)
        return objects

   

    @try_except(logger=logger)
    def upload_file(self, local_file_path:str, prefix="/",progress_callback=None ) -> MinioObject:
        """
        Local file path: absolute local path and file name must be the same as in minio storage bucket
        prefix: path for file in minio
        """
        file_name = os.path.split(local_file_path)[1]
        size = os.path.getsize(local_file_path)
        progress_callback.set_meta(total_length=size, object_name=file_name)
        print(file_name)
        object_name = prefix + '/' + file_name
        file_object = self.client.fput_object(self.bucketname, object_name,local_file_path,progress=progress_callback)
        
        
        logger.info(f"{object_name} is successfully uploaded to bucket {self.bucketname}")
        return MinioObject(bucket_name=self.bucketname, prefix=prefix, file_name=file_name,size=size, etag=file_object.etag,last_modified=file_object.last_modified )

   
    @try_except(logger=logger)
    def download_file(self, local_file_path:str, prefix="/",progress_callback=None) -> MinioObject:
        """
        Local file path: absolute local path and file name must be the same as in minio storage bucket
        prefix: path for file in minio
        """
        try:
            file_name = os.path.split(local_file_path)[1]
            print(file_name)
            object_name = prefix + '/' + file_name
            file_object = self.client.fget_object(self.bucketname, object_name,local_file_path,progress=progress_callback)
            logger.info("It is successfully uploaded to bucket")
            file_info = MinioObject(bucket_name=self.bucketname, prefix=prefix, file_name=file_object.object_name,size=file_object.size, etag=file_object.etag,last_modified=str(file_object.last_modified) )

            return file_info
        except minio.S3Error as e:
            logger.exception("S3 error from minio download")

    @try_except(logger=logger)
    def get_object_info(self,file_name:str, prefix="/") -> MinioObject:
        """
        Local file path: absolute local path and file name must be the same as in minio storage bucket
        prefix: path for file in minio
        """
        object_name = prefix + '/' + file_name
        file_object = self.client.stat_object(self.bucketname, object_name)
        file_info = MinioObject(bucket_name=self.bucketname, prefix=prefix, file_name=file_object.object_name,size=file_object.size, etag=file_object.etag,last_modified=str(file_object.last_modified) , is_dir=file_object.is_dir)

        return file_info
     

def test_minio_file_handler():
    minio_file_handler = MinioFileHandler(bucketname="test")

    for o in minio_file_handler.list_objects(prefix="/"):
        print(o.object_name, o.size, o.storage_class, o.is_dir, o.etag, o.content_type, o.version_id)
   
    progress_bar = AnimatedProgress()

    minio_file_handler.download_file(local_file_path="./data/docker-compose.yml", prefix="/", progress_callback=progress_bar)
    ## Upload file
    mf = minio_file_handler.upload_file(
        local_file_path="./data/docker-compose.yml", 
        prefix="/",
        progress_callback=progress_bar
    )
    print(mf)

def test_get_info():
    minio_file_handler = MinioFileHandler(bucketname="dtcc")

    o = minio_file_handler.get_object_info(prefix="/solardata", file_name="City34k.stl")

    print(o)


if __name__=='__main__':
    test_get_info()
import os, pathlib, sys, argparse, threading, time, shutil
import subprocess
from multiprocessing.pool import ThreadPool
from dotenv import load_dotenv



project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from src.common.logger import getLogger

logger = getLogger(__file__)

load_dotenv(os.path.join(project_dir, 'docker','.env'))

docker_working_dir = os.getenv('WORKING_DIR')
shared_data_dir = os.getenv('SHARED_DATA_DIR')

from src.common.redis_service import RedisPubSub

def load_sample_file(path:str):
    if os.path.exists(path):
        with open(path, mode='r') as f:
            lines = f.readlines()
            logger.info(lines)
        
    else:
        logger.error(f"path doesn't exist {path}")

def run_binary(parameters_path:str):
    pass

def create_sample_file():
    file_path = os.path.join(shared_data_dir,'sample.txt')

    with open(file_path, mode='w') as f:
        f.write('from ' + os.environ.get('USER') + '\n')
        for i in range(10):
            time_dt = subprocess.check_output(['date']).decode('utf-8')
            f.write(time_dt)
            time.sleep(0.1)

    return file_path

def run_and_notify(host, port,channel,callback,callback_args=[]):
    rps = RedisPubSub(host=host,port=port)
    pool = ThreadPool(processes=4)

    async_result = pool.apply_async(callback, args=(*callback_args,))

    file_path = async_result.get()

    published = rps.publish(channel=channel,message=str(file_path))
    if published:
        logger.info("published")




parameters_file_path = os.path.join(project_dir, "unittests/data/MinimalCase/Parameters.json")
destination_folder = os.path.join(shared_data_dir,'vasnas')

def copy_and_notify(args):
    rps = RedisPubSub(host=args.host,port=args.port)
    src_file_path = args.src
    dst_file_path = os.path.join(args.dst, os.path.split(src_file_path)[1])
    shutil.copy(src_file_path, dst_file_path)
    published = rps.publish(channel=args.channel, message=dst_file_path)
    if published:
        logger.info("published")

if __name__=='__main__':

    parser = argparse.ArgumentParser()

    subparser = parser.add_subparsers(dest='command')

    test = subparser.add_parser('test')
    test.add_argument("--host", "-H", type=str,default='localhost', help="hostname")
    test.add_argument("--port", "-P", type=int,default=6879, help="port")

    sub = subparser.add_parser('subscribe')
    sub.add_argument("--host", "-H", type=str,default='redis', help="hostname")
    sub.add_argument("--port", "-P", type=int,default=6379, help="port")
    sub.add_argument("--channel", "-C", type=str,default='dtcc-core', help="redis channel")


    pub = subparser.add_parser('run')
    pub.add_argument("--host", "-H", type=str,default='redis', help="hostname")
    pub.add_argument("--port", "-P", type=int,default=6379, help="port")
    pub.add_argument("--channel", "-C", type=str,default='dtcc-core', help="redis channel")


    cp = subparser.add_parser('copy')
    cp.add_argument("--host", "-H", type=str,default='redis', help="hostname")
    cp.add_argument("--port", "-P", type=int,default=6379, help="port")
    cp.add_argument("--channel", "-C", type=str,default='dtcc-core', help="redis channel")
    cp.add_argument("--src", type=str,default=parameters_file_path, help="source file path")
    cp.add_argument("--dst", type=str,default=destination_folder, help="destination folder path")
    
    args = parser.parse_args()

    if args.command == 'subscribe':
        rps = RedisPubSub(host=args.host,port=args.port)
        rps.subscribe(channel=args.channel,callback=load_sample_file)

    if args.command == 'run':
        run_and_notify(host=args.host,port=args.port,channel=args.channel,callback=create_sample_file)

    if args.command == 'copy':
        copy_and_notify(args)
        







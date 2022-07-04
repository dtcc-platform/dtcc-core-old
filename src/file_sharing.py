import os, pathlib, sys, argparse, threading, time, shutil
import subprocess
from multiprocessing.pool import ThreadPool
import celery
from dotenv import load_dotenv



project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from src.common.utils import try_except, timer
from src.common.logger import getLogger
from src.common.redis_service import RedisPubSub
from src.scheduler import JobScheduler

logger = getLogger(__file__)

load_dotenv(os.path.join(project_dir, 'docker','.env'))

docker_working_dir = os.getenv('WORKING_DIR')
shared_data_dir = os.getenv('SHARED_DATA_DIR')

#--> Consts
REDIS_HOST = "localhost" #"redis"
REDIS_PORT =  "6879" # 6379
REDIS_CHANNEL = 'dtcc-core'

#--> defaults
parameters_file_path = os.path.join(project_dir, "unittests/data/MinimalCase/Parameters.json")
destination_folder = os.path.join(shared_data_dir,'vasnas')

@celery.shared_task
def test_send_receive(host=REDIS_HOST, port=REDIS_PORT,test_arg='dummy'):
    logger.info("printing test arg: "+ test_arg)
    time_dt = subprocess.check_output(['date'])
    message=time_dt.decode('utf-8').replace('\n','')
    channel="core"

    rps = RedisPubSub(host=host,port=port)
    
    pool = ThreadPool(processes=1)

    async_result = pool.apply_async(rps.subscribe_one, args=(channel,))

    time.sleep(5)

    published = rps.publish(channel=channel,message=message)
    if published:
        logger.info("published")

    incoming_msg = async_result.get()

    assert message == incoming_msg

    logger.info(incoming_msg)


def check_if_path_exists(path:str) -> None:
    if not os.path.exists(path):
        logger.error(f"path does not exist {path}")
        sys.exit(1)

def load_sample_file(path:str) -> None:
    if os.path.exists(path):
        logger.info("loading from: "+ path)
        with open(path, mode='r') as f:
            lines = f.readlines()
            logger.info(lines)
        
    else:
        logger.error(f"path doesn't exist {path}")

def run_binary(parameters_path:str):
    pass


def create_sample_file() -> str:
    file_path = os.path.join(project_dir,'logs','sample.txt')
    logger.info(file_path)
    with open(file_path, mode='w') as f:
        f.write('from ' + os.environ.get('USER') + '\n')
        for i in range(10):
            time_dt = subprocess.check_output(['date']).decode('utf-8')
            f.write(time_dt)
            time.sleep(1)

    logger.info("Success!")

    return file_path

@try_except(logger=logger)
def run_and_notify(channel:str,callback,callback_args=[],host=REDIS_HOST, port=REDIS_PORT) -> None:
    rps = RedisPubSub(host=host,port=port)
    pool = ThreadPool(processes=4)

    async_result = pool.apply_async(callback, args=(*callback_args,))

    file_path = async_result.get()

    published = rps.publish(channel=channel,message=str(file_path))
    if published:
        logger.info("published")


@try_except(logger=logger)
def copy_and_notify(src_file_path:str,dst_folder:str,channel:str,host=REDIS_HOST, port=REDIS_PORT):

    rps = RedisPubSub(host=host,port=port)

    
    check_if_path_exists(src_file_path)
    check_if_path_exists(shared_data_dir)

    dst_folder_path = os.path.join(shared_data_dir,dst_folder)
    os.makedirs(dst_folder_path,exist_ok=True)

    dst_file_path = os.path.join(dst_folder_path, os.path.split(src_file_path)[1])
    shutil.copy(src_file_path, dst_file_path)

    logger.info(f"Copied {src_file_path} to {dst_file_path} ")

    published = rps.publish(channel=channel, message=dst_file_path)
    if published:
        logger.info("published")


if __name__=='__main__':

    parser = argparse.ArgumentParser()

    subparser = parser.add_subparsers(dest='command')

    test = subparser.add_parser('test')
    test.add_argument("--host", "-H", type=str,default='localhost', help="hostname")
    test.add_argument("--port", "-P", type=int,default=6879, help="port")
    test.add_argument("--channel", "-C", type=str,default=REDIS_CHANNEL, help="redis channel")
    test.add_argument("--src", type=str,default=parameters_file_path, help="source file path")
    test.add_argument("--dst", type=str,default=destination_folder, help="destination folder path")

    sub = subparser.add_parser('subscribe')
    sub.add_argument("--host", "-H", type=str,default=REDIS_HOST, help="hostname")
    sub.add_argument("--port", "-P", type=int,default=REDIS_PORT, help="port")
    sub.add_argument("--channel", "-C", type=str,default=REDIS_CHANNEL, help="redis channel")


    pub = subparser.add_parser('run')
    pub.add_argument("--host", "-H", type=str,default=REDIS_HOST, help="hostname")
    pub.add_argument("--port", "-P", type=int,default=REDIS_PORT, help="port")
    pub.add_argument("--channel", "-C", type=str,default=REDIS_CHANNEL, help="redis channel")


    cp = subparser.add_parser('copy')
    cp.add_argument("--host", "-H", type=str,default=REDIS_HOST, help="hostname")
    cp.add_argument("--port", "-P", type=int,default=REDIS_PORT, help="port")
    cp.add_argument("--channel", "-C", type=str,default=REDIS_CHANNEL, help="redis channel")
    cp.add_argument("--src", type=str,default=parameters_file_path, help="source file path")
    cp.add_argument("--dst", type=str,default=destination_folder, help="destination folder path")
    
    args = parser.parse_args()

    job_scheduler = JobScheduler(scheduler_name="core",use_redis_backend=False,max_job_instances=1)

    if args.command == 'subscribe':
        rps = RedisPubSub(host=args.host,port=args.port)
        rps.subscribe(channel=args.channel,callback=load_sample_file)

    elif args.command == 'run':
        # run_and_notify(host=args.host,port=args.port,channel=args.channel,callback=create_sample_file)
        job = job_scheduler.add_job(func=run_and_notify, args=[args.channel, create_sample_file])
        job_scheduler.run()

        while job_scheduler.job_exists(run_and_notify):
            time.sleep(2)

    elif args.command == 'copy':
        copy_and_notify(
            src_file_path=args.src, 
            dst_folder=args.dst,
            channel=args.channel
        )

    elif args.command == 'test':

        rps = RedisPubSub(host=args.host,port=args.port)
        rps.test_redis()
        # copy_and_notify(
        #     src_file_path=args.src, 
        #     dst_folder=args.dst,
        #     channel=args.channel,
        #     host=args.host, 
        #     port=args.port
        # )
    else:
        parser.print_help()
        sys.exit(0)







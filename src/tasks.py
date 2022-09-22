import os, pathlib, sys, argparse, threading, time, shutil
import subprocess, shlex
from datetime import datetime
from multiprocessing.pool import ThreadPool
from dotenv import load_dotenv
from rocketry import Rocketry
from rocketry.conds import every
from rocketry.conds import (
    every, hourly, daily, 
    after_success, 
    true, false
)

project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from src.common.utils import get_uuid, try_except, timer
from src.common.logger import getLogger
from src.common.redis_service import RedisPubSub
from src.common.run_in_shell import run_shell_command

logger = getLogger(__file__)

load_dotenv(os.path.join(project_dir, 'docker','.env'))

docker_working_dir = os.getenv('WORKING_DIR')
shared_data_dir = os.getenv('SHARED_DATA_DIR', project_dir)

REDIS_CHANNEL = 'core'

#--> defaults
parameters_file_path = os.path.join(project_dir, "unittests/data/MinimalCase/Parameters.json")
destination_folder = os.path.join(shared_data_dir,'vasnas')


redis_pub_sub = RedisPubSub()

#--> Rocketry Tasks
scheduler = Rocketry(config={"task_execution": "async"})

@scheduler.task(execution="thread")
def dummy_task():
    test_send_receive()

    file_path = create_sample_file()

    return file_path

@scheduler.task(after_success(dummy_task),execution="thread")
def after_dummy():
    rps = RedisPubSub()
    run_shell_command(command='ls -la -h',redis_pub_sub=rps)
    


@scheduler.task(excecution="thread")
async def dummy_logs_publisher():
    channel = "/task/dummy_logs_publisher/logs"
    sample_logger_path = os.path.join(project_dir, "src/tests/sample_logging_process.py")
    await run_shell_command(
        command=f'python {sample_logger_path}',
        channel=channel,
        publish=True
    )

@scheduler.task(execution="thread")
def run_iboflow_on_builder():
    channel = "/task/run_iboflow_on_builder"
    rps = RedisPubSub()

    published = rps.publish(channel=channel,message="run")

    if published:
        message = rps.subscribe_one(channel=channel,wait_forever=True)

        if message is not None and message == "1":
            return True
        else: 
            return False
    else:

        return False



#--> Export functions
    

@try_except(logger=logger)
def run_and_notify(channel:str,callback,callback_args=[]) -> None:
    rps = RedisPubSub()
    pool = ThreadPool(processes=4)

    async_result = pool.apply_async(callback, args=(*callback_args,))

    file_path = async_result.get()

    published = rps.publish(channel=channel,message=str(file_path))
    if published:
        logger.info("published")


@try_except(logger=logger)
def copy_and_notify(src_file_path:str,dst_folder:str,channel:str):

    rps = RedisPubSub()

    
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



@try_except(logger=logger)
def run_iboflow(job_id:str):

    rps = RedisPubSub()
    message = rps.subscribe_one(REDIS_CHANNEL,wait_forever=True)

    logger.info("received meassge: ", message)

    iboflow_command = 'ls -la -h'

    run_shell_command(command=iboflow_command)



#--> Helper functions

def check_if_path_exists(path:str) -> None:
    if not os.path.exists(path):
        logger.error(f"path does not exist {path}")
        sys.exit(1)


#--> Test functions

def test_send_receive(test_arg='dummy'):
    logger.info("printing test arg: "+ test_arg)
    time_dt = subprocess.check_output(['date'])
    message=time_dt.decode('utf-8').replace('\n','')
    channel="core"

    rps = RedisPubSub()
    
    pool = ThreadPool(processes=1)

    async_result = pool.apply_async(rps.subscribe_one, args=(channel,))

    time.sleep(5)

    published = rps.publish(channel=channel,message=message)
    if published:
        logger.info("published")

    incoming_msg = async_result.get()

    assert message == incoming_msg

    logger.info(incoming_msg)

    

def load_sample_file(path:str) -> None:
    if os.path.exists(path):
        logger.info("loading from: "+ path)
        with open(path, mode='r') as f:
            lines = f.readlines()
            logger.info(lines)
        
    else:
        logger.error(f"path doesn't exist {path}")

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
    sub.add_argument("--channel", "-C", type=str,default=REDIS_CHANNEL, help="redis channel")


    pub = subparser.add_parser('run')
    pub.add_argument("--channel", "-C", type=str,default=REDIS_CHANNEL, help="redis channel")


    cp = subparser.add_parser('copy')
    cp.add_argument("--channel", "-C", type=str,default=REDIS_CHANNEL, help="redis channel")
    cp.add_argument("--src", type=str,default=parameters_file_path, help="source file path")
    cp.add_argument("--dst", type=str,default=destination_folder, help="destination folder path")
    
    args = parser.parse_args()


    if args.command == 'subscribe':
        rps = RedisPubSub(host=args.host,port=args.port)
        rps.subscribe(channel=args.channel,callback=load_sample_file)

    elif args.command == 'run':
        # run_and_notify(channel=args.channel,callback=create_sample_file)
        run_and_notify(args.channel, create_sample_file)
    

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







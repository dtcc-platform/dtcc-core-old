import os, pathlib, sys, argparse, threading, time, shutil
from datetime import datetime
from multiprocessing.pool import ThreadPool
from dotenv import load_dotenv


project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from src.common.utils import get_uuid, try_except, timer
from src.common.logger import getLogger
from src.common.redis_service import RedisPubSub
from src.common.run_in_shell import run_shell_command

logger = getLogger(__file__)

@try_except(logger=logger)
def run_iboflow():
    channel = "/task/run_iboflow_on_builder"
    logs_channel = channel + "/logs"
    rps = RedisPubSub()

    logger.info(f"Waiting for  {channel}")

    while True:
        message = rps.subscribe_one(channel=channel,wait_forever=True)

        logger.info("received meassge: ", message)

        if message == 'run':
            sample_logger_path = os.path.join(project_dir, "src/tests/sample_logging_process.py")
            cmd = f'python3 {sample_logger_path}'
            success = run_shell_command(command=cmd, channel=logs_channel)
            if success:
                rps.publish(channel=channel,message="success!")
            else:
                rps.publish(channel=channel,message="failed!")

        elif message == 'terminate':
            break


if __name__ == '__main__':
    run_iboflow()
import os, pathlib, sys, argparse, threading, time

project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from logger import getLogger

logger = getLogger(__file__)



def start_logging():
    try:
        for i in range(1000):
            logger.info(f"{i}: new logg from sample logging process")
            time.sleep(0.2)
    except KeyboardInterrupt:
        logger.info('keyboard interrupt')


if __name__=='__main__':
    start_logging()
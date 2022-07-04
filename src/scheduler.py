from ctypes import Union
from datetime import datetime, timedelta
import os, pathlib, sys, argparse, threading, time, shutil,json

import apscheduler.job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore

import atexit
from cv2 import log

from numpy import True_, dtype


project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from src.common.utils import get_uuid, try_except, timer
from src.common.logger import getLogger
from src.common.redis_service import REDIS_PASSWORD

logger = getLogger(__file__)





#--> Consts
class RedisConfig:
    host = "localhost" #"redis"
    port =  "6879" # 6379
    channel = 'dtcc:core:jobs'
    db_number = 0


class JobScheduler():
    def __init__(self,scheduler_name="core",use_redis_backend=True,max_job_instances=1) -> None:
        self.scheduler_name = scheduler_name

        self.channel = f"dtcc_{scheduler_name}_jobs"
        self.runtime_tag = f"dtcc_{scheduler_name}_running"
        self.use_redis_backend = use_redis_backend
        self.max_job_instances = max_job_instances

        self.scheduler = self.get_scheduler()

    def get_scheduler(self) -> BackgroundScheduler:
        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }

        job_defaults = {
            'coalesce': False,
            'max_instances': self.max_job_instances
        }

        if self.use_redis_backend:
            jobstores = {
                'default': RedisJobStore(
                    jobs_key=self.channel, 
                    run_times_key=self.runtime_tag, 
                    host=RedisConfig.host, 
                    port=RedisConfig.port, 
                    password=REDIS_PASSWORD
                ),
            }

            scheduler = BackgroundScheduler(job_defaults=job_defaults, executors=executors,jobstores=jobstores)
        else:
            scheduler = BackgroundScheduler(job_defaults=job_defaults, executors=executors)

        

        self.scheduler = scheduler

        return scheduler

    @try_except(logger=logger)
    def add_job(self, func, args=[], kwargs={}, job_id=None) -> apscheduler.job.Job:

        if job_id is None:
            job_id = get_uuid(size=8)
        dt = datetime.now() + timedelta(seconds=2)
        job = self.scheduler.add_job(func, args=args,trigger=DateTrigger(run_date=dt), kwargs=kwargs, id=job_id, name=func.__name__)
    
        return job

    @try_except(logger=logger)
    def schedule_job(self, func, args=[], kwargs={}, seconds=10, minutes=0, hours=0, days=0, job_id=None) -> apscheduler.job.Job:
        dt = datetime.now() + timedelta(seconds=seconds,minutes=minutes,hours=hours, days=days)
        if job_id is None:
            job_id = get_uuid(size=8)
        job = self.scheduler.add_job(func, trigger=DateTrigger(run_date=dt), args=args, kwargs=kwargs, id=job_id, name=func.__name__)
        return job
      

    @try_except(logger=logger)
    def get_jobs(self):
        jobs = self.scheduler.get_jobs(jobstore="default")
        return [{
                'id':j.id,
                'name':j.name,
                'next_run_time':str(getattr(j, "next_run_time",False) if getattr(j, "next_run_time",False) is not None else 'pause'),
                'trigger':str(j.trigger)
            } for j in jobs
        ]

    def job_exists(self,func):
        jobs = self.scheduler.get_jobs(jobstore="default")
        existing_jobs = [j.name for j in jobs]
        return func.__name__ in existing_jobs

    def remove_job(self,job_id):
        self.scheduler.remove_job(job_id= job_id)

    @try_except(logger=logger)
    def run(self):
        self.scheduler.start()

        def OnExitApp():
            self.scheduler.remove_all_jobs()
            self.scheduler.shutdown(wait=True)
            logger.info(f"Exit from '{self.scheduler_name}' apscheduler application")

        atexit.register(OnExitApp)

    

import os, pathlib, sys, argparse, threading, time, shutil, json


project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)


from src.common.scheduler import JobScheduler
from src.file_sharing import test_send_receive, create_sample_file


def test_scheduler():
    aps = JobScheduler(use_redis_backend=False)

    job = aps.schedule_job(test_send_receive,args=('localhost',6879, "from apscheduler"), seconds=10)
    job.pause()

    job = aps.schedule_job(create_sample_file, minutes=10)

    job = aps.add_job(test_send_receive,args=('localhost',6879, "from apscheduler"))
    
    print(json.dumps(aps.get_jobs(),indent=4))

    aps.run()
    time.sleep(2)

    job = aps.schedule_job(create_sample_file, minutes=10)

    while True:
        print(json.dumps(aps.get_jobs(),indent=4))
        time.sleep(2)

if __name__=='__main__':
    test_scheduler()
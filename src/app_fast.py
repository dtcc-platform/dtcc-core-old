import os, pathlib, sys, datetime, time, re
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
import io
import uvicorn
from fastapi import FastAPI, Path, responses, status, Body, Query, BackgroundTasks, Response, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from enum import Enum, IntEnum
from sse_starlette.sse import EventSourceResponse

from redbird.oper import in_, between, greater_equal

project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

#sys.path.append( str((Path(__file__).parent / "../src").resolve() ))
#from dtcc import core
#from dtcc.core import *
#import sys
#sys.path.insert(0, '/home/dtcc/dtcc-core/')
#from dtcc.core import *


#def GetProjects(self):
#    def GetAvailableDataSetNames(self):
#    def GetGeneratedDataSetNames(self, project):
#    def GetDataSet(self, project, name):
#    def GenerateDataSet(self, project, name):


from src.task_scheduler_publisher import scheduler, pause, resume, terminate, close_client_loop
from src.common.rabbitmq_service import log_consumer
from src.common.redis_service import RedisPubSub

app = FastAPI(
    title="DTCC Core API",
    description="API for db access and communication",
    version="1.0"
)

session = scheduler.session
rps = RedisPubSub()

# Enable CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# c = Core()

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

# @app.get("/api/get-projects")
# async def root():
#     response=c.GetProjects()
#     return response
# @app.get("/api/GetAvailableDataSetNames")
# async def availdatasetnames():
#     response=c.GetAvailableDataSetNames()
#     return response
# @app.get("/api/GetGeneratedDataSetNames/{project}")
# async def gendatasetnames(project):
#     response=c.GetGeneratedDataSetNames(project)
#     return response
# #    def GetDataSet(self, project, name):
# @app.get("/api/GetDataSet/{project}/{name}")
# async def dataset(project,name):
#     response=c.GetDataSet(project,name)
# #    print(response)
# #    file = io.BytesIO(response["data"])
# #    return FileResponse(file, media_type="attachment/x-protobuf")
# #    return StreamingResponse(content=response["data"])
#     return StreamingResponse(io.BytesIO(response["data"]), media_type="attachment/x-protobuf")


@app.on_event('startup')
async def startup():
    pass

@app.on_event("shutdown")
async def shutdown():
    pass


# Job scheduler API

# Models (for serializing JSON)
# -----------------------------

class Task(BaseModel):
    name: str
    description: Optional[str]
    priority: int

    start_cond: str
    end_cond: str
    timeout: Optional[int]

    disabled: bool
    force_termination: bool
    force_run: bool

    status: str
    is_running: bool
    last_run: Optional[datetime.datetime]
    last_success: Optional[datetime.datetime]
    last_fail: Optional[datetime.datetime]
    last_terminate: Optional[datetime.datetime]
    last_inaction: Optional[datetime.datetime]
    last_crash: Optional[datetime.datetime]

class Log(BaseModel):
    timestamp: Optional[datetime.datetime] = Field(alias="created")
    task_name: str
    action: str
    result: Optional[str]

# Session Config
# --------------

router_config = APIRouter(tags=["config"])

@router_config.get("/session/config")
async def get_session_config():
    return session.config

@router_config.patch("/session/config")
async def patch_session_config(values:dict):
    for key, val in values.items():
        setattr(session.config, key, val)


# Session Parameters
# ------------------

router_params = APIRouter(tags=["session parameters"])

@router_params.get("/session/parameters")
async def get_session_parameters():
    return session.parameters

@router_params.get("/session/parameters/{name}")
async def get_session_parameters(name):
    return session.parameters[name]

@router_params.put("/session/parameters/{name}")
async def put_session_parameter(name:str, value):
    session.parameters[name] = value

@router_params.delete("/session/parameters/{name}")
async def delete_session_parameter(name:str):
    del session.parameters[name]


# Session Actions
# ---------------

router_session = APIRouter(tags=["session"])

@router_session.post("/session/shut_down")
async def shut_down_session():
    session.shut_down()


# Task
# ----

router_task = APIRouter(tags=["task"])

@router_task.get("/tasks", response_model=List[Task])
async def get_tasks():
    task_list =  [
        Task(
            start_cond=str(task.start_cond), 
            end_cond=str(task.end_cond),
            is_running=task.is_running,
            status=str(task.status),
            **task.dict(exclude={'start_cond', 'end_cond','status'})
        )
        for task in session.tasks
    ]

    return task_list

@router_task.get("/tasks/{task_name}")
async def get_task(task_name:str):
    return session[task_name]
    
@router_task.patch("/tasks/{task_name}")
async def patch_task(task_name:str, values:dict):
    task = session[task_name]
    for attr, val in values.items():
        setattr(task, attr, val)


# Task Actions
# ------------

@router_task.post("/tasks/{task_name}/pause")
async def pause_task(task_name:str):
    task = session[task_name]
    channel = f"/task/{task_name}"
    if pause(channel=channel,rps=rps):
        task.disabled = True

@router_task.post("/tasks/{task_name}/resume")
async def resume_task(task_name:str):
    task = session[task_name]
    channel = f"/task/{task_name}"
    resume(channel=channel,rps=rps)
    task.disabled = False

@router_task.post("/tasks/{task_name}/terminate")
async def terminate_task(task_name:str):
    task = session[task_name]
    channel = f"/task/{task_name}"
    if terminate(channel=channel,rps=rps):
        task.force_termination = True

@router_task.post("/tasks/{task_name}/end-subsciber-loop")
async def end_subscriber_loop(task_name:str):
    task = session[task_name]
    channel = f"/task/{task_name}"
    if close_client_loop(channel=channel,rps=rps):
        task.force_termination = True

@router_task.post("/tasks/{task_name}/start")
async def start_task(task_name:str):
    task = session[task_name]
    if not task.is_running:
        task.force_run = True


@router_task.get("/tasks/{task_name}/stream-logs")
async def stream_task_logs(request: Request, task_name:str):
    channel = re.sub(r'(?<!^)(?=[A-Z])', '-', task_name).lower()
    queue_name = f"/task/dtcc/{channel}/logs"
    event_generator = log_consumer(request, queue_name) 
    return EventSourceResponse(event_generator)


@router_task.post("/tasks/{task_name}/get-result")
async def get_result(task_name:str):
    task = session[task_name]
    if not task.is_running:
        if task.status == "success":
            return 
    else:
        return status.HTTP_425_TOO_EARLY



# Logging
# -------

router_logs = APIRouter(tags=["logs"])

@router_logs.get("/logs", description="Get tasks")
async def get_task_logs(action: Optional[List[Literal['run', 'success', 'fail', 'terminate', 'crash', 'inaction']]] = Query(default=[]),
                        min_created: Optional[int]=Query(default=None), max_created: Optional[int] = Query(default=None),
                        past: Optional[int]=Query(default=None),
                        limit: Optional[int]=Query(default=None),
                        task: Optional[List[str]] = Query(default=None)):
    filter = {}
    if action:
        filter['action'] = in_(action)
    if (min_created or max_created) and not past:
        filter['created'] = between(min_created, max_created, none_as_open=True)
    elif past:
        filter['created'] = greater_equal(time.time() - past)
    
    if task:
        filter['task_name'] = in_(task)

    repo = session.get_repo()
    logs = repo.filter_by(**filter).all()
    if limit:
        logs = logs[max(len(logs)-limit, 0):]
    logs = sorted(logs, key=lambda log: log.created, reverse=True)
    logs = [Log(**vars(log)) for log in logs]

    return logs

@router_logs.get("/task/{task_name}/logs", description="Get tasks")
async def get_task_logs(task_name:str,
                        action: Optional[List[Literal['run', 'success', 'fail', 'terminate', 'crash', 'inaction']]] = Query(default=[]),
                        min_created: Optional[int]=Query(default=None), max_created: Optional[int] = Query(default=None)):
    filter = {}
    if action:
        filter['action'] = in_(action)
    if min_created or max_created:
        filter['created'] = between(min_created, max_created, none_as_open=True)

    return session[task_name].logger.filter_by(**filter).all()


# Add routers
# -----------

app.include_router(router_config)
app.include_router(router_params)
app.include_router(router_session)
app.include_router(router_task)
app.include_router(router_logs)


 


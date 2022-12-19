#!/usr/bin/env python3

import os, pathlib, sys, datetime, time, re, asyncio, logging, json
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


logging.getLogger("pika").setLevel(logging.WARNING)


project_dir = str(pathlib.Path(__file__).resolve().parents[0])
sys.path.append(project_dir)

from logger import getLogger
from utils import try_except, DictStorage, file_exists, find_all_files_in_folder
from rabbitmq_service import PikaPubSub, log_consumer
from registry_manager import RegistryManager
from data_models import ModuleConfig, RequestMessage, ReturnMessage, ModuleRegistry, ModuleStatus

logger = getLogger(__file__)

pub_sub = PikaPubSub(queue_name="/task/run_sample_python_process")
pub_sub.publish(message={"cmd":"start"})

app = FastAPI(
    title="DTCC Core API",
    description="API for controlling modules",
    version="1.0"
)

registry_manager = RegistryManager()





def load_module_config():
    indexed_modules_config = {}
    modules_list = []
    config_file_paths = find_all_files_in_folder(project_dir,"module-config.json")

    for config_file_path in config_file_paths:
        modules_list.append(json.load(open(config_file_path,'r')))

    if len(modules_list)>0:
        for module_info in modules_list:
            tool_info_list = module_info.get("tools")
            for tool_info in tool_info_list:
                indexed_modules_config[f"{module_info['name']}/{tool_info['name']}"] = module_info
    else:
        raise Exception("No modules and module configs found!!")
                
    return indexed_modules_config

modules_config = load_module_config()


def check_if_module_exists(module_name, tool):
    key = f"{module_name}/{tool}"
    if key in modules_config.keys():
        return True, modules_config[key]
    return False, {}

def get_time_diff_in_minutes(iso_timestamp:str):
    diff = datetime.datetime.now() - datetime.datetime.fromisoformat(iso_timestamp)
    minutes, seconds = divmod(diff.total_seconds(), 60) 
    return int(minutes)



# Enable CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('startup')
async def startup():
    registry_manager.listen_for_modules()

@app.on_event("shutdown")
async def shutdown():
    registry_manager.close()



router_task = APIRouter(tags=["task"])

@router_task.get("/tasks", response_model=List[ModuleRegistry])
async def get_tasks():
    available_modules_info = []
    registered_modules = list(registry_manager.get_available_modules().values())
    for registered_module in registered_modules:
        time_diff_minutes = get_time_diff_in_minutes(registered_module.last_seen)
        print(registered_module.status, time_diff_minutes)
        if time_diff_minutes<2 and registered_module.status == ModuleStatus.waiting.value:
            print(registered_module)
            module_exists, module_info = check_if_module_exists(registered_module.module, registered_module.tool)
            if module_exists:
                print(module_info)
                module_config = ModuleConfig.parse_obj(module_info)
                registered_module.config =module_config
                print(registered_module)
                available_modules_info.append(registered_module)

    return available_modules_info



def get_channel(msg:RequestMessage):
    module = registry_manager.get_module_data(task_id=msg.task_id)
    channel = f"/task/{module.token}"
    return channel

def get_logs_channel(msg:RequestMessage):
    channel = f"/task/{msg.task_id}/logs"
    return channel


def on_response_from_pubsub_listener(ch, method, properties, body):
    ch.basic_ack(delivery_tag=method.delivery_tag)
    if body is not None: 
        message = json.loads(body)
        print("####################", message)
    return ReturnMessage(success=True)

@router_task.post("/task/start", response_model=ReturnMessage)
async def start_task(msg:RequestMessage):
    if registry_manager.check_if_module_is_registered(task_id=msg.task_id):
        module = registry_manager.get_module_data(task_id=msg.task_id)
        if module.is_running:
            return ReturnMessage(success=False, info="task is already running")
        else:
            channel = get_channel(msg)
            rps = PikaPubSub(queue_name=channel)
            message = {'cmd': "start" } 
            if len(msg.parameters)>0:
                try:
                    parameters = json.loads(msg.parameters.encode())
                    ## TODO Validate parameters here
                    message.update(parameters)
                except:
                    logger.exception("from parsing parameter json from start!!")
            
            if rps.publish(message=message):
                time.sleep(1)
                module_registry_data = registry_manager.get_module_data(msg.task_id)
                return ReturnMessage(success=True, status=module_registry_data)
    else:
        ## Check with module conf if module exists 
        module_exists, _ = check_if_module_exists(module_name=msg.name, tool=msg.tool)
        if module_exists:
            return ReturnMessage(success=False, info="module is not online")
        else:
            return ReturnMessage(success=False, info="module does not exist")


    

@router_task.post("/task/pause", response_model=ReturnMessage)
async def pause_task(msg:RequestMessage):
    if registry_manager.check_if_module_is_registered(task_id=msg.task_id):
        module = registry_manager.get_module_data(task_id=msg.task_id)
        if module.is_running:
            channel = get_channel(msg)
            rps = PikaPubSub(queue_name=channel)
            message = {'cmd': "pause" }
            
            if rps.publish(message=message):
                time.sleep(1)
                module_registry_data = registry_manager.get_module_data(msg.task_id)
                return ReturnMessage(success=True, status=module_registry_data)
        else:
            return ReturnMessage(success=False, info="task is not running")
    else:
        ## Check with module conf if module exists 
        module_exists, _ = check_if_module_exists(module_name=msg.name, tool=msg.tool)
        if module_exists:
            return ReturnMessage(success=False, info="module is not online")
        else:
            return ReturnMessage(success=False, info="module does not exist")

   
   

@router_task.post("/task/resume", response_model=ReturnMessage)
async def resume_task(msg:RequestMessage):
    if registry_manager.check_if_module_is_registered(task_id=msg.task_id):
        module = registry_manager.get_module_data(task_id=msg.task_id)
        if module.is_running:
            return ReturnMessage(success=False, info="task is already running")
        else:
            channel = get_channel(msg)
            rps = PikaPubSub(queue_name=channel)
            message = {'cmd': "resume" }

            if rps.publish(message=message):
                time.sleep(1)
                module_registry_data = registry_manager.get_module_data(msg.task_id)
                return ReturnMessage(success=True, status=module_registry_data)
    else:
        ## Check with module conf if module exists 
        module_exists, _ = check_if_module_exists(module_name=msg.name, tool=msg.tool)
        if module_exists:
            return ReturnMessage(success=False, info="module is not online")
        else:
            return ReturnMessage(success=False, info="module does not exist")

@router_task.post("/task/stop", response_model=ReturnMessage)
async def stop_task(msg:RequestMessage):
    if registry_manager.check_if_module_is_registered(task_id=msg.task_id):
        module = registry_manager.get_module_data(task_id=msg.task_id)
        if module.is_running:
            channel = get_channel(msg)
            rps = PikaPubSub(queue_name=channel)
            message = {'cmd': "stop" }

            if rps.publish(message=message):
                time.sleep(1)
                module_registry_data = registry_manager.get_module_data(msg.task_id)
                return ReturnMessage(success=True, status=module_registry_data)
        else:
            return ReturnMessage(success=False, info="task is not running")
            
    else:
        ## Check with module conf if module exists 
        module_exists, _ = check_if_module_exists(module_name=msg.name, tool=msg.tool)
        if module_exists:
            return ReturnMessage(success=False, info="module is not online")
        else:
            return ReturnMessage(success=False, info="module does not exist")


@router_task.post("/task/status", response_model=ReturnMessage)
async def get_status(msg: RequestMessage):
    if registry_manager.check_if_module_is_registered(task_id=msg.task_id):
        module = registry_manager.get_module_data(task_id=msg.task_id)
        if module.is_running:
            channel = get_channel(msg)
            rps = PikaPubSub(queue_name=channel)
            message = {'cmd': "status" }

            if rps.publish(message=message):
                time.sleep(1)
                module_registry_data = registry_manager.get_module_data(msg.task_id)
                return ReturnMessage(success=True, status=module_registry_data)
        else:
            module_registry_data = registry_manager.get_module_data(msg.task_id)
            return ReturnMessage(success=True, info="task is not running",status=module_registry_data)
            
    else:
        ## Check with module conf if module exists 
        module_exists, _ = check_if_module_exists(module_name=msg.name, tool=msg.tool)
        if module_exists:
            return ReturnMessage(success=False, info="module is not online")
        else:
            return ReturnMessage(success=False, info="module does not exist")
    



@router_task.get("/task/stream-stdout")
async def stream_task_stdout(msg:RequestMessage, request: Request):
    if registry_manager.check_if_module_is_registered(task_id=msg.task_id):
        module = registry_manager.get_module_data(task_id=msg.task_id)
        if module.is_running:
            channel = get_logs_channel(msg)
            event_generator = log_consumer(request, channel) 
            return EventSourceResponse(event_generator)
        else:
            return ReturnMessage(success=False, info="task is not running")
            
    else:
        ## Check with module conf if module exists 
        module_exists, _ = check_if_module_exists(module_name=msg.name, tool=msg.tool)
        if module_exists:
            return ReturnMessage(success=False, info="module is not online")
        else:
            return ReturnMessage(success=False, info="module does not exist")

   

"""
 TODO api for querying mongodb logs
1) get task logs Maybe filter on status and timestamp 
2) get task logs per module/tool/taskid
""" 


app.include_router(router_task)

fastapi_port = int(os.environ.get("FASTAPI_PORT", "8070"))

class Server(uvicorn.Server):
    """Customized uvicorn.Server
    Uvicorn server overrides signals"""
    def handle_exit(self, sig: int, frame) -> None:
        return super().handle_exit(sig, frame)

async def runner():
    server = Server(config=uvicorn.Config(app, workers=2, loop="asyncio", port=fastapi_port, host="0.0.0.0",log_level='info'))

    api = asyncio.create_task(server.serve())

    await asyncio.wait([api])

def main():
    asyncio.run(runner())

if __name__ == "__main__":
    main()
import os, pathlib, sys, datetime, time, re, asyncio, logging
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
import io
from grpc import channel_ready_future
from sqlalchemy import true
import uvicorn
from fastapi import FastAPI, Path, responses, status, Body, Query, BackgroundTasks, Response, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from enum import Enum, IntEnum
from sse_starlette.sse import EventSourceResponse


logging.getLogger("pika").setLevel(logging.WARNING)


project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from src.common.rabbitmq_service import log_consumer
from src.common.run_in_shell import RunInShell

app = FastAPI(
    title="DTCC Core demo API",
    description="API for db access and communication",
    version="1.0"
)

class ReturnMessage(BaseModel):
    success: bool = False


class SamplePythonProcessRunner(RunInShell):
    def __init__(self, publish=False) -> None:
        sample_logger_path = os.path.join(project_dir, "src/tests/sample_logging_process.py")
        command=f'python3 {sample_logger_path}'

        RunInShell.__init__(self,
            task_name="sample_python_process",
            publish=publish,
            shell_command=command
        )

    def process_arguments_on_start(self, message:dict):
        return self.shell_command

    def process_return_data(self):
        return "dummy result"


process_runner = SamplePythonProcessRunner(publish=True)

# Enable CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




router_task = APIRouter(tags=["task"])

@router_task.post("/task/pause", response_model=ReturnMessage)
async def pause_task():
    success = process_runner.pause()
    return ReturnMessage(success=success)

@router_task.post("/task/resume", response_model=ReturnMessage)
async def resume_task():
    success = process_runner.resume()
    return ReturnMessage(success=success)

@router_task.post("/task/terminate", response_model=ReturnMessage)
async def terminate_task():
   success = process_runner.terminate()
   return ReturnMessage(success=success)

@router_task.post("/task/start", response_model=ReturnMessage)
async def start_task():
    success = process_runner.start()
    return ReturnMessage(success=success)


@router_task.get("/task/stream-logs")
async def stream_task_logs(request: Request):
    queue_name = process_runner.channel
    event_generator = log_consumer(request, queue_name) 
    return EventSourceResponse(event_generator)

app.include_router(router_task)

fastapi_port = int(os.environ.get("FASTAPI_PORT", "8070"))

class Server(uvicorn.Server):
    """Customized uvicorn.Server
    
    Uvicorn server overrides signals and we need to include
    Rocketry to the signals."""
    def handle_exit(self, sig: int, frame) -> None:
        return super().handle_exit(sig, frame)

async def main():
    "Run Rocketry and FastAPI"
    server = Server(config=uvicorn.Config(app, workers=2, loop="asyncio", port=fastapi_port, host="0.0.0.0",log_level='info'))

    api = asyncio.create_task(server.serve())

    await asyncio.wait([api])

if __name__ == "__main__":
    asyncio.run(main())
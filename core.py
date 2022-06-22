import os,sys, json, pathlib, threading, asyncio, time, datetime, pickle, logging

import uvicorn
from fastapi import FastAPI, Path, responses, status, Body, Query, BackgroundTasks, Response
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum, IntEnum

project_dir = str(pathlib.Path(__file__).resolve().parents[0])

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DTCC Core API",
    description="API for db access and communication",
    version="1.0"
)

class StatusEnum(str, Enum):
    idle = 'idle'
    ready = 'ready to start!'
    in_progress = 'path planning in progress!'
    success = 'path planning generated a path successfully!'
    failed = "Failed path not found"
    error = "error"

class StatusMessage(BaseModel):
    status:StatusEnum = StatusEnum.idle
    msg:str = ''
    class Config:
        orm_mode = True


@app.on_event('startup')
async def startup():
    pass

@app.on_event("shutdown")
async def shutdown():
    pass

## API
@app.get("/api/maps/list",response_model=dict)
async def get_maps_list():
    return []

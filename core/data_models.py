from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from enum import Enum, IntEnum

class ModuleStatus(Enum):
    started = "started"
    paused = "paused"
    resumed = "resumed"
    stopped = "stopped"
    terminated = "terminated"
    running = "running"
    success = "success"
    failed = "failed"
    waiting = "waiting"
    processing_input = "processing_input"
    processing_output = "processing_output"

class Stdout(BaseModel):
    task_id:str
    percent:int
    level:str
    line_number:int
    message:str



class Input(BaseModel):
    name:str
    type:str

class Output(BaseModel):
    name:str
    type:str

class Parameters(BaseModel):
    name: str
    description: Optional[str]
    type:str
    required:bool


class Tool(BaseModel):
    name: str
    description: Optional[str]
    category:str
    input: List[Input]
    output: List[Output]
    parameters: List[Parameters]
    

class ModuleConfig(BaseModel):
    name: str
    description: Optional[str]
    tools: List[Tool]
    
class ModuleRegistry(BaseModel):
    token:str
    task_id:str
    module: str
    tool: str
    is_running:bool
    last_seen: str
    status: str
    info: Optional[str]
    result:Optional[str]
    config: Optional[ModuleConfig]


class RequestMessage(BaseModel):
    task_id:str
    name:Optional[str] = Field("",description="module name needed for start command")
    tool:Optional[str] = Field("",description="tool name needed for start command")
    parameters:Optional[str] = Field("",description="Parameters needed for start command")

class ReturnMessage(BaseModel):
    success: bool = False
    info:Optional[str] = ""
    status: Optional[ModuleRegistry] ## Expect this on success

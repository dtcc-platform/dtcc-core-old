from fastapi import FastAPI
#import sys
#from pathlib import Path

#sys.path.append( str((Path(__file__).parent / "../src").resolve() ))
#from dtcc import core
from dtcc.core import *
#import sys
#sys.path.insert(0, '/home/dtcc/dtcc-core/')
#from dtcc.core import *

app = FastAPI()
c = Core()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/get-projects")
async def root():
    response=c.GetProjects()
    return response

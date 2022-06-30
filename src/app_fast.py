from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
import io
#import sys
#from pathlib import Path

#sys.path.append( str((Path(__file__).parent / "../src").resolve() ))
#from dtcc import core
from dtcc.core import *
#import sys
#sys.path.insert(0, '/home/dtcc/dtcc-core/')
#from dtcc.core import *


#def GetProjects(self):
#    def GetAvailableDataSetNames(self):
#    def GetGeneratedDataSetNames(self, project):
#    def GetDataSet(self, project, name):
#    def GenerateDataSet(self, project, name):

app = FastAPI()
c = Core()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/get-projects")
async def root():
    response=c.GetProjects()
    return response
@app.get("/api/GetAvailableDataSetNames")
async def availdatasetnames():
    response=c.GetAvailableDataSetNames()
    return response
@app.get("/api/GetGeneratedDataSetNames/{project}")
async def gendatasetnames(project):
    response=c.GetGeneratedDataSetNames(project)
    return response
#    def GetDataSet(self, project, name):
@app.get("/api/GetDataSet/{project}/{name}")
async def dataset(project,name):
    response=c.GetDataSet(project,name)
#    print(response)
#    file = io.BytesIO(response["data"])
#    return FileResponse(file, media_type="attachment/x-protobuf")
#    return StreamingResponse(content=response["data"])
    return StreamingResponse(io.BytesIO(response["data"]), media_type="attachment/x-protobuf")

from fastapi import FastAPI
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

app = FastAPI(
    title="DTCC Core API",
    description="API for db access and communication",
    version="1.0"
)
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
    return reponse
@app.get("/api/GetGeneratedDataSetNames/{project}")
async def gendatasetnames(project):
    response=c.GetGeneratedDataSetNames(project)
    return reponse

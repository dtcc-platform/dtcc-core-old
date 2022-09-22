import os, pathlib, sys, threading
import asyncio
import pytest
from httpx import AsyncClient

project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from src.app_fast import app , status, scheduler

task_name = "dummy_logs_publisher"

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop


@pytest.mark.asyncio
async def test_stream_logs():
    max_lines = 20
    i = 0
    sched = asyncio.create_task(scheduler.serve())
 
    asyncio.wait([sched])
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        response = await client.post(f"/tasks/{task_name}/run")

        assert response.status_code == status.HTTP_200_OK
        async with client.stream("GET", f"/tasks/{task_name}/stream-logs") as response:
            print('------------', response)
            async for line in response.aiter_lines():
                if i > max_lines:
                    break
                assert "sample logging process" in line.strip() 
                print('-------->>>> ', i, line.strip())
                i += 1
    
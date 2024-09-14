from typing import List
import time

from fastapi.testclient import TestClient
from psik import JobSpec

from psik_api.main import api
from psik_api.compute import QueueOutput
from psik_api.tasks import PostTaskResult, Task, Tasks

from .test_config import setup_psik

# docs: python-httpx.org/advanced/
client = TestClient(api)

def test_get_jobs(setup_psik) -> None:
    response = client.get("/compute/jobs/_nohost")
    assert response.status_code == 404 \
           or response.status_code == 422 

    response = client.get("/compute/jobs/default")
    assert response.status_code == 200
    resp = response.json()
    QueueOutput.model_validate(resp)

def test_post_job(setup_psik) -> None:
    spec = JobSpec(script="echo 'OK'")
    response = client.post("/compute/jobs/default",
                           json = spec.model_dump())
    assert response.status_code == 200
    resp = PostTaskResult.model_validate( response.json() )
    tid = resp.task_id

    response = client.get("/tasks")
    assert response.status_code == 200
    resp2 = Tasks.model_validate(response.json()).tasks
    assert isinstance(resp2, list)
    assert len(resp2) == 1
    assert resp2[0].id == tid
    print(tid, resp2[0])

    response = client.get(f"/tasks/{tid}")
    assert response.status_code == 200
    resp3 = Task.model_validate(response.json())
    assert resp3.id == tid
    jobid = resp3.result
    print(jobid)
    time.sleep(0.5)
    if resp3.status == "completed":
        response = client.get(f"/compute/jobs/default/{jobid}")
        assert response.status_code == 200

        response = client.delete(f"/compute/jobs/default/{jobid}")
        assert response.status_code == 200

def test_read_job(setup_psik) -> None:
    response = client.get("/compute/jobs/default/_nojob")
    assert response.status_code == 404

def test_delete_job(setup_psik) -> None:
    response = client.delete("/compute/jobs/default/_nojob")
    assert response.status_code == 404

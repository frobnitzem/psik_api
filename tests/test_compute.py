from typing import List
import time

from fastapi.testclient import TestClient
from psik import JobSpec

from psik_api.main import api
from psik_api.models import JobStepInfo

from .test_config import setup_psik

# docs: python-httpx.org/advanced/
client = TestClient(api)

def test_get_jobs(setup_psik) -> None:
    response = client.get("/jobs/_nohost")
    assert response.status_code == 404 \
           or response.status_code == 422 

    response = client.get("/jobs/default")
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, list)
    for r in resp:
        JobStepInfo.model_validate(r)

def test_post_job(setup_psik) -> None:
    spec = JobSpec(script="echo 'OK'")
    response = client.post("/jobs/default",
                           json = spec.model_dump())
    assert response.status_code == 200
    jobid = response.json()
    assert isinstance(jobid, str)

    time.sleep(0.5)

    response = client.get(f"/jobs/default/{jobid}")
    resp = response.json()
    assert isinstance(resp, list)
    jobsteps = [JobStepInfo.model_validate(r) for r in resp]
    print(jobsteps)

    response = client.delete(f"/jobs/default/{jobid}")
    assert response.status_code == 200

def test_read_job(setup_psik) -> None:
    response = client.get("/jobs/default/_nojob")
    assert response.status_code == 400

def test_delete_job(setup_psik) -> None:
    response = client.delete("/jobs/default/_nojob")
    assert response.status_code == 400

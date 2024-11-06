from typing import List
import time

from fastapi.testclient import TestClient
from psik import JobSpec

from psik_api.main import api
from psik_api.models import JobStepInfo

from .test_config import setup_psik
from .test_psik_api import client

def test_get_jobs(client) -> None:
    response = client.get("/jobs", params={"backend":"_nohost"})
    assert response.status_code == 404 \
           or response.status_code == 422 

    response = client.get("/jobs", params={"backend":"default"})
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, list)
    for r in resp:
        JobStepInfo.model_validate(r)

    for route in ["/jobs", "/jobs/"]:
        response = client.get(route)
        assert response.status_code == 200
        resp = response.json()
        assert isinstance(resp, list)
        for r in resp:
            JobStepInfo.model_validate(r)

def test_post_job(client) -> None:
    spec = JobSpec(script="echo 'OK'")
    response = client.post("/jobs", params={"backend":"default"},
                           json = spec.model_dump())
    assert response.status_code == 200
    jobid = response.json()
    assert isinstance(jobid, str)

    time.sleep(0.5)

    response = client.get(f"/jobs/{jobid}", params={"backend":"default"})
    resp = response.json()
    assert isinstance(resp, list)
    jobsteps = [JobStepInfo.model_validate(r) for r in resp]
    print(jobsteps)

    response = client.delete(f"/jobs/{jobid}", params={"backend":"default"})
    assert response.status_code == 200

    ## test nonexistent backend
    spec = JobSpec(name="hello", script="echo world")
    response = client.post("/jobs", params={"backend":"_nonexistent"},
                           json = spec.model_dump())
    assert response.status_code//100 == 4

    ## test no explicit backend
    spec = JobSpec(name="hello", script="echo world")
    response = client.post("/jobs", json = spec.model_dump())
    assert response.status_code == 200
    jobid = response.json()
    assert isinstance(jobid, str)

    response = client.get(f"/jobs/{jobid}")
    resp = response.json()
    assert isinstance(resp, list)
    jobsteps = [JobStepInfo.model_validate(r) for r in resp]
    print(jobsteps)

    response = client.delete(f"/jobs/{jobid}")
    assert response.status_code == 200

def test_read_job(client) -> None:
    response = client.get("/jobs/0000.123")
    assert response.status_code == 404

    response = client.get("/jobs/0000.123", params={"backend":"default"})
    assert response.status_code == 404

def test_delete_job(client) -> None:
    response = client.delete("/jobs/0000.123")
    assert response.status_code == 404

    response = client.delete("/jobs/0000.123", params={"backend":"default"})
    assert response.status_code == 404

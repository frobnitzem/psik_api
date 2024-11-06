from typing import List
import time

from fastapi.testclient import TestClient
from psik import JobSpec

from psik_api.main import api
from psik_api.models import JobStepInfo, JobState

from .test_config import setup_psik
from .test_psik_api import client

def test_post_job(client) -> None:
    spec = JobSpec(script="echo 'OK' >out.txt; cat out.txt;")
    response = client.post("/jobs", json = spec.model_dump())
    assert response.status_code == 200
    jobid = response.json()
    assert isinstance(jobid, str)

    for i in range(100):
        time.sleep(0.1)
        response = client.get(f"/jobs/{jobid}/state")
        assert response.status_code == 200
        state = JobState(response.json())
        if state == JobState.completed:
            break
    else:
        assert False, f"Job status is {response.text}"

    response = client.get(f"/jobs/{jobid}/logs")
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, dict)
    for k, v in resp.items():
        assert isinstance(k, str)
        assert isinstance(v, str)
    assert "OK" in resp["stdout.1"]

    for route in ["scripts/", "scripts"]:
        response = client.get(f"/jobs/{jobid}/{route}")
        assert response.status_code == 200
        resp = response.json()
        assert isinstance(resp, dict)
        for k, v in resp.items():
            assert isinstance(k, str)
            assert isinstance(v, str)

    for route in ["files/", "files"]:
        response = client.get(f"/jobs/{jobid}/{route}")
        assert response.status_code == 200
        resp = response.json()
        assert isinstance(resp, dict)
        for k, v in resp.items():
            assert isinstance(k, str)
            assert isinstance(v, dict)
            assert v['size'] > 0
            assert v['atime'] > 0
            assert v['mtime'] > 0

    response = client.get(f"/jobs/{jobid}/files/out.txt")
    assert response.status_code == 200
    assert "OK" in response.text

    response = client.get(f"/jobs/{jobid}/files/run")
    assert response.status_code//100 == 4

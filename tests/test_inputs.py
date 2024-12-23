from typing import List
import time

from fastapi.testclient import TestClient
from psik import JobSpec

from psik_api.main import api
from psik_api.models import JobStepInfo, JobState

from .test_config import setup_psik
from .test_psik_api import client

# docs: python-httpx.org/advanced/

def test_post_new(client) -> None:
    spec = JobSpec(script="echo 'OK' >out.txt; cat out.txt;")
    response = client.post("/jobs/new", json = spec.model_dump())
    assert response.status_code == 200
    jobid = response.json()
    assert isinstance(jobid, str)

    response = client.get(f"/jobs/{jobid}")
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, list)
    assert len(resp) == 1
    info = JobStepInfo.model_validate(resp[0])
    assert info.state == JobState.new

    # https://www.python-httpx.org/advanced/clients/
    # files = [('images', ('foo.png', open('foo.png', 'rb'), 'image/png')),
    #          ('images', ('bar.png', open('bar.png', 'rb'), 'image/png'))]
    # files = {'upload-file': ('name', 'text content', 'text/plain')}
    #files = {'upload-file': ('input.txt', 'Hello World!\n', 'text/plain')}
    files = [('files', ('input.txt', 'Hello World!\n', 'text/plain'))]
    response = client.post(f"/jobs/{jobid}/files", files=files)
    print(response.text)
    assert response.status_code == 200

    response = client.get(f"/jobs/{jobid}/files/input.txt")
    assert response.status_code == 200
    assert "Hello World!" in response.text

    response = client.post(f"/jobs/{jobid}/start")
    assert response.status_code == 200
    print(response.text)

    time.sleep(0.5)
    response = client.get(f"/jobs/{jobid}")
    resp = response.json()
    assert isinstance(resp, list)
    jobsteps = [JobStepInfo.model_validate(r) for r in resp]
    print(jobsteps)
    assert len(jobsteps) > 1

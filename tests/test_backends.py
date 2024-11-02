from typing import List

from fastapi.testclient import TestClient

from psik_api.main import api
from psik_api.status import SystemStatus

from .test_config import setup_psik

# docs: python-httpx.org/advanced/
client = TestClient(api)

def test_get_status(setup_psik):
    response = client.get("/status")
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, dict)
    for r in resp.values():
        SystemStatus.model_validate(r)

def test_read_status(setup_psik):
    response = client.get("/status", params={"name": "_nonexistent"})
    assert response.status_code == 404 or response.status_code == 422
    response = client.get("/status", params={"name": "default"})
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(response.json(), dict)
    assert len(resp) == 1
    r = resp["default"]
    SystemStatus.model_validate(r)

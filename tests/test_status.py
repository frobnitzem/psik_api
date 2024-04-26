from typing import List

from fastapi.testclient import TestClient

from psik_api.main import api
from psik_api.status import SystemStatus, Outage

# docs: python-httpx.org/advanced/
client = TestClient(api)

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, list)
    for r in resp:
        SystemStatus.model_validate(r)

def test_read_status():
    response = client.get("/status", params={"name": "_nonexistent"})
    assert response.status_code == 404 or response.status_code == 422
    response = client.get("/status", params={"name": "summit"})
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(response.json(), list)
    assert len(resp) == 1
    for r in resp:
        SystemStatus.model_validate(r)

def test_get_outages():
    response = client.get("/status/outages")
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, list)
    for r in resp:
        Outage.model_validate(r)

def test_read_outage():
    response = client.get("/status/outages", params={"name": "_nonexistent"})
    assert response.status_code == 404 or response.status_code == 422
    response = client.get("/status/outages", params={"name": "summit"})
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, list)
    for r in resp:
        Outage.model_validate(r)

def test_get_planned_outages():
    response = client.get("/status/outages/planned")
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, list)
    for r in resp:
        Outage.model_validate(r)

def test_read_planned_outage():
    response = client.get("/status/outages/planned", params={"name": "_nonexistent"})
    assert response.status_code == 404 or response.status_code == 422
    response = client.get("/status/outages/planned", params={"name": "summit"})
    assert response.status_code == 200
    resp = response.json()
    assert isinstance(resp, list)
    for r in resp:
        Outage.model_validate(r)

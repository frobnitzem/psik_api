from typing import List

from fastapi.testclient import TestClient

from psik_api.main import api
from psik_api.routers.backends import SystemStatus

from .test_config import setup_psik

# docs: python-httpx.org/advanced/
client = TestClient(api)

def test_get_backends(setup_psik):
    for route in "/backends", "/backends/":
        response = client.get(route)
        assert response.status_code == 200
        resp = response.json()
        assert isinstance(resp, dict)
        for r in resp.values():
            SystemStatus.model_validate(r)

def test_read_backends(setup_psik):
    for route in "/backends", "/backends/":
        response = client.get(route, params={"name": "_nonexistent"})
        assert response.status_code == 404 or response.status_code == 422

        response = client.get(route, params={"name": "default"})
        assert response.status_code == 200
        resp = response.json()
        assert isinstance(resp, dict)
        assert len(resp) == 1
        r = resp["default"]
        SystemStatus.model_validate(r)

def test_read_backend(setup_psik):
    response = client.get("/backends/_nonexistent")
    assert response.status_code == 404 or response.status_code == 422

    response = client.get("/backends/default")
    assert response.status_code == 200
    SystemStatus.model_validate_json(response.text)

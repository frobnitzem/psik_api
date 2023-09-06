from fastapi.testclient import TestClient

from olcf_api import __version__
from olcf_api.main import api

client = TestClient(api)

def test_version():
    assert len(__version__.split('.')) == 3

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200

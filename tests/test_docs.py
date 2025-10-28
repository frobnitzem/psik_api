import pytest
from fastapi.testclient import TestClient

from psik_api.main import api

from .test_config import setup_psik

@pytest.fixture
def client(setup_psik):
    with TestClient(api) as c:
      yield c

def test_download_docs(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    print(response.text)

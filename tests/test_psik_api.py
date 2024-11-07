import pytest
from fastapi.testclient import TestClient

from psik_api import __version__
from psik_api.main import api

from .test_config import setup_psik

@pytest.fixture
def client(setup_psik):
    with TestClient(api) as c:
      yield c

#headers={"Authorization": f"Bearer {token}"}

def test_version():
    assert len(__version__.split('.')) == 3

def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200

    response = client.get("")
    assert response.status_code == 200

def test_token(client):
    response = client.get("/token")
    assert response.status_code == 200
    tok = response.text
    print(tok)

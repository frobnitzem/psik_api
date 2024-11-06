import pytest

from fastapi.testclient import TestClient

from psik_api.main import api

from .test_config import setup_psik

# Have to skip this one, since it only works
# if no other tests have run (uninitialized state).
@pytest.mark.skip
def test_uninitialized(setup_psik):
    client = TestClient(api)
    response = client.get("/")
    assert response.status_code == 200
    response = client.get("/token")
    assert response.status_code == 200

    response = client.get("/jobs")
    assert response.status_code == 501

import sys
import os
import pytest

from fastapi.testclient import TestClient

from psik_api.main import api
from psik_api import dependencies

from .test_config import setup_psik

# Somehow doesn't help.
#if dependencies._Authz != dependencies.fail_auth:
#    pytest.skip("skipping uninit tests (already initialized)", allow_module_level=True)

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

def test_secure(tmp_path):
    cfg = tmp_path/"psik_api.json"
    # Use default (non-local) auth.
    cfg.write_text("""
    { "backends": {
        "default": {
          "prefix": "%s",
          "backend": {"type": "local"}
        }
      }
    }
    """ % str(tmp_path/"psik_jobs"))
    os.environ["PSIK_API_CONFIG"] = str(cfg)

    with TestClient(api) as client:
        with pytest.raises(KeyError): # 0.10.0 raises this
            response = client.get("/jobs")
            assert response.status_code == 403 # 1.0 does this.
            raise KeyError("ok")

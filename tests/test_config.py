from pathlib import Path
import pytest

import os
import json

import psik
from psik_api.config import get_manager, list_backends

@pytest.fixture
def setup_psik(tmp_path):
    cfg = tmp_path/"psik_api.json"
    cfg.write_text("""
    { "prefix": "%s",
      "backends": {
        "default": {
          "type": "local"
        }
      },
      "authz": "local"
    }
    """ % str(tmp_path/"psik_jobs"))
    os.environ["PSIK_API_CONFIG"] = str(cfg)
    return cfg

def test_config(setup_psik):
    mgr = get_manager(setup_psik)
    assert isinstance(mgr, psik.JobManager)
    assert tuple(list_backends(setup_psik)) == ("default",)
    #with pytest.raises(json.decoder.JSONDecodeError):
    #    pass
    mgr = get_manager(setup_psik)
    assert isinstance(mgr, psik.JobManager)

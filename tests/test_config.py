from pathlib import Path
import pytest

import os
import json

import psik
from psik_api.config import get_manager, list_managers

@pytest.fixture
def setup_psik(tmp_path):
    cfg = tmp_path/"psik_api.json"
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
    return cfg

def test_config(setup_psik):
    mgr = get_manager("default", setup_psik)
    assert isinstance(mgr, psik.JobManager)
    with pytest.raises(KeyError):
        mgr = get_manager("local", setup_psik)
    assert tuple(list_managers(setup_psik)) == ("default",)
    #with pytest.raises(json.decoder.JSONDecodeError):
    #    pass
    mgr = get_manager(None, setup_psik)
    assert isinstance(mgr, psik.JobManager)

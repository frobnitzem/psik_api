from pathlib import Path
import pytest

import os
import json

import psik
from psik_api.config import get_manager, load_config

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
    cfg = load_config(setup_psik)
    assert tuple(cfg.backends.keys()) == ("default",)
    #with pytest.raises(json.decoder.JSONDecodeError):
    #    pass
    mgr = get_manager(setup_psik)
    assert isinstance(mgr, psik.JobManager)

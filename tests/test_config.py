from pathlib import Path
import pytest

import json

import psik
from psik_api.config import managers

@pytest.fixture
def setup_psik(tmp_path):
    cfg = tmp_path/"psik_api.json"
    cfg.write_text("""
    { "default": {
        "prefix": "%s",
        "backend": { "type": "local"}
      }
    }
    """ % str(tmp_path/"psik_jobs"))

    managers.setup(cfg)

def test_config(setup_psik):
    mgr = managers["default"]
    assert isinstance(mgr, psik.JobManager)
    with pytest.raises(KeyError):
        mgr = managers["local"]
    #with pytest.raises(json.decoder.JSONDecodeError):
    #    pass

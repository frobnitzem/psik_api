import os
import json
from functools import cache
from typing import Dict

from pathlib import Path

import psik

def to_mgr(info):
    cfg = psik.Config.model_validate(info)
    return psik.JobManager(cfg)

@cache
def get_managers() -> Dict[str, psik.JobManager]:
    cfg_name = 'psik_api.json'
    if "PSIK_API_CONFIG" in os.environ:
        path = Path(os.environ["PSIK_API_CONFIG"])
    else:
        path = Path(os.environ["HOME"]) / '.config' / cfg_name
    if not path.exists():
        return { "default": to_mgr({
                    "prefix": "/tmp/psik_jobs",
                    "backend": { "type": "local"} })
               }
    #assert path.exists(), f"{cfg_name} is required to exist (tried {path})"

    with open(path, "r", encoding="utf-8") as f:
        ans = json.load(f)

    return dict( (k,to_mgr(v)) for k,v in ans.items() )

managers = get_managers()

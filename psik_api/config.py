from typing import Dict, Union, Optional
import os
import json

from pathlib import Path

import psik

def to_mgr(info):
    cfg = psik.Config.model_validate(info)
    cfg.prefix.mkdir(exist_ok=True, parents=True)
    return psik.JobManager(cfg)

Pstr = Union[str, os.PathLike[str]]

def get_managers(config_name : Optional[Pstr] = None
                ) -> Dict[str, psik.JobManager]:
    """Lookup and return the dict of job managers found in
    psik_api's configuration file.

    Priority order is:
      1. config_name (if not None)
      2. $PSIK_API_CONFIG (if defined)
      3. $VIRTUAL_ENV/etc/psik_api.json (if VIRTUAL_ENV defined)
      4. /etc/psik_api.json

    Note: The return value of this function is cached,
          so changes to environment variables have
          no effect after the first return from this function.

    Args:
      config_name: if defined, the configuration is read from this file

    Raises:
      FileNotFoundError: If the file does not exist.
      IsADirectoryError: Path does not point to a file.
      PermissionError:   If the file cannot be read.
    """
    cfg_name = "psik_api.json"
    if config_name is not None:
        path = Path(config_name)
    elif "PSIK_API_CONFIG" in os.environ:
        path = Path(os.environ["PSIK_API_CONFIG"])
    else:
        path = Path(os.environ.get("VIRTUAL_ENV", "/")) / "etc" / cfg_name
    #if not path.exists():
    #    return { "default": to_mgr({
    #                "prefix": "/tmp/psik_jobs",
    #                "backend": { "type": "local"} })
    #           }
    #assert path.exists(), f"{cfg_name} is required to exist (tried {path})"

    with open(path, "r", encoding="utf-8") as f:
        ans = json.load(f)

    return dict( (k,to_mgr(v)) for k,v in ans.items() )

class Managers(dict):
    # Simple class to cache the result of get_managers
    def __init__(self):
        self._is_init = False
        self._old_get = super().__getitem__
    def setup(self, config_name : Optional[Pstr] = None):
        for k, v in get_managers(config_name).items():
            self[k] = v
        self._is_init = True
    def __getitem__(self, mgr):
        if not self._is_init:
            self.setup()
        return self._old_get(mgr)

managers = Managers()

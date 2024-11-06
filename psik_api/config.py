from typing import Dict, Union, Optional, List
import os
import json
from functools import cache
from pathlib import Path

from pydantic import BaseModel
import psik

class Config(BaseModel):
    database_url: str = "sqlite+pysqlite:///:memory:"
    authz: str = "psik_api.authz:BaseAuthz"
    backends: Dict[str, psik.Config]

Pstr = Union[str, Path]

@cache
def load_config(config_name : Optional[Pstr] = None) -> Config:
    """Load psik_api's configuration file.

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
    cfg = path.read_text(encoding='utf-8')
    return Config.model_validate_json(cfg)

def to_mgr(cfg: psik.Config) -> psik.JobManager:
    cfg.prefix.mkdir(exist_ok=True, parents=True)
    return psik.JobManager(cfg)

@cache
def get_managers(config_name : Optional[Pstr] = None
                ) -> Dict[str, psik.JobManager]:
    """Lookup and return the dict of job managers found in
    psik_api's configuration file.
    """
    config = load_config(config_name)
    return dict( (k,to_mgr(v)) for k,v in config.backends.items() )

@cache
def get_manager(mgr: Optional[str] = None,
                config_name: Optional[Pstr] = None) -> psik.JobManager:
    """Return the named manager / backend.
    If mgr is None, returns the first defined backend.
    """
    managers = get_managers(config_name)
    if mgr is None:
        if len(managers) > 0:
            mgr = list(managers.keys())[0]
        else:
            raise KeyError("No backends defined.")
    return managers[mgr]

@cache
def list_managers(config_name: Optional[Pstr] = None) -> List[str]:
    managers = get_managers(config_name)
    return list(managers.keys())

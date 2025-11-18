from enum import Enum
from typing import Dict, List, Optional
from datetime import date as date_, datetime, timezone, timedelta
import logging
_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from psik.models import BackendConfig
from ..config import load_config, Config

backends = APIRouter()

@backends.get("/{name}")
async def get_backend(name: str) -> BackendConfig:
    "Get information on a specific backend."

    cfg = load_config()
    try:
        backend = cfg.backends[name]
    except KeyError:
        raise HTTPException(status_code=404, detail="Backend not found")
    return backend

@backends.get("/", include_in_schema=False)
@backends.get("")
async def get_backends(name: Optional[str] = None,
                       type: Optional[str] = None,
                      ) -> Dict[str, BackendConfig]:
    "Get information on all backends."

    if name is not None:
        x = await get_backend(name)
        return {name: x}

    cfg = load_config()
    ans = dict(cfg.backends)
    if type is not None:
        ans = dict((k,v) for k,v in ans.items() if v.type == type)
    return ans

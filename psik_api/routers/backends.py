from enum import Enum
from typing import Dict, List, Optional
from datetime import date as date_, datetime, timezone, timedelta
import logging
_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from ..config import list_backends, load_config, Config

# Data models specific to status routes:
class StatusValue(str, Enum):
    active = "active"
    unavailable = "unavailable"
    degraded = "degraded"
    other = "other"

class SystemStatus(BaseModel):
    name: str                  = Field(..., title = "System Name")
    full_name: Optional[str]   = Field(None, title="Full System Name")
    description: Optional[str] = Field(None, title="Description")
    system_type: Optional[str] = Field(None, title="System Type")
    notes: List[str]           = Field([], title="Status Notes")
    status: StatusValue
    updated_at: Optional[datetime] = Field(None, title="Updated At")

class Note(BaseModel):
    name: str = Field(..., title="System Name")
    notes: Optional[str] = Field(None, title="Notes")
    active: Optional[bool] = Field(False, title="Active")
    timestamp: Optional[datetime] = Field(None, title="Timestamp")

backends = APIRouter()

def get_info(cfg: Config, n: str) -> SystemStatus:
    backend = cfg.backends[n]
    return SystemStatus(name = n,
                    full_name = n,
                    description = f"psik:{backend.type} job manager at {cfg.prefix}",
                    system_type = backend.type,
                    notes = [],
                    status = StatusValue.active,
                    updated_at = datetime.now())

@backends.get("")
@backends.get("/")
async def get_backends(name: Optional[str] = None) -> Dict[str, SystemStatus]:
    "Get information on all backends."
    #await update_status()

    cfg = load_config()
    mgrs = list_backends()
    if name is None:
        return dict( (n,get_info(cfg, n)) for n in mgrs )
    elif name not in mgrs:
        raise HTTPException(status_code=404, detail="Item not found")
    return { name : get_info(cfg, name) }

@backends.get("/{name}")
async def get_backend(name: str) -> SystemStatus:
    "Get information on a specific backend."
    return (await get_backends(name))[name]

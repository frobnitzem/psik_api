from enum import Enum
from typing import Dict, List, Optional
from datetime import date as date_, datetime, timezone, timedelta
import logging
_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from .queries import get_http, fetch_current_status
from .config import managers

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

status = APIRouter()

@status.get("/")
async def get_status(name : Optional[str] = None) -> Dict[str, SystemStatus]:
    "Read system status information"
    #await update_status()

    get_info = lambda n: SystemStatus(name = n,
                    full_name = n,
                    description = f"psik {managers[n].config.backend.type} job manager at {managers[n].config.prefix}",
                    system_type = managers[n].config.backend.type,
                    notes = [],
                    status = StatusValue.active,
                    updated_at = datetime.now())
    if name is None:
        return dict( (n,get_info(n)) for n in managers.keys() )
    elif name not in managers:
        raise HTTPException(status_code=404, detail="Item not found")
    return { name : get_info(name) }

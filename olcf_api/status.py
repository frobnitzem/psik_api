from enum import Enum
from typing import Dict, List, Optional
from datetime import date as date_, datetime, timezone, timedelta
import logging
_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from .queries import get_json
#from .models import PublicHost

# https://fastapi.tiangolo.com/tutorial/bigger-applications/

# Data models specific to status routes:
class StatusValue(str, Enum):
    active = "active"
    unavailable = "unavailable"
    degraded = "degraded"
    other = "other"

class SystemStatus(BaseModel):
    name: str = Field(..., title="Name")
    full_name: Optional[str] = Field(None, title="Full Name")
    description: Optional[str] = Field(None, title="Description")
    system_type: Optional[str] = Field(None, title="System Type")
    notes: Optional[List[str]] = Field(None, title="Notes")
    status: StatusValue
    updated_at: Optional[datetime] = Field(None, title="Updated At")

class Note(BaseModel):
    name: str = Field(..., title="Name")
    notes: Optional[str] = Field(None, title="Notes")
    active: Optional[bool] = Field(False, title="Active")
    timestamp: Optional[datetime] = Field(None, title="Timestamp")

class Outage(BaseModel):
    name: str = Field(..., title="Name")
    start_at: Optional[datetime] = Field(None, title="Start At")
    end_at: Optional[datetime] = Field(None, title="End At")
    description: Optional[str] = Field(None, title="Description")
    notes: Optional[str] = Field(None, title="Notes")
    status: Optional[str] = Field(None, title="Status")
    swo: Optional[str] = Field(None, title="Swo")
    update_at: Optional[datetime] = Field(None, title="Update At")


status = APIRouter()

# An old date sure to trigger a refresh:
t0 = datetime.fromisoformat('1970-01-01T00:00:00').replace(tzinfo=timezone.utc)
# Mappings from system name to statuses
current_status  : Dict[str, SystemStatus] = {}
current_outages : Dict[str, List[Outage]] = {}
last_status_query  : datetime = t0
last_outage_query  : datetime = t0
# This is not an active timer.
# It is the time interval on which API queries will trigger
# a system query.
refresh_interval = timedelta(minutes=1)

system_names = { "summit": "IBM AC922",
                 "hpss": "High Performance Storage System",
                 "andes": "Data Analysis System",
                 "frontier": "Cray EX 235a",
               }

async def update_status():
    global last_status_query
    t = datetime.now(tz=timezone.utc)
    if t - last_status_query < refresh_interval:
        return

    last_status_query = t
    # TODO: query sinfo for queue status
    
    for m, full_name in system_names.items():
        stat = StatusValue.active
            #unavailable
            #degraded
            #other
        current_status[m] = SystemStatus(
                name = m,
                full_name = full_name,
                description = None,
                system_type = None,
                notes = None,
                status = stat,
                updated_at = last_status_query,
            )

def parse_time(s) -> Optional[datetime]:
    if len(s) == 0:
        return None
    tzinfo = None
    # need to remove trailing 'Z' for python < 3.11
    if s[-1] == 'Z':
        tzinfo = timezone.utc
        s = s[:-1]
    t = datetime.fromisoformat(s)
    if tzinfo is not None:
        t = t.replace(tzinfo=tzinfo)
    # Convert all timezones to utc internally.
    return t.astimezone(tz=timezone.utc)

async def update_outages():
    global current_outages
    global last_outage_query
    t = datetime.now(tz=timezone.utc)
    if t - last_outage_query < refresh_interval:
        return

    # TODO: query showres for planned outages
    # (alternative to OLCF status web-API).
    last_outage_query = t
    outs = await get_json("https://www.olcf.ornl.gov/wp-content/themes/olcf-edition-child/get-downtimes.php")
    if outs is None:
        _logger.error("Error fetching OLCF status web-API")
        return
    if 'data' not in outs:
        _logger.error("Invalid response from OLCF status web-API")
        return
    _logger.info("Received response from OLCF status web-API:", outs['data'])

    current_outages = dict((m,[]) for m in system_names.keys())
    for out in outs['data']:
        if (  'system_name' not in out
           or 'downtime' not in out
           or 'uptime' not in out ):
               _logger.error("Invalid response from OLCF status web-API")
               continue
        info = Outage(name        = str(out['system_name']),
                      start_at    = parse_time(out['downtime']),
                      end_at      = parse_time(out['uptime']),
                      description = out.get('description', None),
                      notes       = None,
                      status      = None,
                      swo         = None,
                      update_at   = t,
                     )
        if info.name not in outages:
            current_outages[info.name] = []
        current_outages[info.name].append( info )

@status.get("/")
async def get_status() -> List[SystemStatus]:
    await update_status()
    return [stat for m, stat in current_status.items()]

@status.get("/status/{name}")
async def read_status(name: str) -> SystemStatus:
    await update_status()
    if name not in current_status:
        raise HTTPException(status_code=404, detail="Item not found")
    return current_status[name]

@status.get("/notes")
async def get_notes() -> List[List[Note]]:
    return []

@status.get("/notes/{name}")
async def read_note(name: str) -> List[Note]:
    raise HTTPException(status_code=404, detail="Item not found")

@status.get("/outages")
async def get_outages() -> List[List[Outage]]:
    await update_outages()
    return [ out for m, out in current_outages.items() ]

@status.get("/outages/{name}")
async def read_outage(name: str) -> List[Outage]:
    await update_outages()
    if name not in current_outages:
        raise HTTPException(status_code=404, detail="Item not found")
    return current_outages[name]

@status.get("/outages/planned")
async def get_planned_outages() -> List[List[Outage]]:
    await update_outages()
    now = datetime.now(tz=timezone.utc)
    return [ [o for o in out if o.start_at > now] \
             for m, out in current_outages.items() ]

@status.get("/outages/planned/{name}")
async def read_planned_outage(name: str) -> List[Outage]:
    await update_outages()
    now = datetime.now(tz=timezone.utc)
    if name not in current_outages:
        raise HTTPException(status_code=404, detail="Item not found")
    return [o for o in current_outages[name] if o.start_at > now]

#@status.put(
#    "/{item_id}",
#    tags=["custom"],
#    responses={403: {"description": "Operation forbidden"}},
#)

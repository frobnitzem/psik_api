from enum import Enum
from typing import Dict, List, Optional
from datetime import date as date_, datetime, timezone, timedelta
import logging
_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from .queries import get_http, fetch_current_status
from .models import PublicHost

# TODO: output dates in local (EST/EDT) timezone rather than UTC

# Data models specific to status routes:
class StatusValue(str, Enum):
    active = "active"
    unavailable = "unavailable"
    degraded = "degraded"
    other = "other"

class SystemStatus(BaseModel):
    name: str = Field(..., title="System Name")
    full_name: Optional[str] = Field(None, title="Full System Name")
    description: Optional[str] = Field(None, title="Description")
    system_type: Optional[str] = Field(None, title="System Type")
    notes: Optional[List[str]] = Field(None, title="Status Notes")
    status: StatusValue
    updated_at: Optional[datetime] = Field(None, title="Updated At")

class Note(BaseModel):
    name: str = Field(..., title="System Name")
    notes: Optional[str] = Field(None, title="Notes")
    active: Optional[bool] = Field(False, title="Active")
    timestamp: Optional[datetime] = Field(None, title="Timestamp")

class Outage(BaseModel):
    name: str = Field(..., title="Name")
    start_at: Optional[datetime] = Field(None, title="Start At")
    end_at: Optional[datetime] = Field(None, title="End At")
    description: Optional[str] = Field(None, title="Description") # Scheduled Maintenance, System Degraded, Unavailable
    notes: Optional[str] = Field(None, title="Notes") # why/what's up
    status: Optional[str] = Field(None, title="Status") # Completed/Planned/Cancelled/Active
    swo: Optional[str] = Field(None, title="Will system be off? degr, true, or fals")
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
system_types = { "summit": "compute",
                 "hpss": "filesystem",
                 "andes": "compute",
                 "frontier": "compute",
               }

async def update_status():
    global last_status_query
    t = datetime.now(tz=timezone.utc)
    if t - last_status_query < refresh_interval:
        return

    last_status_query = t
    # TODO: query sinfo for queue status instead
    stat = await fetch_current_status()
    
    for m, full_name in system_names.items():
        status = StatusValue.other
        notes = [ "no information" ]
        if m in stat:
            val, since = stat[m]
            if val == 'status-up':
                status = StatusValue.active
                notes = [since]
            elif val == 'status-down':
                status = StatusValue.unavailable
                notes = [since]
            else:
                status = StatusValue.other
                notes = [ stat[m], since ]
            #unavailable
            #degraded
            #other
        current_status[m] = SystemStatus(
                name = m,
                full_name = full_name,
                description = f"System is {status.value}",
                system_type = system_types.get(m, None),
                notes = notes,
                status = status,
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

# Example API Return Result:
# {"type":"downtimes",
#  "id":19084,
#  "system_name":"hpss",
#  "downtime":"2023-09-05T08:00:00-04:00",
#  "uptime":"2023-09-05T20:00:00-04:00",
#  "description":"File system software interrupt",
#  "user_impact":"",
#  "details":"HPSS outage to replace DDN hpss-ddn1a chassis to remedy internal power redundancy issue. We will also perform a PMI on the tape library at this time.",
#  "scheduled":true,
#  "reboot":true,
#  "reportable":true,
#  "displayable":false,
#  "hardware":true,
#  "software":true,
#  "other":false,
#  "ticket_url":"",
#  "updated_at":"2023-08-29T13:50:25-04:00"}
async def update_outages():
    global current_outages
    global last_outage_query
    t = datetime.now(tz=timezone.utc)
    if t - last_outage_query < refresh_interval:
        return

    # TODO: query showres for planned outages
    # (alternative to OLCF status web-API).
    last_outage_query = t
    outs = await get_http("https://www.olcf.ornl.gov/wp-content/themes/olcf-edition-child/get-downtimes.php", json=True)
    if outs is None:
        _logger.error("Error fetching OLCF outage web-API")
        return
    if 'data' not in outs:
        _logger.error("Invalid response from OLCF outage web-API")
        return
    _logger.info("Received response from OLCF outage web-API:", outs['data'])

    current_outages = dict((m,[]) for m in system_names.keys())
    for out in outs['data']:
        if (  'system_name' not in out
           or 'downtime' not in out
           or 'uptime' not in out ):
               _logger.error("Invalid response from OLCF outage web-API")
               continue

        upd = t
        if "updated_at" in out:
            upd = parse_time(out["updated_at"])
        info = Outage(name        = str(out['system_name']),
                      start_at    = parse_time(out['downtime']),
                      end_at      = parse_time(out['uptime']),
                      description = out.get("description",
                                            "Scheduled Maintenance"),
                      notes       = out.get("details", None),
                      status      = "Planned",
                      swo         = "true",
                      update_at   = upd,
                     )
        if info.name not in current_outages:
            current_outages[info.name] = []
        current_outages[info.name].append( info )

@status.get("/")
async def get_status(name : Optional[PublicHost] = None) -> List[SystemStatus]:
    "Read system status information"
    await update_status()

    if name is None:
        return [stat for m, stat in current_status.items()]
    elif name not in current_status:
        raise HTTPException(status_code=404, detail="Item not found")
    return [current_status[name]]

#@status.get("/notes")
#async def get_notes() -> List[List[Note]]:
#    "Read all status notes"
#    return []
#
#@status.get("/notes/{name}")
#async def read_note(name: str) -> List[Note]:
#    "Read all notes pertaining to one system"
#    raise HTTPException(status_code=404, detail="Item not found")

@status.get("/outages")
async def get_outages(name: Optional[PublicHost] = None) -> List[Outage]:
    "Read Outage information."
    await update_outages()
    if name is None:
        outs : List[Outage] = []
        for m, out in current_outages.items():
            if len(out) > 0:
                outs.extend(out)
        return outs
    if name not in current_outages:
        raise HTTPException(status_code=404, detail="Item not found")
    return current_outages[name]

@status.get("/outages/planned")
async def get_planned_outages(name: Optional[PublicHost] = None
                             ) -> List[Outage]:
    "Read planned Outages."
    await update_outages()
    now = datetime.now(tz=timezone.utc)
    if name is None:
        outs : List[Outage] = []
        for m, out in current_outages.items():
            outs.extend( [o for o in out if is_after(o.start_at, now)] )
        return outs
    if name not in current_outages:
        raise HTTPException(status_code=404, detail="Item not found")
    return [o for o in current_outages[name] if is_after(o.start_at, now)]

def is_after(a : Optional[datetime], b : datetime) -> bool:
    if a is None:
        return False
    return a > b

#@status.put(
#    "/{item_id}",
#    tags=["custom"],
#    responses={403: {"description": "Operation forbidden"}},
#)

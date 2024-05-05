from enum import Enum
from typing import Dict, List, Optional
from datetime import date as date_, datetime, timezone, timedelta
import logging
_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

import psik

from .config import managers
from .models import ErrorStatus, stamp_re

callback = APIRouter()

@callback.post("/{machine}/{jobid}")
async def do_callback(machine : str, jobid : str, cb : psik.Callback) -> ErrorStatus:
    "Notify psik_api that a job has reached a given state."

    if not stamp_re.match(jobid):
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        mgr = managers[machine]
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")

    base = mgr.prefix / jobid
    if not base.is_dir():
        raise HTTPException(status_code=404, detail="Item not found")

    job = psik.Job(base)
    ok = await job.reached(cb.jobndx, cb.state, cb.info)
    if ok:
        return ErrorStatus.OK
    return ErrorStatus.ERROR

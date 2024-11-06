from typing import Optional, List, Dict
from typing_extensions import Annotated
from pathlib import Path
import logging
_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from fastapi import (
    APIRouter,
    HTTPException,
    Form,
    Query,
    File,
    BackgroundTasks,
)
import psik

from ..internal.tasks import submit_job
from ..models import JobStepInfo, stamp_re
from ..config import get_manager

## Potential response
#class ValidationError(BaseModel):
#    loc: List[str] = Field(..., title="Location")
#    msg: str = Field(..., title="Message")
#   xtype: str = Field(..., title="Error Type")

#@app.post("/login/")
#async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
#    return {"username": username}


jobs = APIRouter(responses={
        401: {"description": "Unauthorized"}})

KeyVals = Annotated[str, Query(pattern=r"^[^=]+=[^=]+$")]

def get_mgr(backend: Optional[str] = None) -> psik.JobManager:
    try:
        mgr = get_manager(backend)
    except KeyError:
        raise HTTPException(status_code=404, detail="Backend not found")
    return mgr

async def get_job(jobid: str, backend: Optional[str] = None) -> Path:
    if not stamp_re.match(jobid):
        raise HTTPException(status_code=400, detail="Invalid jobid")
    try:
        mgr = get_manager(backend)
    except KeyError:
        raise HTTPException(status_code=404, detail="Invalid backend")

    base = mgr.prefix / jobid
    if not await base.is_dir():
        raise HTTPException(status_code=404, detail="Job not found")
    return Path(base)

@jobs.get("")
@jobs.get("/")
async def get_jobs(index: int = 0,
                   limit: Optional[int] = None,
                   backend: Optional[str] = None,
                   state: Optional[psik.JobState] = None,
                  ) -> List[JobStepInfo]:
    """
    Get information about jobs running on compute resources.

      - index: the index of the last job info to retrieve
               Jobs are sorted by time, so index 0 is the most recent job.
      - limit: (optional) how many JobStepInfo-s to retrieve
      - backend: (optional) the compute resource name
      - state: (optional) filter by job state
    """

    # TODO: use a real db query here.
    mgr = get_mgr(backend)

    out = []
    async for job in mgr.ls():
        t, ndx, jstate, info = job.history[-1]
        if state is not None and jstate != state:
            continue
        out.append(JobStepInfo(
                    jobid = job.stamp,
                    name = job.spec.name or '',
                    updated = t,
                    jobndx = ndx,
                    state = jstate,
                    info = info))
    out.sort(key = lambda x: -float(x.jobid))
    if index is not None and index > 0:
        if index >= len(out):
            out = []
        else:
            out = out[index:]
    if limit is not None:
        out = out[:limit]
    return out

@jobs.post("")
@jobs.post("/")
async def post_job(job: psik.JobSpec,
                   bg_tasks: BackgroundTasks,
                   backend: Optional[str] = None,
                  ) -> str:
    """
    Submit a job to run on a compute resource.

      - backend: (optional) specific backend to receive the job

    If successful this api will return the jobid created.
    """
    mgr = get_mgr(backend)
    return await submit_job(mgr, job, bg_tasks)

@jobs.post("/{jobid}/start")
async def start_job(jobid: str,
                    bg_tasks: BackgroundTasks,
                    backend: Optional[str] = None
                   ) -> None:
    pre = await get_job(jobid, backend)
    job = psik.Job(pre)
    bg_tasks.add_task(job.submit)
    return

@jobs.get("/{jobid}")
async def read_job(jobid: str,
                   backend: Optional[str] = None) -> List[JobStepInfo]:
    """Read job
      - jobid: the job's ID string
      - backend: (optional) the job's backend
    """
    pre = await get_job(jobid, backend)
    try:
        job = await psik.Job(pre)
    except Exception:
        raise HTTPException(status_code=500, detail="Error reading job")

    out = []
    for t, ndx, state, info in job.history:
        out.append(JobStepInfo(
                    jobid = job.stamp,
                    name = job.spec.name or '',
                    updated = t,
                    jobndx = ndx,
                    state = state,
                    info = info))
    return out

@jobs.delete("/{jobid}")
async def delete_job(jobid   : str,
                     bg_tasks: BackgroundTasks,
                     backend : Optional[str] = None) -> None:
    # Cancel job
    pre = await get_job(jobid, backend)
    try:
        job = await psik.Job(pre)
    except Exception:
        raise HTTPException(status_code=500, detail="Error reading job")
    bg_tasks.add_task(job.cancel)
    return

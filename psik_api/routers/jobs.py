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

async def get_job(jobid: str) -> Path:
    if not stamp_re.match(jobid):
        raise HTTPException(status_code=400, detail="Invalid jobid")
    mgr = get_manager()

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

    mgr = get_manager()

    out = []
    async for job in mgr.ls():
        if backend and job.spec.backend != backend:
            # filter out jobs from other backends
            continue
        trs = job.history[-1]
        if state is not None and trs.state != state:
            continue
        out.append(JobStepInfo(
                    jobid = job.stamp,
                    name = job.spec.name or '',
                    updated = trs.time,
                    jobndx = trs.jobndx,
                    state = trs.state,
                    info = trs.info))
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
                   bg_tasks: BackgroundTasks
                  ) -> str:
    """
    Submit a job to run on a compute resource.

    If successful this api will return the jobid created.
    """
    mgr = get_manager()
    return await submit_job(mgr, job, bg_tasks)

@jobs.post("/{jobid}/start")
async def start_job(jobid: str,
                    bg_tasks: BackgroundTasks
                   ) -> None:
    pre = await get_job(jobid)
    job = psik.Job(pre)
    bg_tasks.add_task(job.submit)
    return

@jobs.get("/{jobid}")
async def read_job(jobid: str) -> List[JobStepInfo]:
    """Read job
      - jobid: the job's ID string
    """
    pre = await get_job(jobid)
    try:
        job = await psik.Job(pre)
    except Exception:
        raise HTTPException(status_code=500, detail="Error reading job")

    out = []
    for trs in job.history:
        out.append(JobStepInfo(
                    jobid = job.stamp,
                    name = job.spec.name or '',
                    updated = trs.time,
                    jobndx = trs.jobndx,
                    state = trs.state,
                    info = trs.info))
    return out

@jobs.delete("/{jobid}")
async def delete_job(jobid   : str,
                     bg_tasks: BackgroundTasks) -> None:
    # Cancel job
    pre = await get_job(jobid)
    try:
        job = await psik.Job(pre)
    except Exception:
        raise HTTPException(status_code=500, detail="Error reading job")
    bg_tasks.add_task(job.cancel)
    return

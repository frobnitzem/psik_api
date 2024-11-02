from typing import Optional, List, Dict
from typing_extensions import Annotated
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
from pathlib import Path

from .tasks import submit_job
from .models import JobStepInfo, stamp_re
from .config import get_manager

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

def get_mgr(machine: str) -> psik.JobManager:
    try:
        mgr = get_manager(machine)
    except KeyError:
        raise HTTPException(status_code=404, detail="Backend machine not found")
    return mgr

async def get_job(machine: str, jobid: str) -> Path:
    if not stamp_re.match(jobid):
        raise HTTPException(status_code=400, detail="Invalid jobid")
    mgr = get_mgr(machine)
    base = mgr.prefix / jobid
    if not await base.is_dir():
        raise HTTPException(status_code=404, detail="Job not found")
    return Path(base)

@jobs.get("/{machine}")
async def get_jobs(machine: str,
                   index: int = 0,
                   limit: Optional[int] = None,
                   kwargs: Annotated[List[KeyVals], Query()] = []) -> List[JobStepInfo]:
    """
    Get information about jobs running on compute resources.

      - machine: the compute resource name
      - index: the index of the first job info to retrieve
      - limit: (optional) how many job infos to retrieve
      - kwargs: (optional) a list of key/value pairs (in the form of name=value) to filter job results by
    """

    mgr = get_mgr(machine)

    out = []
    async for job in mgr.ls():
        t, ndx, state, info = job.history[-1]
        out.append(JobStepInfo(
                    jobid = job.stamp,
                    name = job.spec.name or '',
                    updated = t,
                    jobndx = ndx,
                    state = state,
                    info = info))
    return out

@jobs.post("/{machine}")
async def post_job(machine: str,
                   job: psik.JobSpec,
                   bg_tasks: BackgroundTasks) -> str:
    """
    Submit a job to run on a compute resource.

      - machine: the machine to run the job on.

    If successful this api will return the jobid created.
    """
    mgr = get_mgr(machine)
    return await submit_job(mgr, job, bg_tasks)

# TODO: allow population of a job directory with
# files (https://fastapi.tiangolo.com/reference/uploadfile/)
# (posted as multipart form-data)
#
#@jobs.post("/{machine}/new")
#async def create_with_files(files: list[UploadFile] = File(...)):
#    for file in files:
#        images.append({
#            "filename": file.filename,
#            "bytes": str(await file.read(10))
#        })
#    return await create_job()

@jobs.get("/{machine}/{jobid}")
async def read_job(machine : str,
                   jobid   : str) -> List[JobStepInfo]:
    # Read job
    pre = await get_job(machine, jobid)
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

@jobs.delete("/{machine}/{jobid}")
async def delete_job(machine : str,
                     jobid   : str,
                     bg_tasks: BackgroundTasks) -> None:
    # Cancel job
    pre = await get_job(machine, jobid)
    try:
        job = await psik.Job(pre)
    except Exception:
        raise HTTPException(status_code=500, detail="Error reading job")
    bg_tasks.add_task(job.cancel)
    return

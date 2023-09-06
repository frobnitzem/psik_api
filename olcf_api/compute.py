from typing import Optional, List, Dict
from typing_extensions import Annotated
import re
import logging
_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Form, Query
import psik

from .tasks import task_list, PostTaskResult
from .models import ErrorStatus, PublicHost
from .jobs import managers

class JobOutput(BaseModel):
    status: ErrorStatus
    output: List[Dict[str, str]] = Field(..., title="Output")
    error: Optional[str] = Field(None, title="Error")

class QueueOutput(BaseModel):
    status: ErrorStatus
    output: List[Dict[str, str]] = Field(..., title="Output")
    error: Optional[str] = Field(None, title="Error")

## Potential response
#class ValidationError(BaseModel):
#    loc: List[str] = Field(..., title="Location")
#    msg: str = Field(..., title="Message")
#    type: str = Field(..., title="Error Type")

#@app.post("/login/")
#async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
#    return {"username": username}


compute = APIRouter(responses={
        401: {"description": "Unauthorized"}})

KeyVals = Annotated[str, Query(pattern=r"^[^=]+=[^=]+$")]

@compute.get("/jobs/{machine}")
async def get_jobs(machine : PublicHost,
                   index : int = 0,
                   limit : Optional[int] = None,
                   kwargs : Annotated[List[KeyVals], Query()] = []) -> QueueOutput:
    """
    Get information about jobs running on compute resources.

      - machine: the compute resource name
      - index: the index of the first job info to retrieve
      - limit: (optional) how many job infos to retrieve
      - kwargs: (optional) a list of key/value pairs (in the form of name=value) to filter job results by
    """

    try:
        mgr = managers[machine.value]
    except :
        raise HTTPException(status_code=404, detail="Item not found")

    out = []
    async for job in mgr.ls():
        t, ndx, state, info = job.history[-1]
        out.append({'stamp': job.stamp,
                    'name': job.spec.name or '',
                    'updated': str(t),
                    'jobndx': str(ndx),
                    'state': state.value,
                    'info': str(info)})
    return QueueOutput(status=ErrorStatus.OK, output=out, error=None)

@compute.post("/jobs/{machine}")
async def post_job(machine : PublicHost, job : psik.JobSpec) -> PostTaskResult:
    """
    Submit a job to run on a compute resource.

      - machine: the machine to run the job on.

    If successful this api will return a task_id which you can
    look up via the /tasks api. Once the job has been scheduled,
    the task body will contain the job id.
    """

    return await task_list.submit_job(machine.value, job)

@compute.get("/jobs/{machine}/{jobid}")
async def read_job(machine : PublicHost,
                   jobid   : str) -> JobOutput:
    # Read job
    try:
        mgr = managers[machine.value]
    except :
        raise HTTPException(status_code=404, detail="Item not found")

    # TODO: document this
    if not re.match(r'[0-9]+\.[0-9]*', jobid):
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        job = await psik.Job(mgr.prefix / jobid)
    except Exception:
        raise HTTPException(status_code=404, detail="Item not found")

    out = []
    for t, ndx, state, info in job.history:
        out.append({'stamp': job.stamp,
                    'name': job.spec.name or '',
                    'updated': str(t),
                    'jobndx': str(ndx),
                    'state': state.value,
                    'info': str(info)})
    return QueueOutput(status=ErrorStatus.OK, output=out, error=None)

@compute.delete("/jobs/{machine}/{jobid}")
async def delete_job(machine : PublicHost,
                     jobid   : str) -> PostTaskResult:
    # Cancel job
    try:
        mgr = managers[machine.value]
    except :
        raise HTTPException(status_code=404, detail="Item not found")

    # TODO: document this
    if not re.match(r'[0-9]+\.[0-9]*', jobid):
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        job = await psik.Job(mgr.prefix / jobid)
    except Exception:
        raise HTTPException(status_code=404, detail="Item not found")
    return await task_list.cancel_job(job)

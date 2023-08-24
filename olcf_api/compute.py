from typing import Optional, List, Dict
from typing_extensions import Annotated
import logging
_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Form, Query

from .tasks import task_list, PostTaskResult
from .models import ErrorStatus

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
async def get_jobs(machine : str,
                   index : int = 0,
                   limit : Optional[int] = None,
                   sacct : bool = False,
                   kwargs : Annotated[List[KeyVals], Query()] = []) -> QueueOutput:
    """
    Get information about jobs running on compute resources.

      - machine: the compute resource name
      - index: the index of the first job info to retrieve
      - limit: (optional) how many job infos to retrieve
      - sacct: (optional) if true, use sacct otherwise squeue to get the job info
      - kwargs: (optional) a list of key/value pairs (in the form of name=value) to filter job results by
    """

    return QueueOutput(status=ErrorStatus.OK, output=[], error=None)

@compute.post("/jobs/{machine}")
async def post_job(machine : str,
             isPath : Annotated[bool, Form()],
             job : Annotated[str, Form()],
             args : Annotated[List[str], Form()] = []) -> PostTaskResult:
    """
    Submit a job to run on a compute resource.

      - machine: the machine to run the job on.
      - job: either a path to the job script, or the job script itself
      - isPath: if true, the job parameter is a path
      - args: (Optional) if isPath is true, you can specify command line arguments here (note that this swagger ui will concatenate your args into a single value. Instead your should submit with multiple &arg=<value>-s.)

    If successful this api will return a task_id which you can look up via the /tasks api. Once the job has been scheduled, the task body will contain the job id.
    """

    return await task_list.submit_job(machine, isPath, job, args)

@compute.get("/jobs/{machine}/{jobid}")
async def read_job(machine : str,
                   jobid : int,
                   sacct : bool = False) -> JobOutput:
    # Read job
    raise HTTPException(status_code=404, detail="Item not found")

@compute.delete("/jobs/{machine}/{jobid}")
async def delete_job(machine : str,
                     jobid : int) -> PostTaskResult:
    # Cancel job
    raise HTTPException(status_code=404, detail="Item not found")
    return await task_list.cancel_job(machine, jobid)

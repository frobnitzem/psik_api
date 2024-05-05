from typing import Optional, List, Dict, Any, Awaitable
from datetime import timedelta
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict
import psik

from .models import ErrorStatus
from .config import managers

class Task(BaseModel):
    id: int = Field(title="Task id")
    status: str = Field(title="Status")
    result: Optional[str] = Field(default=None, title="Result")

class Tasks(BaseModel):
    tasks: List[Task] = Field(default=[], title="Tasks")

class PostTaskResult(BaseModel):
    task_id: int = Field(title="Task Id")
    status: ErrorStatus
    error: Optional[str] = Field(default=None, title="Error")

class TaskInfo(Task):
    underlying : Awaitable
    task       : Optional[asyncio.Task] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def start(self, name=None):
        self.task = asyncio.create_task(self.auto_update(), name=name)

    async def auto_update(self):
        """ Wrap the task in this function to
            automatically update self info.
        """
        try:
            ret = str(await self.underlying)
            self.status = "completed"
        except asyncio.CancelledError as e:
            self.status = "canceled"
        except Exception as e:
            ret = str(e)
            self.status = "failed"
        self.result = ret

    def cancel(self):
        self.underlying.cancel()

class TaskList(dict[int,TaskInfo]):
    # Internal task list used for tracking all server tasks.
    # Note that this should be separated in a per-user basis
    # for production (so that a user only sees their own tasks).
    #
    # Also note that tasks are equivalent to jobs in the current
    # implementation.
    #
    def __init__(self):
        super().__init__()

        self.taskid = 0 # internal job ID to assign to next task

    def append(self, task : Awaitable, name : Optional[str] = None) -> int:
        """ Append the task to the current task set.
        """
        self.taskid += 1
        t = TaskInfo(id=self.taskid, status="active", underlying=task)
        t.start(name)
        self[self.taskid] = t
        return self.taskid

    async def submit_job(self, machine : str,
                         spec : psik.JobSpec) -> PostTaskResult:
        if machine not in managers:
            return PostTaskResult(task_id = -1,
                          status = ErrorStatus.ERROR,
                          error = f"Unable to submit jobs to {machine}")

        task = self.append(_submit_job(managers[machine], spec), spec.name)
        return PostTaskResult(task_id = task,
                              status = ErrorStatus.OK)
    async def cancel_job(self, job : psik.Job) -> PostTaskResult:
        # Note: race condition if the user somehow guesses the jobid
        # and cancels the job while being created (unlikely).
        task = self.append(job.cancel(), job.spec.name)
        return PostTaskResult(task_id = task,
                              status = ErrorStatus.OK)

async def _submit_job(mgr : psik.JobManager, spec : psik.JobSpec):
    """ Async coroutine to create and submit the jobspec through Psi_k.
    """
    job = await mgr.create(spec)
    await job.submit()
    return job.stamp

# Create a tracker for tasks in-progress.
task_list = TaskList()

#tasks = APIRouter(responses={
#        401: {"description": "Unauthorized"},
#        403: {"description": "Forbidden"}})
tasks = APIRouter()

@tasks.get("/")
def get_tasks() -> Tasks:
    return Tasks(tasks = [v for k,v in task_list.items()])

@tasks.get("/{id}")
def read_task(id : int) -> Task:
    if id not in task_list:
        raise HTTPException(status_code=404, detail="Item not found")
    return task_list[id]

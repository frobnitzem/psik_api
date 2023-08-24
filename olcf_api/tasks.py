from typing import Optional, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .models import ErrorStatus

class Task(BaseModel):
    id: str = Field(..., title="Id")
    status: str = Field(..., title="Status")
    result: Optional[str] = Field(None, title="Result")

class Tasks(BaseModel):
    tasks: List[Task] = Field([], title="Tasks")

class PostTaskResult(BaseModel):
    task_id: str = Field(..., title="Task Id")
    status: ErrorStatus
    error: Optional[str] = Field(None, title="Error")

# Internal task list used for tracking all server tasks.
# Note that this should be separated in a per-user basis
# for production (so that a user only sees their own tasks).
class TaskList(dict):
    async def submit_job(self, machine : str,
                   isPath : bool,
                   job : str,
                   args : List[str]):
        return PostTaskResult(task_id = "",
                              status = ErrorStatus.ERROR,
                              error = "not implemented")

# Create a tracker for tasks in-progress.
task_list = TaskList()

tasks = APIRouter(responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}})

@tasks.get("/")
def get_tasks() -> Tasks:
    return Tasks(tasks = [v for k,v in task_list.items()])

@tasks.get("/{id}")
def read_task(id : str) -> Task:
    if id not in task_list:
        raise HTTPException(status_code=404, detail="Item not found")
    return task_list[id]

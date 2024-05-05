# Data models shared by many components:
from enum import Enum
import re

from pydantic import BaseModel, Field
from psik import JobState

stamp_re = re.compile(r'[0-9]+\.[0-9]*')

# DMR: why not make this a bool?
class ErrorStatus(str, Enum):
    OK = "OK"
    ERROR = "ERROR"

class JobStepInfo(BaseModel):
    jobid   : str
    name    : str
    updated : float
    jobndx  : int
    state   : JobState
    info    : int

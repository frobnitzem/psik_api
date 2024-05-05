# Data models shared by many components:
from enum import Enum

from pydantic import BaseModel, Field

# DMR: why not make this a bool?
class ErrorStatus(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


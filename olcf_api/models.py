# Data models shared by many components:
from enum import Enum

from pydantic import BaseModel, Field

class PublicHost(str, Enum):
    cori = "cori"
    dtn01 = "dtn01"
    perlmutter = "perlmutter"
    summit = "summit"
    andes = "andes"
    hpss = "hpss"
    frontier = "frontier"

# DMR: why not make this a bool?
class ErrorStatus(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


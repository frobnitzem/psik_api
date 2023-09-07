# Data models shared by many components:
from enum import Enum

from pydantic import BaseModel, Field

class PublicHost(str, Enum):
    andes = "andes"
    cori = "cori"
    dtn01 = "dtn01"
    frontier = "frontier"
    hpss = "hpss"
    localhost = "localhost"
    perlmutter = "perlmutter"
    summit = "summit"

# DMR: why not make this a bool?
class ErrorStatus(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


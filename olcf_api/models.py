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


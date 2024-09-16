from fastapi import Depends, FastAPI
from typing import Any
from importlib.metadata import version
__version__ = version(__package__)

#from .dependencies import get_token_header
from .status import status
from .compute import compute
from .tasks import tasks
from .callback import callback
from .outputs import outputs

# TODO: @cache a config-file here.

description = """
A network interface to resources provided through psik.
"""

tags_metadata : list[dict[str, Any]] = [
    {
        "name": "status",
        "description": "psik backend status info.",
    },
    {
        "name": "compute",
        "description": "Run commands and manage batch jobs on configured compute resources.",
    },
    {
        "name": "tasks",
        "description": "Get information about tasks you are running within the API.",
    },
    {
        "name": "callback",
        "description": "Callbacks used by tasks to update their status.",
    },
    {
        "name": "outputs",
        "description": "Access compute job outputs.",
    },
    {
        "name": "inputs",
        "description": "Setup compute job inputs.",
    },
]

api = FastAPI(
        title = "psik API",
        openapi_url   = "/openapi.json",
        #root_path     = api_version_prefix,
        docs_url      = "/",
        description   = description,
        #summary      = "A fancy re-packaging of command-line tools.",
        #version       = version_tag,
        #terms_of_service="You're on your own here.",
        #contact={
        #    "name": "",
        #    "url": "",
        #    "email": "help@psik.local",
        #},
        openapi_tags  = tags_metadata,
        responses     = {404: {"description": "Not found"}},
    )

api.include_router(
    status,
    prefix="/status",
    tags = ["status"],
)
api.include_router(
    compute,
    prefix="/compute",
    tags = ["compute"],
)
api.include_router(
    tasks,
    prefix="/tasks",
    tags = ["tasks"],
)
api.include_router(
    outputs,
    prefix="/outputs",
    tags = ["outputs"],
)
api.include_router(
    callback,
    prefix="/callback",
    tags = ["callback"],
)

app = api
try:
    from certified.formatter import log_request
    app.middleware("http")(log_request)
except ImportError:
    pass

#app = FastAPI()
#app.mount("/api", api)

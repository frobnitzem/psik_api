from fastapi import Depends, FastAPI
from typing import Any
from importlib.metadata import version
__version__ = version(__package__)

#from .dependencies import get_token_header
from .routers.backends import backends
from .routers.jobs import jobs

# TODO: @cache a config-file here.

description = """
A network interface to resources provided through psik.
"""

tags_metadata : list[dict[str, Any]] = [
    {
        "name": "backends",
        "description": "psik backend information (e.g. status)",
    },
    {
        "name": "jobs",
        "description": "Manage jobs on configured compute backends.",
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
    backends,
    prefix="/backends",
    tags = ["backends"],
)
api.include_router(
    jobs,
    prefix="/jobs",
    tags = ["jobs"],
)

app = api
try:
    from certified.formatter import log_request # type: ignore[import-not-found]
    app.middleware("http")(log_request)
except ImportError:
    pass

#app = FastAPI()
#app.mount("/api", api)

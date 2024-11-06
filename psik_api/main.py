from contextlib import asynccontextmanager
import logging
from typing import Any, Dict, List
from importlib.metadata import version
_logger = logging.getLogger(__name__)
__version__ = version(__package__)

from fastapi import Depends, FastAPI, Request

from .config import load_config
from .dependencies import setup_security, create_token, Authz
from .routers.backends import backends
from .routers.jobs import jobs

# TODO: @cache a config-file here.

description = """
A network interface to resources provided through psik.
"""

tags_metadata : List[Dict[str, Any]] = [
    {
        "name": "backends",
        "description": "psik backend information (e.g. status)",
    },
    {
        "name": "jobs",
        "description": "Manage jobs on configured compute backends.",
    },
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    _logger.debug("Starting lifespan.")
    config = load_config()
    # Setup activities
    setup_security(config.authz)
    yield
    # Teardown activities

api = FastAPI(
        title = "psik API",
        lifespan = lifespan,
        openapi_url   = "/openapi.json",
        #root_path     = api_version_prefix,
        docs_url      = "/",
        description   = description,
        summary      = "A web-interface to the psik command-line tool, with user management and a database backend.",
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
    dependencies=[Authz],
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

@app.get("/token")
async def get_token(r: Request):
    return create_token(r)

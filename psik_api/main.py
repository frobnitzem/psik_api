from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
import logging
from importlib.metadata import version
_logger = logging.getLogger(__name__)
version_tag = version(__package__)

from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import PlainTextResponse

from .config import load_config
from .dependencies import setup_security, create_token, Authz, token_scheme
from .routers.backends import backends
from .routers.jobs import jobs

# TODO: @cache a config-file here.

description = """
Stop fussing with SLURM and shell background tasks.
Setup, start, and monitor the progress of your batch
jobs using modern, secure, REST-API routes and callbacks.
"""

tags_metadata : List[Dict[str, Any]] = [
    { "name": "backends",
      "description": "psik backend information (e.g. status)",
    },
    { "name": "jobs",
      "description": "Manage jobs on configured compute backends.",
    },
    { "name": "auth",
      "description": "Create authorization tokens.",
    },
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    _logger.info("Starting lifespan.")
    config = load_config()
    # Setup activities
    setup_security(config.authz)
    yield
    # Teardown activities

api = FastAPI(
        title = "psik API",
        lifespan = lifespan,
        openapi_url   = "/openapi.json",
        root_path     = "/v2",
        docs_url      = "/",
        description   = description,
        summary      = "An API for batch jobs and their files",
        version       = version_tag,
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

@api.get("/token", tags=["auth"], response_class=PlainTextResponse)
async def get_token(r: Request):
    return create_token(r)

from biscuit_auth import UnverifiedBiscuit, BiscuitValidationError

@api.post("/token", tags=["auth"])
async def show_token(credentials: Annotated[
                      Optional[HTTPAuthorizationCredentials],
                      Depends(token_scheme)] = None):
    if credentials is None:
        raise HTTPException(status_code=401,
                                detail='required header Authorization: bearer b64-token')
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401,
                                detail='header format should be Authorization: bearer b64-token')
    biscuit = credentials.credentials

    try:
        x = UnverifiedBiscuit.from_base64(biscuit)
    except BiscuitValidationError as e:
        return {"BiscuitValidationError": str(e)}
    return {"blocks": [
        x.block_source(i) for i in range(x.block_count())
    ]}

#app = api
app = FastAPI(lifespan = lifespan)
app.mount("/v2", api)

try:
    from certified.formatter import log_request # type: ignore[import-not-found]
    app.middleware("http")(log_request)
except ImportError:
    pass

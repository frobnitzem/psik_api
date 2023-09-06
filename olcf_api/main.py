from fastapi import Depends, FastAPI
from importlib.metadata import version
__version__ = version(__package__)

from .dependencies import get_token_header
from .status import status
from .compute import compute
from .tasks import tasks

version_tag = __version__.rsplit(".", 1)[0]
api_version_prefix = "/api/v" + version_tag

description = """
A programmatic way to access resources at OLCF.
"""

tags_metadata = [
    {
        "name": "status",
        "description": "OLCF component system health.",
    },
    {
        "name": "compute",
        "description": "Run commands and manage batch jobs on OLCF compute resources.",
        "externalDocs": {
            "description": "OLCF System Documentation",
            "url": "https://docs.olcf.ornl.gov/systems/index.html",
        },
    },
    {
        "name": "tasks",
        "description": "Get information about tasks you are running on the API server.",
    },
]

api = FastAPI(
        title="OLCF SuperFacility API",
        openapi_url   = "/openapi.json",
        #root_path     = api_version_prefix,
        docs_url      = "/",
        description   = description,
        #summary      = "A fancy re-packaging of command-line tools.",
        version       = version_tag,
        terms_of_service="https://docs.olcf.ornl.gov/accounts/olcf_policy_guide.html",
        #contact={
        #    "name": "",
        #    "url": "",
        #    "email": "help@olcf.ornl.gov",
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

#app = api
app = FastAPI()
app.mount(api_version_prefix, api)

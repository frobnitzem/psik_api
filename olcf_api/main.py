from fastapi import Depends, APIRouter, FastAPI

from .dependencies import get_token_header
from .status import status
from .compute import compute
from .tasks import tasks

version_tag = "0.1"
api_version_prefix = "/api/v" + version_tag

router = APIRouter(prefix = api_version_prefix)
router.include_router(
    status,
    prefix="/status",
    tags = ["status"],
)
router.include_router(
    compute,
    prefix="/compute",
    tags = ["compute"],
)
router.include_router(
    tasks,
    prefix="/tasks",
    tags = ["tasks"],
)

#@router.get("/")
#async def docs():
#    return {"message": "Redirect to /docs"}

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

description = """
A programmatic way to access resources at OLCF.
"""

app = FastAPI(
        title="OLCF SuperFacility API",
        openapi_url=api_version_prefix+"/openapi.json",
        docs_url=api_version_prefix,
        description=description,
        #summary="A fancy re-packaging of command-line tools.",
        version=version_tag,
        terms_of_service="https://docs.olcf.ornl.gov/accounts/olcf_policy_guide.html",
        #contact={
        #    "name": "",
        #    "url": "",
        #    "email": "help@olcf.ornl.gov",
        #},
        openapi_tags = tags_metadata,
        responses = {404: {"description": "Not found"}},
    )
app.include_router(router)
# ... , dependencies=[Depends(get_token_header)]

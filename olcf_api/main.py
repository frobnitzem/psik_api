from fastapi import Depends, APIRouter, FastAPI

from .dependencies import get_token_header
from .status import status

router = APIRouter(prefix="/api/v0.1")
router.include_router(
    status,
    prefix="/status",
    #tags=["status"],
)

#@router.get("/")
#async def docs():
#    return {"message": "Redirect to /docs"}

app = FastAPI(responses={404: {"description": "Not found"}},
             )
app.include_router(router)
# ... , dependencies=[Depends(get_token_header)]

from typing import Annotated, Optional
import logging
_logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Header

import psik

from .config import managers
from .models import ErrorStatus, stamp_re

callback = APIRouter()

@callback.post("/{machine}/{jobid}")
async def do_callback(machine: str,
                      jobid: str,
                      cb: psik.Callback,
                      x_hub_signature_256: Annotated[Optional[str], Header()]
                                            = None
                     ) -> ErrorStatus:
    """ Notify psik_api that a job has reached a given state.
    This will call `psik.Job.reached`, forwarding
    the callback along the chain.
    """

    if not stamp_re.match(jobid):
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        mgr = managers[machine]
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")

    base = mgr.prefix / jobid
    if not base.is_dir():
        raise HTTPException(status_code=404, detail="Item not found")

    job = await psik.Job(base)
    if job.spec.client_secret:
        if x_hub_signature_256 is None:
            raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")
        psik.web.verify_signature(
                   cb.model_dump_json(), # FIXME - get actual message body
                   job.spec.client_secret.get_secret_value(),
                   x_hub_signature_256)

    ok = await job.reached(cb.jobndx, cb.state, cb.info)
    if not ok:
        return ErrorStatus.ERROR
    return ErrorStatus.OK

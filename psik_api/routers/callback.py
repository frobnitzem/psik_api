from typing import Annotated, Optional
import logging
_logger = logging.getLogger(__name__)

from fastapi import HTTPException, Header

import psik

from ..config import get_manager
from ..models import ErrorStatus, stamp_re
from .jobs import jobs, get_job

added_callback = True

@jobs.post("/callback")
async def do_callback(cb: psik.Callback,
                      x_hub_signature_256: Annotated[Optional[str], Header()]
                                            = None,
                      backend: Optional[str] = None,
                     ) -> ErrorStatus:
    """ Notify psik_api that a job has reached a given state.
    This will call `psik.Job.reached`, forwarding
    the callback along the chain.
    """
    jobid = cb.jobid
    base = await get_job(jobid, backend)
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

@jobs.get("/{jobid}/state")
async def get_state(jobid: str,
                    backend: Optional[str] = None
                   ) -> psik.JobState:
    """Read the current job's state.

      - jobid: str
      - backend: (optional) the compute resource name
    """

    base = await get_job(jobid, backend)
    job = await psik.Job(base)

    t, ndx, state, info = job.history[-1]
    return state

from typing import Optional, List
from typing_extensions import Annotated
import logging
_logger = logging.getLogger(__name__)

# TODO: switch to (simpler) aiofiles?
# https://superfastpython.com/aiofiles-for-asyncio-in-python/
from anyio import open_file
from fastapi import HTTPException, UploadFile, File

import psik

from ..models import ErrorStatus, stamp_re
from ..internal.paths import clean_rel_path
from .jobs import jobs, get_mgr, get_job

added_inputs = True

@jobs.post("/new")
async def new_input(jobspec: psik.JobSpec,
                    machine: Optional[str] = None) -> str:
    "Create a new job, but do not submit it."

    mgr = get_mgr(machine)
    try:
        job = await mgr.create(jobspec)
    except AssertionError as e:
        raise HTTPException(status_code=400,
                            detail=f"Error creating job: {str(e)}")
    return job.stamp

# see also: https://fastapi.tiangolo.com/tutorial/request-files/#multiple-file-uploads
@jobs.post("/{jobid}/files")
@jobs.post("/{jobid}/files/")
async def create_upload_file(jobid: str,
                             files: Annotated[
                                List[UploadFile],
                                File(description="Files uploaded as multipart/form-data")
                             ],
                             backend: Optional[str] = None
                            ):
    #return {"filenames": [file.filename for file in files]}
    job = await psik.Job(await get_job(jobid, backend))

    chunksz = 16*1024 # 16 kb chunk size

    for file in files:
        path = clean_rel_path(job, file.filename)
        if not path.parent.is_dir():
            raise HTTPException(status_code=404,
                                detail=f"Invalid path: {file.filename}")
        
        _logger.warning("Writing %s", path)
        # TODO: set file permissions?
        # TODO: detect whether file.read() will return str or bytes?
        async with await open_file(path, 'wb') as out:
            while True:
                buf = await file.read(chunksz)
                if buf is None or len(buf) == 0:
                    break
                if isinstance(buf, str):
                    buf = buf.encode('utf-8')
                n = await out.write(buf)

from typing import Dict, Optional
from pathlib import Path
import logging
_logger = logging.getLogger(__name__)

from fastapi import HTTPException
from fastapi.responses import FileResponse

import psik

from ..config import get_manager
from ..models import ErrorStatus
from ..internal.paths import clean_rel_path

from .jobs import jobs, get_job

added_outputs = True

@jobs.get("/{jobid}/logs")
@jobs.get("/{jobid}/logs/")
async def list_outputs(jobid: str,
                       backend: Optional[str] = None,
                      ) -> Dict[str,str]:
    """ Retreive all job logs.
    """
    logs = (await get_job(jobid, backend)) / "log"
    if not logs.is_dir():
        raise HTTPException(status_code=404, detail="log dir missing")
    ans : Dict[str,str] = {}
    for p in logs.iterdir():
        ans[p.name] = p.read_text()
    return ans

@jobs.get("/{jobid}/scripts")
@jobs.get("/{jobid}/scripts/")
async def download_scripts(jobid: str, backend: Optional[str] = None,
                          ) -> Dict[str,str]:
    """ Retreive all job scripts.
    """
    scripts = (await get_job(jobid, backend)) / "scripts"
    if not scripts.is_dir():
        raise HTTPException(status_code=404, detail="scripts dir missing")
    ans : Dict[str, str] = {}
    for p in scripts.iterdir():
        ans[p.name] = p.read_text()
    return ans

def stat_dir(path: Path) -> Dict[str, Dict[str,int]]:
    # Caution! the path is not checked to ensure
    # it is safe to serve. (caller should do this)
    ans = {}
    for p in path.iterdir():
        st = p.stat()
        ans[p.name] = { 'size': int(st.st_size),
                        'atime': int(st.st_atime),
                        'mtime': int(st.st_mtime)
                      }
    return ans

@jobs.get("/{jobid}/files")
@jobs.get("/{jobid}/files/")
async def list_output(jobid: str,
                      backend: Optional[str] = None,
                     ) -> Dict[str,Dict[str,int]]:
    """ List all output files.
    """
    job = await psik.Job(await get_job(jobid, backend))
    work = Path(job.spec.directory)
    if not work.is_dir():
        raise HTTPException(status_code=404, detail="work dir missing")
    return stat_dir(work)

@jobs.get("/{jobid}/files/{fname}")
async def download_output(jobid: str, fname: Path,
                          backend: Optional[str] = None):
    job = await psik.Job(await get_job(jobid, backend))

    path = clean_rel_path(job, fname)

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"file {fname} not found")
    if path.is_dir():
        return stat_dir(path)
    return FileResponse(path,
                        media_type='application/octet-stream',
                        filename=str(fname))

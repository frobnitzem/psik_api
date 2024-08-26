from typing import Dict
from pathlib import Path, PurePosixPath
import logging
_logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

import psik

from .config import managers
from .models import ErrorStatus, stamp_re

outputs = APIRouter()

def get_job(machine : str, jobid : str) -> Path:
    if not stamp_re.match(jobid):
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        mgr = managers[machine]
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")

    base = mgr.prefix / jobid
    if not base.is_dir():
        raise HTTPException(status_code=404, detail="Item not found")
    return Path(base)

@outputs.get("/{machine}/{jobid}/logs")
async def list_outputs(machine : str, jobid : str) -> Dict[str,str]:
    """ Retreive all job logs.
    """
    logs = get_job(machine, jobid) / "log"
    if not logs.is_dir():
        raise HTTPException(status_code=404, detail="log dir missing")
    ans : Dict[str,str] = {}
    for p in logs.iterdir():
        ans[p.name] = p.read_text()
    return ans

@outputs.get("/{machine}/{jobid}/scripts")
async def download_scripts(machine : str, jobid : str) -> Dict[str,str]:
    """ Retreive all job scripts.
    """
    scripts = get_job(machine, jobid) / "scripts"
    if not scripts.is_dir():
        raise HTTPException(status_code=404, detail="scripts dir missing")
    ans : Dict[str, str] = {}
    for p in scripts.iterdir():
        ans[p.name] = p.read_text()
    return ans

def stat_dir(path : Path) -> Dict[str, Dict[str,int]]:
    # Caution! the path is not checked to ensure
    # it is safe to serve.
    ans = {}
    for p in path.iterdir():
        st = p.stat()
        ans[p.name] = { 'size': int(st.st_size),
                        'atime': int(st.st_atime),
                        'mtime': int(st.st_mtime)
                      }
    return ans

@outputs.get("/{machine}/{jobid}/work")
async def list_output(machine : str, jobid : str) -> Dict[str,Dict[str,int]]:
    """ List all output files.
    """
    job = await psik.Job(get_job(machine, jobid))
    work = Path(job.spec.directory)
    if not work.is_dir():
        raise HTTPException(status_code=404, detail="work dir missing")
    return stat_dir(work)

@outputs.get("/{machine}/{jobid}/work/{fname}")
async def download_output(machine : str, jobid : str, fname : Path):
    job = await psik.Job(get_job(machine, jobid))
    work = Path(job.spec.directory)
    if not work.is_dir():
        raise HTTPException(status_code=404, detail="work dir missing")

    try:
        path = work / Path( PurePosixPath(work/fname).relative_to(work) )
    except ValueError:
        raise HTTPException(status_code=403, detail="invalid path")
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"file {fname} not found")

    if path.is_dir():
        return stat_dir(path)
    return FileResponse(path,
                        media_type='application/octet-stream',
                        filename=str(fname))

from pathlib import Path, PurePosixPath

from fastapi import HTTPException
import psik

from ..config import Pstr

def clean_rel_path(job: psik.Job, fname: Pstr) -> Path:
    """Take an unsafe, user-provided fname, and place it
    relative to the job.spec.directory (working dir. path).

    Throw an http exception if the path does not point within
    the work directory.
    """
    if job.spec.directory is None:
        raise HTTPException(status_code=404, detail="work dir missing")
    work = Path(job.spec.directory)
    if not work.is_dir():
        raise HTTPException(status_code=404, detail="work dir missing")

    try:
        path = work / Path( PurePosixPath(work/fname).relative_to(work) )
    except ValueError:
        raise HTTPException(status_code=403, detail="invalid path")

    # FIXME: check whether this path traverses a symlink
    # (https://stackoverflow.com/questions/41460434/getting-the-target-of-a-symbolic-link-with-pathlib)
    return path

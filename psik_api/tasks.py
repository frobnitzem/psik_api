from fastapi import HTTPException
import psik

# TODO: run the submission step as a BackgroundTask
async def submit_job(mgr : psik.JobManager,
                     spec : psik.JobSpec) -> str:
    try:
        job = await mgr.create(spec)
    except AssertionError as e:
        raise HTTPException(status_code=400,
                            detail=f"Error creating job: {str(e)}")
    try:
        await job.submit()
    except psik.SubmitException as e:
        raise HTTPException(status_code=400,
                            detail=f"Error submitting job: {str(e)}")
    return job.stamp

# TODO: run the cancel step as a BackgroundTask
async def cancel_job(job : psik.Job) -> None:
    # Note: race condition if the user somehow guesses the jobid
    # and cancels the job while being created (unlikely).
    try:
        await job.cancel()
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error canceling job: {str(e)}")
    return

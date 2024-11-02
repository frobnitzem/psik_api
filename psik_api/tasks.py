from fastapi import HTTPException, BackgroundTasks
import psik

async def submit_job(mgr: psik.JobManager,
                     spec: psik.JobSpec,
                     bg_tasks: BackgroundTasks) -> str:
    try:
        job = await mgr.create(spec)
    except AssertionError as e:
        raise HTTPException(status_code=400,
                            detail=f"Error creating job: {str(e)}")
    bg_tasks.add_task(job.submit)
    #try:
    #    await job.submit()
    #except psik.SubmitException as e:
    #    raise HTTPException(status_code=400,
    #                        detail=f"Error submitting job: {str(e)}")
    return job.stamp

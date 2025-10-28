from fastapi import HTTPException, BackgroundTasks
import psik

async def new_job(spec: psik.JobSpec,
                  mgr: psik.JobManager,
                 ) -> psik.Job:
    try:
        job = await mgr.create(spec)
    except AssertionError as e:
        raise HTTPException(status_code=400,
                            detail=f"Error creating job: {str(e)}")
    return job

    #bg_tasks.add_task(job.submit)
    #try:
    #    await job.submit()
    #except psik.SubmitException as e:
    #    raise HTTPException(status_code=400,
    #                        detail=f"Error submitting job: {str(e)}")
    #return job.stamp

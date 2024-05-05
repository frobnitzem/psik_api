PSI\_K API
========

This project presents a REST-HTTP API to
functionality available through other APIs and
command-line utilities on PSI\_K systems.

This API is inspired by the NERSC "superfacility" API
v1.2 and the ExaWorks JobSpec.  Differences come from
the need to make the superfacility more portable between
backends and the JobSpec more API-friendly.

To setup and run:

1. Install the rc shell and psik\_api (from the site you intend to use):

```
     module load python/3
     python3 -m venv
     getrc.sh venv # https://github.com/frobnitzem/rcrc
     VIRTUAL_ENV=/full/path/to/venv
     PATH=$VIRTUAL_ENV/bin:$PATH
   
     pip install git+https://github.com/frobnitzem/psik_api.git
```

2. Setup a psik\_api config file.  This file contains multiple
   psik config files -- one for each system you wish to access.

   Every machine in psik\_api corresponds to a particular
   psik config.  Be careful with the `psik_path` and `rc_path`
   options here, since these are the paths that must be
   accessible during the execution of the job.

   Note that the `PSIK_CONFIG` environment variable does not
   influence the server running `psik_api`.

   Create a config file at `$PSIK_API_CONFIG` (defaults to
   `$HOME/.config/psik_api.json`) like,

       { "default": {
           "prefix": "/ccs/proj/stf006/rogersdd/frontier",
           "psik_path": "/ccs/proj/stf006/rogersdd/frontier/bin/psik",
           "rc_path": "/ccs/proj/stf006/rogersdd/frontier/bin/rc",
           "backend": {
             "type": "slurm",
             "project_name": "stf006",
             "attributes": {
               "---gpu-bind": "closest"
             }
           }
         }
       }

   here, each entry maps a queue name (e.g. "default") to
   a `psik.Config` object.

3. Start the server.  This can be done either directly
   by ssh-tunneling to a login node, or indirectly
   by starting a long-running containerized service.

   The ssh-tunnel method is simplest,

```
    ssh frontier -L 127.0.0.1:8000:/ccs/home/rogersdd/psik_api.sock
    activate /ccs/proj/stf006/frontier
    uvicorn psik_api.main:app --log-level info --uds $HOME/psik_api.sock
```

    Note that using a UNIX socket in `$HOME` is secure since only
    your user can read/write from it.

4. Browse / access the API at:

```
   http://127.0.0.1:8000/
```

5. Send a test job:

```
    curl -X POST \
      http://127.0.0.1:8000/compute/jobs/default \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "name": "show system info",
      "script": "cat /proc/cpuinfo; cat /proc/meminfo; rocm-smi; echo $nodes; $mpirun hostname",
      "resources": {
        "process_count": 8,
        "cpu_cores_per_process": 7,
        "duration": 2,
        "gpu_cores_per_process": 1
      },
      "pre_submit": "pwd; module load rocm/5.5.1"
    }'

    curl -X 'GET' \
      'http://127.0.0.1:8000/tasks/' \
      -H 'accept: application/json'

    # replace 1693992878.203 with your job's timestamp
    curl -X 'GET' \
      'http://127.0.0.1:8000/compute/jobs/default/1693992878.203' \
      -H 'accept: application/json'
```

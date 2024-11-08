[![CI](https://github.com/frobnitzem/psik_api/actions/workflows/python-package.yml/badge.svg)](https://github.com/frobnitzem/psik_api/actions)
[![Coverage](https://codecov.io/github/frobnitzem/psik_api/branch/main/graph/badge.svg)](https://app.codecov.io/gh/frobnitzem/psik_api)

PSI\_K API
==========

This project presents a REST-HTTP API to PSI\_K,
a portable batch job submission interface.

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

2. Setup a psik\_api config file.  This file is a key-value store
   mapping machine names to psik config files
   -- one for each scheduler configuration.

   Be careful with the `psik_path` and `rc_path`
   options here. These paths must be
   accessible during the execution of the job, and
   on the host running psik\_api.

   Note that the `PSIK_CONFIG` environment variable does not
   influence the server running `psik_api`.

   Create a config file at `$PSIK_API_CONFIG` (defaults to
   `$VIRTUAL_ENV/etc/psik_api.json`) like,

       { "backends": {
           "default": {
             "prefix": "/tmp/psik_jobs",
             "backend": { "type": "local"}
           }
         }
       }

   or

       { "backends": {
           "default": {
             "prefix": "/ccs/proj/prj123/uname/frontier",
             "psik_path": "/ccs/proj/prj123/uname/frontier/bin/psik",
             "rc_path": "/ccs/proj/prj123/uname/frontier/bin/rc",
             "backend": {
               "type": "slurm",
               "project_name": "prj123",
               "attributes": {
               "---gpu-bind": "closest"
               }
             }
           }
         }
       }


3. Start the server.  This can be done either directly
   by ssh-tunneling to a login node, or indirectly
   by starting a long-running containerized service.

   The ssh-tunnel method is simplest,

```
    ssh frontier -L 127.0.0.1:8000:/ccs/home/uname/psik_api.sock
    activate /ccs/proj/prj123/frontier
    uvicorn psik_api.main:app --log-level info --uds $HOME/psik_api.sock
```

    Note that using a UNIX socket in `$HOME` is secure as long as
    only your user can read/write from it.

    For a more secure environment, use the `certified` package with:

        ssh frontier -L 8000:localhost:4433
        activate /ccs/proj/prj123/frontier
        certified serve psik_api.main:app https://127.0.0.1:4433

    `certified` is a dependency of psik_api, so should already
    be available if you have installed psik.
    
4. Browse / access the API at:

```
   http://127.0.0.1:8000/
```

5. Send a test job:

```
    curl -X POST \
      http://127.0.0.1:8000/v1/jobs \
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
      }
    }'

    curl -X GET \
      'http://127.0.0.1:8000/v1/jobs \
      -H 'accept: application/json'

    # replace 1693992878.203 with your job's jobid
    curl -X GET \
      'http://127.0.0.1:8000/v1/jobs/1693992878.203/logs' \
      -H 'accept: application/json'
```

6. Create a job without submitting it, then send input
   files, then submit

```
    # full JobSpec must be present at this point,
    # but it will not run until later
    curl -X POST \
      http://127.0.0.1:8000/v1/jobs/new \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "script": "cat data.txt",
    }'

    # replace 1693992878.203 with your job's jobid below
    # Upload files
    curl -X POST \
      'http://127.0.0.1:8000/v1/jobs/1693992878.203/files/ \
      -H 'accept: application/json' \
      --upload-file data.txt

    # start the job
    curl -X POST \
      'http://127.0.0.1:8000/v1/jobs/1693992878.203/start' \
      -H 'accept: application/json'
```

## Authorization and Authentication

The server has 3 modes of operation:

  1. local -- when specifically requested with
     configuration setting "authz"="local".
     In this mode, only requests originating from
     the localhost IP (either v4 or v6) will
     be served.  Also, this mode is the only
     way to serve the full API through a UNIX domain socket.

  2. insecure -- when Request.transport is not available
     (started without certified serve).  In this case
     the user name is taken as 'addr:<addr>' -- based
     on the client's address.  Psik_api will refuse
     to issue tokens (hence no access to secured
     routes) in this case.

  3. TLS -- when started with `certified serve`

In local mode, the system sees all jobs as owned by user
`local:psik_api`.

In TLS mode, the `user` value is read from a biscuit
token that the client provides on each request.
This should be present in a header like,
`Authorization: bearer b64-encoded-biscuit-value=`.
If no biscuit is provided with the request, then one is
auto-generated for that request by reading the client's
TLS certificate.

Note, a biscuit can also be generated with `user` == `client`
by visiting the `/token` endpoint.

A database tracks the owner of each job and grants GET/POST
permissions only to a job's owner.
This way, a user can delegate access permissions
to a job to another user or an automated agent.

Note that biscuits allow tokens to be attenuated
by enforcing additional checks.
For example, by checking mode=GET, they can confer a
token that grants read-only access.

Sites may customize the job access policy above by
implementing a custom authz class -- replacing
`psik_api.authz:BaseAuthz` in their `Config.authz`
setting.

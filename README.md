[![CI](https://github.com/frobnitzem/psik_api/actions/workflows/python-package.yml/badge.svg)](https://github.com/frobnitzem/psik_api/actions)
[![Coverage](https://codecov.io/github/frobnitzem/psik_api/branch/main/graph/badge.svg)](https://app.codecov.io/gh/frobnitzem/psik_api)

PSI\_K API
==========

This project presents a REST-HTTP API to PSI\_K,
a portable batch job submission interface.

To setup and run:

1. Install psik\_api (from the site you intend to use):

       python3 -m venv
       VIRTUAL_ENV=/full/path/to/venv
       PATH=$VIRTUAL_ENV/bin:$PATH
   
       pip install git+https://github.com/frobnitzem/psik_api.git

2. Setup a psik\_api config file.  This file is a key-value store
   mapping machine names to psik config files
   -- one for each scheduler configuration.

   Note that the `PSIK_CONFIG` environment variable does not
   influence the server running `psik_api`.

   The server loads configuration from the first available location in this order:
   1. A file path provided as an argument to the server
   2. The path specified in the `$PSIK_API_CONFIG` environment variable
   3. `$VIRTUAL_ENV/etc/psik_api.json` (if `$VIRTUAL_ENV` is defined)
   4. `/etc/psik_api.json`

   Example config:

       { "backends": {
           "default": {
             "type": "local"
           }
         },
         "prefix": "/tmp/psik_jobs"
       }

   or

       { "prefix": "/ccs/proj/prj123/uname/frontier",
         "backends": {
           "default": {
             "type": "slurm",
             "project_name": "prj123",
             "attributes": {
               "--gpu-bind": "closest"
             }
           }
         }
       }

   you can quickly test this setup with (bash)

       psik -vv --config psik_api.json run <(echo '{"name":"test", "script":"hostname; pwd; ls -l ../"}')

   or (rc)

       psik -vv --config psik_api.json run <{echo '{"name":"test", "script":"hostname; pwd; ls -l ../"}'}

3. Start the server.  This can be done either directly
   by ssh-tunneling to a login node, or indirectly
   by starting a long-running containerized service.

   The ssh-tunnel method is simplest,

        ssh frontier -L 127.0.0.1:8000:./psik_api.sock
        activate /ccs/proj/prj123/frontier
        uvicorn psik_api.main:app --log-level info --uds $HOME/psik_api.sock

    Note that using a UNIX socket in `$HOME` is secure as long as
    only your user can read/write from it.

    For a more secure environment, use the `certified` package with:

        ssh frontier -L 8000:localhost:4433
        activate /ccs/proj/prj123/frontier
        certified serve psik_api.main:app https://127.0.0.1:4433

    `certified` is a dependency of psik_api, so should already
    be available if you have installed psik.

    A `Dockerfile` is provided in this repo to faciliate
    running psik as a Kubernetes service.

4. Browse / access the API at:

```
   http://127.0.0.1:8000/v2
```

5. Send a test job:

```
    curl -X POST \
      http://127.0.0.1:8000/v2/jobs \
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
      'http://127.0.0.1:8000/v2/jobs \
      -H 'accept: application/json'

    # replace 1693992878.203 with your job's jobid
    curl -X GET \
      'http://127.0.0.1:8000/v2/jobs/1693992878.203/logs' \
      -H 'accept: application/json'
```

6. Create a job without submitting it, then send input
   files, then submit

```
    # full JobSpec must be present at this point,
    # but it will not run until later
    curl -X POST \
      http://127.0.0.1:8000/v2/jobs/new \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "script": "cat data.txt",
    }'

    # replace 1693992878.203 with your job's jobid below
    # Upload files
    curl -X POST \
      'http://127.0.0.1:8000/v2/jobs/1693992878.203/files/ \
      -H 'accept: application/json' \
      --upload-file data.txt

    # start the job
    curl -X POST \
      'http://127.0.0.1:8000/v2/jobs/1693992878.203/start' \
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

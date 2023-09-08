OLCF API
========

This project presents a REST-HTTP API to
functionality available through other APIs and
command-line utilities on OLCF systems.

Note that this API differs from NERSC v1.2 because
it uses a Psi\_k, which implements a JobSpec
based on the ExaWorks job api.

To setup and run:

1. Install olcf\_api (from the site you intend to use):
   Note that psik (installed automatically as a dependency) must
   be accessible to your job script so it can provide status updates.
   This is usually the case because the PATH var should
   include olcf\_api's VIRTUAL\_ENV/bin.

     module load python/3
     python3 -m venv
     getrc.sh venv # https://github.com/frobnitzem/rcrc
     VIRTUAL_ENV=/full/path/to/venv
     PATH=$VIRTUAL_ENV/bin:$PATH
   
     pip install git+https://code.ornl.gov/olcf_api

     Create a config file in $HOME/.config/psik.json
     listing your job working directory and project id:
        {
        "prefix": "/lustre/orion/stf006/scratch/rogersdd/andes",
        "backend": "slurm",
        "default_attr": {
            "project_name": "stf006",
            "custom_attributes": {
                    "slurm": {"--gpu-bind": "closest"},
                    "jsrun": {"-b": "packed:rs"}
                }
            }
        }

2. Set up a local to remote ssh tunnel and 
   start a worker process:

    ssh andes -L 127.0.0.1:8000:/ccs/home/rogersdd/olcf_api.sock
    activate venv
    uvicorn olcf_api.main:app --log-level info \
             --uds $HOME/olcf_api.sock

    Note that using a UNIX socket in $HOME is secure since only
    your user can read/write from it.

4. Browse / access the API at:

   http://127.0.0.1:8000/api/v0.2

5. Send a test job:

    curl -X POST \
      http://127.0.0.1:8000/api/v0.2/compute/jobs/frontier \
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
      'http://127.0.0.1:8000/api/v0.2/tasks/' \
      -H 'accept: application/json'

    # replace 1693992878.203 with your job's timestamp
    curl -X 'GET' \
      'http://127.0.0.1:8000/api/v0.2/compute/jobs/frontier/1693992878.203' \
      -H 'accept: application/json'


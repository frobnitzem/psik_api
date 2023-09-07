# run on a socket if LMOD_SYSTEM_NAME is defined
[ -z $LMOD_SYSTEM_NAME ] && poetry run uvicorn olcf_api.main:app --reload --log-level info
[ -z $LMOD_SYSTEM_NAME ] || poetry run uvicorn olcf_api.main:app --reload --log-level info --uds $HOME/olcf_api.sock

# Notes (https://www.uvicorn.org/deployment/)
#
# Secure options for single-user execution:
#--uds $HOME/olcf_api.sock # process requests through a UNIX domain socket
#--fd 0 # process requests through stdin/out

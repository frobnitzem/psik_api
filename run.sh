poetry run uvicorn olcf_api.main:app --reload --log-level info

# Secure options for single-user execution:
#--uds $HOME/olcf_api.sock # process requests through a UNIX domain socket
#--fd 0 # process requests through stdin/out

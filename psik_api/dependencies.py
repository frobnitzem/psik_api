from typing import Optional
from typing_extensions import Annotated
import sys
import os
import importlib

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from certified.fast import BiscuitAuthz

def fail_auth(req, biscuit):
    raise HTTPException(status_code=501,
                        detail='setup_security not called.')

# place-holders until setup_security is called.
_create_token = lambda req: None # Don't generate tokens.
_Authz = fail_auth

_oauth2_scheme = OAuth2AuthorizationCodeBearer(
                   authorizationUrl="/auth",
                   tokenUrl="/token",
                   auto_error=False,
                 )

def run_auth(req: Request,
             biscuit: Annotated[Optional[str], Depends(_oauth2_scheme)] = None,
            ) -> bool:
    # Expects a header of the form:
    # "Authorization: bearer b64-encoded biscuit"
    if biscuit is None:
        # Will create a token with user=client
        # if no biscuit has been provided.
        biscuit = create_token(req)
    try:
        return _Authz(req, biscuit)
    except KeyError as e:
        if str(e) == "'transport'":
            return True
        raise

# functions exported by this module:
def create_token(req: Request) -> Optional[str]:
    return _create_token(req)

Authz = Depends(run_auth)

def setup_security(policyfn: str):
    """ Import the policyfn and run it to create
    authz, an instance of the authz class.

    Then populate Authz and create_token from it.
    """
    global _Authz, _create_token

    mod_name, fn_name = policyfn.split(':')

    sys.path.insert(0, os.getcwd())
    mod = importlib.import_module(mod_name)
    # TODO: allow reloading policy fn.
    #importlib.reload(mymodule)
    authorizor_fn = getattr(mod, fn_name)
    sys.path.pop(0)

    authz = authorizor_fn()
    _Authz = BiscuitAuthz("psik_api",
                          authz.get_pubkey,
                          authz)
    _create_token = authz.create_token

from typing import List, Optional
from datetime import datetime, timedelta, timezone
import logging
_logger = logging.getLogger(__name__)

from fastapi import Request
from certified.fast import get_clientname

from biscuit_auth import (
        BiscuitBuilder,
        Authorizer,
        KeyPair,
        Biscuit,
        PublicKey,
        BiscuitValidationError,
        AuthorizationError,
        Fact,
        Policy,
        Rule
)

class BaseAuthz:
    """ Basic authorizer which provides a __call__
    method as expected by psik-api.

    This class should *not* be referenced directly
    by psik_api.  Instead, psik_api.dependencies
    dynamically loads create_token
    and Authz functions from config.authz.

    If you wish to implement your own authorization
    mechanism, it may be simpler to override
    this method - then put your override in place
    by referencing it from config.authz.
    """
    def __init__(self):
        keypair = KeyPair() # new random keypair
        self.pubkey = keypair.public_key
        self.privkey = keypair.private_key

    #@property
    #def pubkey(self) -> str:
    #    # serialize a keypair to hexadecimal strings
    #    return self.public_key.to_hex()

    def get_pubkey(self, idx):
        return self.pubkey

    def create_token(self, req: Request) -> Optional[str]:
        client = get_clientname(req)
        if client.startswith("addr:"):
            _logger.warning("Refusing to create token for (insecure) address-based client: %s", client)
            return None
        _logger.info("Creating token for %s", client)

        tok = BiscuitBuilder("""
            user({user_id});
            check if time($time), $time < {expiration};
        """,
        { 'user_id': client,
          'expiration': datetime.now(tz = timezone.utc) \
                      + timedelta(days = 1)
        })
        return tok.build(self.privkey).to_base64()
        #return None

    def add_rules(self, auth: Authorizer) -> bool:
        # Default rule - every user is a super-user,
        # and can delegate to any client.
        #
        # TODO: add_fact(Fact("owner({user},{path})", {...}))
        auth.add_rule(Rule('right($u, $c, $p, $op) <- user($u), client($c), path($p), operation($op)'))
        return True

    def is_revoked(self, revocation_ids: List[str]) -> bool:
        return False

    def __call__(self,
                 auth: Authorizer,
                 revocation_ids: List[str]) -> bool:
        if self.is_revoked(revocation_ids):
            return False

        ok = self.add_rules(auth)
        if not ok:
            return False
        auth.add_policy(
                  Policy("allow if user($u), "
                         "client($c), "
                         "path($p), "
                         "operation($op), "
                         "right($u, $c, $p, $op)"
                  )
              )
        try:
            auth.authorize()
        except AuthorizationError:
            return False
        return True

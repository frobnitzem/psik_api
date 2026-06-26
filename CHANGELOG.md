## Version 3.0

This version is technically a major version update because there is one
backward-incompatible change related to callback (and job state transition)
formatting.

1. Callback.info (and Transition.info) are now str instead of int types.

2. More backend types (provided by psik-3 release).

   Updating to psik-3 also brings in a refreshed backend design
   along with IRI and the much awaited psik-api backends.

2. Finally, there's a new option in the callback structure.

   JobSpec.callback, JobSpec.cb\_headers is now supported,
   in addition to the original JobSpec.callback (URL) and
   JobSpec.cb\_secret (shared hmac256 validation secret).

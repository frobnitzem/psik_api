import os
import psik


system = os.environ.get("LMOD_SYSTEM_NAME", "localhost")

config = psik.config.load_config(None)
managers = {
          system: psik.JobManager(config.prefix, config.backend,
                                  config.default_attr)
        }

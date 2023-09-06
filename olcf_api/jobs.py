import psik

config = psik.config.load_config(None)
managers = {
          "andes": psik.JobManager(config.prefix, config.backend,
                                   config.default_attr)
        }

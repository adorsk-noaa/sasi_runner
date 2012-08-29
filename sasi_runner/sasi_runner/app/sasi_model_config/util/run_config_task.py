import sasi_runner.app.sasi_model_config.util.tasks as tasks


class RunConfigTask(tasks.Task):
    def __init__(self, config=None):
        super(RunConfigTask, self).__init__()
        self.config = config

    def run(self):
        # Validate the config.
        # Make target directory.
        # Unpack config files to tmp dir.
        # Generate metadata.
        # Generate model results.
        # Format results and metadata per output format.
        # Create results object.
        # Generate results link.
        pass

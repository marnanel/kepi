import os
import glob
import logging

logger = logging.getLogger('kepi')

class Daemon:
    def __init__(self,
                 config,
                 ):

        self._config = config
        self._set_up()

        logger.info("Daemon ready.")

    def _set_up(self):
        try:
            os.makedirs(self._config['spool'])
        except FileExistsError:
            self._load_existing_spool()

    def _load_existing_spool(self):
        raise NotImplementedError()

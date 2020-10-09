"""Module for running docker-container tests"""
from __future__ import absolute_import

import os
import logger

from .native_host import make_native_host
from .external_module import ExternalModule


LOGGER = logger.get_logger('docker')


class NativeModule(ExternalModule):
    """Class for running native tests"""

    # pylint: disable=too-many-arguments
    def __init__(self, host, tmpdir, test_name, module_config, basedir, startup_cmd):
        super().__init__(host, tmpdir, test_name, module_config, basedir=basedir)
        self.startup_cmd = startup_cmd

    def start(self, port, params, callback, finish_hook):
        """Start the native test"""
        super().start(port, params, callback, finish_hook)
        LOGGER.debug("activating native test %s", self)

    def _get_env_vars(self, params):
        env_vars = super()._get_env_vars(params)
        env_vars.append(('TEST_ROOT', self.basedir))
        return env_vars

    def _get_vol_maps(self, params):
        vol_maps = super()._get_vol_maps(params)

        # Common testing tools
        vol_maps.append((os.path.abspath('bin/retry_cmd'), '/bin/retry_cmd'))
        vol_maps.append((os.path.abspath('docker/include/utils/reporting.sh'),
                         os.path.join(self.basedir, 'reporting.sh')))
        return vol_maps

    def _get_module_class(self):
        LOGGER.debug("%s running native test %s", self, self.test_name)
        return make_native_host(self.basedir, self.startup_cmd)

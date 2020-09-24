"""Host module base class"""

from __future__ import absolute_import

import datetime
from abc import ABC
import logger


LOGGER = logger.get_logger('module')


class HostModule(ABC):
    """Base class for host test modules"""

    def __init__(self, host, tmpdir, test_name, module_config):
        self.host = host
        self.tmpdir = tmpdir
        self.test_name = test_name
        self.device = host.device
        self.test_config = module_config.get('modules').get(test_name)
        self.runner = host.runner
        self.host_name = '%s%02d' % (test_name, host.device.set_id)
        # Host name can't be more than 10 characters because it is also used to create a
        # network interface with -eth0 on the end and there's a hard linux limit on length.
        assert len(self.host_name) <= 10, 'Hostname %s too long'
        self.callback = None
        self._finish_hook = None
        self.port = None
        self.params = None
        self.start_time = None

    def start(self, port, params, callback, finish_hook):
        """Start a test module"""
        LOGGER.debug('Starting test module %s', self)
        self.port = port
        self.params = params
        self.callback = callback
        self._finish_hook = finish_hook
        self.start_time = datetime.datetime.now()

    def ip_listener(self, target_ip):
        """Defaults to do nothing about ip notifications"""

    def heartbeat(self):
        """For modules that need to do periodic checks"""

    def __repr__(self):
        return "Target device %s test %s" % (self.device, self.test_name)

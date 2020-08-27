"""Module for running docker-container tests"""

import subprocess
import logger
from clib import docker_host

from .external_test import ExternalTest


LOGGER = logger.get_logger('docker')


class DockerTest(ExternalTest):
    """Class for running docker tests"""

    IMAGE_NAME_FORMAT = 'daqf/test_%s'
    TAGGED_IMAGE_FORMAT = IMAGE_NAME_FORMAT + ':latest'
    CONTAINER_PREFIX = 'daq'

    def start(self, port, params, callback, finish_hook):
        """Start the docker test"""
        super().start(port, params, callback, finish_hook)
        LOGGER.debug("%s activating docker test %s", self)
        # Docker tests don't use DHCP, so manually set up DNS.
        if self.host:
            self.host.cmd('echo nameserver $GATEWAY_IP > /etc/resolv.conf')

    def _get_env_vars(self, params):
        env_vars = super()._get_env_vars(params)
        return ["%s=%s" % var for var in env_vars]

    def _get_vol_maps(self, params):
        vol_maps = super()._get_vol_maps(params)
        return ["%s:%s" % vol_map for vol_map in vol_maps]

    def _get_test_class(self):
        image = self.IMAGE_NAME_FORMAT % self.test_name
        LOGGER.debug("%s running docker test %s", self, image)
        cls = docker_host.make_docker_host(image, prefix=self.CONTAINER_PREFIX)
        # Work around an instability in the faucet/clib/docker library, b/152520627.
        setattr(cls, 'pullImage', self._check_image)
        return cls

    def _check_image(self):
        lines = subprocess.check_output(["docker", "images", "--format",
                                         "{{ .Repository }}:{{ .Tag }}"])
        expected = self.TAGGED_IMAGE_FORMAT % self.test_name
        lines = str(lines, 'utf-8').splitlines()
        assert expected in lines, 'Could not find image %s, maybe rebuild images.' % expected

"""Module for running docker-container tests"""

import logging

from clib import docker_host

LOGGER = logging.getLogger('docker')

class DockerTest(object):
    """Class for running docker tests"""
    IMAGE_NAME_FORMAT = 'daq/test_%s'
    CONTAINER_PREFIX = 'daq'

    port_set = None
    test_name = None
    host_name = None
    runner = None
    tmpdir = None
    docker_log = None
    docker_host = None
    callback = None

    def __init__(self, runner, parent, test_name):
        self.port_set = parent.port_set
        self.tmpdir = parent.tmpdir
        self.test_name = test_name
        self.runner = runner
        self.host_name = '%s%02d' % (test_name, self.port_set)

    def start(self, port, params, callback):
        """Start the docker test"""
        LOGGER.info('Set %d running test %s', self.port_set, self.test_name)

        self.callback = callback

        env_vars = ["TARGET_NAME=" + self.host_name,
                    "TARGET_IP=" + params['target_ip'],
                    "TARGET_MAC=" + params['target_mac'],
                    "GATEWAY_IP=" + params['gateway_ip'],
                    "GATEWAY_MAC=" + params['gateway_mac']]
        vol_maps = [params['scan_base'] + ":/scans"]

        image = self.IMAGE_NAME_FORMAT % self.test_name
        LOGGER.debug("Set %d running docker test %s", self.port_set, image)
        cls = docker_host.make_docker_host(image, prefix=self.CONTAINER_PREFIX)
        host = self.runner.add_host(self.host_name, port=port, cls=cls, env_vars=env_vars,
                                    vol_maps=vol_maps, tmpdir=self.tmpdir)
        self.docker_host = host
        try:
            host = self.docker_host
            pipe = host.activate(log_name=None)
            self.docker_log = host.open_log()
            self.runner.monitor_stream(self.host_name, pipe.stdout, copy_to=self.docker_log,
                                       hangup=self._docker_complete,
                                       error=self._docker_error)
        except:
            host.terminate()
            self.runner.remove_host(host)
            raise

    def _docker_error(self, e):
        LOGGER.error('Set %d docker error: %s', self.port_set, e)
        self._docker_finalize()
        self.callback(exception=e)

    def _docker_finalize(self):
        if self.docker_host:
            self.runner.remove_host(self.docker_host)
            return_code = self.docker_host.terminate()
            self.docker_host = None
            self.docker_log.close()
            self.docker_log = None
            return return_code
        return None

    def _docker_complete(self):
        try:
            return_code = self._docker_finalize()
            exception = None
        except Exception as e:
            return_code = -1
            exception = e
        LOGGER.debug("Set %d docker complete, return=%d (%s)",
                     self.port_set, return_code, exception)
        if return_code:
            LOGGER.info("Set %d FAILED test %s with error %s: %s",
                        self.port_set, self.test_name, return_code, exception)
        else:
            LOGGER.info("Set %d PASSED test %s", self.port_set, self.test_name)
        self.callback(return_code=return_code, exception=exception)

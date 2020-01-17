"""Module for running docker-container tests"""

import datetime
import logging
import os

from clib import docker_host
import wrappers

LOGGER = logging.getLogger('docker')


class DockerTest():
    """Class for running docker tests"""

    IMAGE_NAME_FORMAT = 'daq/test_%s'
    CONTAINER_PREFIX = 'daq'

    def __init__(self, runner, target_port, tmpdir, test_name):
        self.target_port = target_port
        self.tmpdir = tmpdir
        self.test_name = test_name
        self.runner = runner
        self.host_name = '%s%02d' % (test_name, self.target_port)
        self.docker_log = None
        self.docker_host = None
        self.callback = None
        self.start_time = None
        self.pipe = None

    def start(self, port, params, callback):
        """Start the docker test"""
        LOGGER.debug('Target port %d starting docker test %s', self.target_port, self.test_name)

        self.start_time = datetime.datetime.now()
        self.callback = callback

        env_vars = ["TARGET_NAME=" + self.host_name,
                    "TARGET_IP=" + params['target_ip'],
                    "TARGET_MAC=" + params['target_mac'],
                    "GATEWAY_IP=" + params['gateway_ip'],
                    "GATEWAY_MAC=" + params['gateway_mac']]


        if 'local_ip' in params:
            env_vars += ["LOCAL_IP=" + params['local_ip'],
                         "SWITCH_PORT=" + params['switch_port'],
                         "SWITCH_IP=" + params['switch_ip'],
                         "SWITCH_MODEL=" + params['switch_model']]

        vol_maps = [params['scan_base'] + ":/scans"]

        self._map_if_exists(vol_maps, params, 'inst')
        self._map_if_exists(vol_maps, params, 'port')
        self._map_if_exists(vol_maps, params, 'device')
        self._map_if_exists(vol_maps, params, 'type')

        image = self.IMAGE_NAME_FORMAT % self.test_name
        LOGGER.debug("Target port %d running docker test %s", self.target_port, image)
        cls = docker_host.make_docker_host(image, prefix=self.CONTAINER_PREFIX)
        try:
            host = self.runner.add_host(self.host_name, port=port, cls=cls, env_vars=env_vars,
                                        vol_maps=vol_maps, tmpdir=self.tmpdir)
            self.docker_host = host
        except Exception as e:
            # pylint: disable=no-member
            raise wrappers.DaqException(e)
        try:
            LOGGER.debug("Target port %d activating docker test %s", self.target_port, image)
            host = self.docker_host
            self.pipe = host.activate(log_name=None)
            # Docker tests don't use DHCP, so manually set up DNS.
            host.cmd('echo nameserver $GATEWAY_IP > /etc/resolv.conf')
            self.docker_log = host.open_log()
            self.runner.monitor_stream(self.host_name, self.pipe.stdout, copy_to=self.docker_log,
                                       hangup=self._docker_complete,
                                       error=self._docker_error)
        except:
            host.terminate()
            self.runner.monitor_forget(self.pipe.stdout)
            self.runner.remove_host(host)
            raise
        LOGGER.info("Target port %d test %s running", self.target_port, self.test_name)

    def terminate(self):
        """Forcibly terminate this container"""
        if not self.docker_host:
            raise Exception("Target port %d test %s already terminated" % (
                self.target_port, self.test_name))
        LOGGER.info("Target port %d test %s terminating", self.target_port, self.test_name)
        return self._docker_finalize()

    def _map_if_exists(self, vol_maps, params, kind):
        base = params.get('%s_base' % kind)
        if base and os.path.exists(base):
            abs_base = os.path.abspath(base)
            vol_maps += ['%s:/config/%s' % (abs_base, kind)]

    def _docker_error(self, e):
        LOGGER.error('Target port %d docker error: %s', self.target_port, e)
        if self._docker_finalize() is None:
            LOGGER.warning('Target port %d docker already terminated.', self.target_port)
        else:
            self.callback(exception=e)

    def _docker_finalize(self, forget=True):
        if self.docker_host:
            LOGGER.debug('Target port %d docker finalize', self.target_port)
            self.runner.remove_host(self.docker_host)
            if forget:
                self.runner.monitor_forget(self.pipe.stdout)
                self.pipe = None
            return_code = self.docker_host.terminate()
            self.docker_host = None
            self.docker_log.close()
            self.docker_log = None
            return return_code
        return None

    def _docker_complete(self):
        try:
            assert self.pipe, 'complete without active pipe'
            self.pipe = None
            return_code = self._docker_finalize(forget=False)
            exception = None
        except Exception as e:
            return_code = -1
            exception = e
            LOGGER.exception(e)
        delay = (datetime.datetime.now() - self.start_time).total_seconds()
        LOGGER.debug("Target port %d docker complete, return=%d (%s)",
                     self.target_port, return_code, exception)
        if return_code:
            LOGGER.info("Target port %d test %s failed %ss: %s %s",
                        self.target_port, self.test_name, delay, return_code, exception)
        else:
            LOGGER.info("Target port %d test %s passed %ss",
                        self.target_port, self.test_name, delay)
        self.callback(return_code=return_code, exception=exception)

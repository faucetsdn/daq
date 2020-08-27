"""Module for running docker-container tests"""

import datetime
import os
import subprocess
import string
import random

from base_module import HostModule

import logger
from clib import docker_host
import wrappers

LOGGER = logger.get_logger('docker')


class DockerTest(HostModule):
    """Class for running docker tests"""

    IMAGE_NAME_FORMAT = 'daqf/test_%s'
    TAGGED_IMAGE_FORMAT = IMAGE_NAME_FORMAT + ':latest'
    CONTAINER_PREFIX = 'daq'

    def __init__(self, host, tmpdir, test_name, module_config):
        super().__init__(host, tmpdir, test_name, module_config)
        self.docker_log = None
        self.docker_host = None
        self.pipe = None

    def start(self, port, params, callback, finish_hook):
        """Start the docker test"""
        super().start(port, params, callback, finish_hook)

        def opt_param(key):
            return params.get(key) or ''  # Substitute empty string for None

        env_vars = [
            "TARGET_NAME=" + self.host_name,
            "TARGET_IP=" + params['target_ip'],
            "TARGET_MAC=" + params['target_mac'],
            "TARGET_PORT=" + opt_param('target_port'),
            "GATEWAY_IP=" + params['gateway_ip'],
            "GATEWAY_MAC=" + params['gateway_mac'],
            "LOCAL_IP=" + opt_param('local_ip'),
            ]

        vol_maps = [params['scan_base'] + ":/scans"]
        self._map_if_exists(vol_maps, params, 'inst')
        self._map_if_exists(vol_maps, params, 'port')
        self._map_if_exists(vol_maps, params, 'device')
        self._map_if_exists(vol_maps, params, 'type')

        image = self.IMAGE_NAME_FORMAT % self.test_name
        LOGGER.debug("%s running docker test %s", self, image)
        cls = docker_host.make_docker_host(image, prefix=self.CONTAINER_PREFIX)
        # Work around an instability in the faucet/clib/docker library, b/152520627.
        setattr(cls, 'pullImage', self._check_image)
        try:
            host = self.runner.add_host(self.host_name, port=port, cls=cls, env_vars=env_vars,
                                        vol_maps=vol_maps, tmpdir=self.tmpdir)
            self.docker_host = host
        except Exception as e:
            # pylint: disable=no-member
            raise wrappers.DaqException(e)

        try:
            LOGGER.debug("%s activating docker test %s", self, image)
            pipe = host.activate(log_name=None)
            # Docker tests don't use DHCP, so manually set up DNS.
            host.cmd('echo nameserver $GATEWAY_IP > /etc/resolv.conf')
            self.docker_log = host.open_log()
            if self._should_raise_test_exception('initialize'):
                LOGGER.error('%s inducing initialization failure', self)
                raise Exception('induced initialization failure')
            self.runner.monitor_stream(self.host_name, pipe.stdout, copy_to=self.docker_log,
                                       hangup=self._docker_complete,
                                       error=self._docker_error)
            self.pipe = pipe
            if self._should_raise_test_exception('callback'):
                LOGGER.error('%s will induce callback failure', self)
                # Closing this now will cause error when attempting to write output.
                self.docker_log.close()
        except Exception as e:
            host.terminate()
            self.runner.remove_host(host)
            self.docker_host = None
            if self.pipe:
                self.runner.monitor_forget(self.pipe.stdout)
                self.pipe = None
            raise e
        LOGGER.info("%s running", self)

    def _check_image(self):
        lines = subprocess.check_output(["docker", "images", "--format",
                                         "{{ .Repository }}:{{ .Tag }}"])
        expected = self.TAGGED_IMAGE_FORMAT % self.test_name
        lines = str(lines, 'utf-8').splitlines()
        assert expected in lines, 'Could not find image %s, maybe rebuild images.' % expected

    def terminate(self):
        """Forcibly terminate this container"""
        LOGGER.info("%s terminating", self)
        return self._docker_finalize()

    def _map_if_exists(self, vol_maps, params, kind):
        base = params.get('%s_base' % kind)
        if base and os.path.exists(base):
            abs_base = os.path.abspath(base)
            vol_maps += ['%s:/config/%s' % (abs_base, kind)]
            LOGGER.info('%s mapping %s to /config/%s', self, abs_base, kind)

    def _docker_error(self, exception):
        LOGGER.error('%s docker error: %s', self, str(exception))
        if self._docker_finalize() is None:
            LOGGER.warning('%s docker already terminated.', self)
        else:
            self.callback(exception=exception)

    def _docker_finalize(self):
        assert self.docker_host, 'docker host %s already finalized' % self
        if self._finish_hook:
            self._finish_hook()
        self.runner.remove_host(self.docker_host)
        if self.pipe:
            self.runner.monitor_forget(self.pipe.stdout)
            self.pipe = None
        return_code = self.docker_host.terminate()
        LOGGER.info('%s docker finalize %d', self, return_code)
        self.docker_host = None
        self.docker_log.close()
        self.docker_log = None
        if self._should_raise_test_exception('finalize'):
            LOGGER.error('%s inducing finalize failure', self)
            raise Exception('induced finalize failure')
        return return_code

    def _should_raise_test_exception(self, trigger_value):
        key = "%s_%s" % (self.test_name, self.device.mac.replace(':', ''))
        return self.runner.config.get('fail_module', {}).get(key) == trigger_value

    def _docker_complete(self):
        try:
            assert self.pipe, 'complete without active pipe'
            self.pipe = None
            return_code = self._docker_finalize()
            exception = None
        except Exception as e:
            return_code = -1
            exception = e
            LOGGER.exception(e)
        delay = (datetime.datetime.now() - self.start_time).total_seconds()
        LOGGER.debug("%s docker complete, return=%d (%s)",
                     self, return_code, exception)
        if return_code:
            LOGGER.info("%s failed %ss: %s %s",
                        self, delay, return_code, exception)
        else:
            LOGGER.info("%s passed %ss",
                        self, delay)
        self.callback(return_code=return_code, exception=exception)

    def _get_random_string(self, length):
        return ''.join(random.choice(string.ascii_letters) for _ in range(length))

    def ip_listener(self, target_ip):
        """Do nothing b/c docker tests don't care about ip notifications"""

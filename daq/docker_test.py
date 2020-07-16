"""Module for running docker-container tests"""

import datetime
import os
import subprocess

import logger
from clib import docker_host
import wrappers

LOGGER = logger.get_logger('docker')


class DockerTest:
    """Class for running docker tests"""

    IMAGE_NAME_FORMAT = 'daqf/test_%s'
    TAGGED_IMAGE_FORMAT = IMAGE_NAME_FORMAT + ':latest'
    CONTAINER_PREFIX = 'daq'

    # pylint: disable=too-many-arguments
    def __init__(self, host, target_port, tmpdir, test_name, module_config):
        self.target_port = target_port
        self.tmpdir = tmpdir
        self.test_name = test_name
        self.runner = host.runner
        self.host_name = '%s%02d' % (test_name, self.target_port)
        self.docker_log = None
        self.docker_host = None
        self.callback = None
        self.start_time = None
        self.pipe = None
        self._finish_hook = None

    def start(self, port, params, callback, finish_hook):
        """Start the docker test"""
        LOGGER.debug('Target port %d starting docker test %s', self.target_port, self.test_name)

        self.start_time = datetime.datetime.now()
        self.callback = callback
        self._finish_hook = finish_hook

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
        LOGGER.debug("Target port %d running docker test %s", self.target_port, image)
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
            LOGGER.debug("Target port %d activating docker test %s", self.target_port, image)
            pipe = host.activate(log_name=None)
            # Docker tests don't use DHCP, so manually set up DNS.
            host.cmd('echo nameserver $GATEWAY_IP > /etc/resolv.conf')
            self.docker_log = host.open_log()
            if self._should_raise_test_exception('initialize'):
                LOGGER.error('Target port %d inducing initialization failure', self.target_port)
                raise Exception('induced initialization failure')
            self.runner.monitor_stream(self.host_name, pipe.stdout, copy_to=self.docker_log,
                                       hangup=self._docker_complete,
                                       error=self._docker_error)
            self.pipe = pipe
            if self._should_raise_test_exception('callback'):
                LOGGER.error('Target port %d will induce callback failure', self.target_port)
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
        LOGGER.info("Target port %d test %s running", self.target_port, self.test_name)

    def _check_image(self):
        lines = subprocess.check_output(["docker", "images", "--format",
                                         "{{ .Repository }}:{{ .Tag }}"])
        expected = self.TAGGED_IMAGE_FORMAT % self.test_name
        lines = str(lines, 'utf-8').splitlines()
        assert expected in lines, 'Could not find image %s, maybe rebuild images.' % expected

    def terminate(self):
        """Forcibly terminate this container"""
        LOGGER.info("Target port %d test %s terminating", self.target_port, self.test_name)
        return self._docker_finalize()

    def _map_if_exists(self, vol_maps, params, kind):
        base = params.get('%s_base' % kind)
        if base and os.path.exists(base):
            abs_base = os.path.abspath(base)
            vol_maps += ['%s:/config/%s' % (abs_base, kind)]
            LOGGER.info('Target port %d mapping %s to /config/%s', self.target_port, abs_base, kind)

    def _docker_error(self, exception):
        LOGGER.error('Target port %d docker error: %s', self.target_port, str(exception))
        if self._docker_finalize() is None:
            LOGGER.warning('Target port %d docker already terminated.', self.target_port)
        else:
            self.callback(exception=exception)

    def _docker_finalize(self):
        assert self.docker_host, 'docker host %s already finalized' % self.target_port
        LOGGER.info('Target port %d docker finalize', self.target_port)
        if self._finish_hook:
            self._finish_hook()
        self.runner.remove_host(self.docker_host)
        if self.pipe:
            self.runner.monitor_forget(self.pipe.stdout)
            self.pipe = None
        return_code = self.docker_host.terminate()
        self.docker_host = None
        self.docker_log.close()
        self.docker_log = None
        if self._should_raise_test_exception('finalize'):
            LOGGER.error('Target port %d inducing finalize failure', self.target_port)
            raise Exception('induced finalize failure')
        return return_code

    def _should_raise_test_exception(self, trigger_value):
        key = '%s_%02d' % (self.test_name, self.target_port)
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
        LOGGER.debug("Target port %d docker complete, return=%d (%s)",
                     self.target_port, return_code, exception)
        if return_code:
            LOGGER.info("Target port %d test %s failed %ss: %s %s",
                        self.target_port, self.test_name, delay, return_code, exception)
        else:
            LOGGER.info("Target port %d test %s passed %ss",
                        self.target_port, self.test_name, delay)
        self.callback(return_code=return_code, exception=exception)

    def ip_listener(self, target_ip):
        """Do nothing b/c docker tests don't care about ip notifications"""

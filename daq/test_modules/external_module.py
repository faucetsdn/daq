"""Class for running non inline modules"""
from __future__ import absolute_import

import datetime
import abc
import os
from ipaddress import ip_network, ip_address

import logger
import wrappers

from .base_module import HostModule


LOGGER = logger.get_logger('exmodule')


class ExternalModule(HostModule):
    """Class for running non inline modules"""

    # pylint: disable=too-many-arguments
    def __init__(self, host, tmpdir, test_name, module_config, basedir="/"):
        super().__init__(host, tmpdir, test_name, module_config)
        self.log = None
        self.host = None
        self.pipe = None
        self.basedir = basedir
        self.external_subnets = self.runner.config.get('external_subnets', [])

    @abc.abstractmethod
    def _get_module_class(self):
        pass

    def start(self, port, params, callback, finish_hook):
        """Start the external module"""
        super().start(port, params, callback, finish_hook)
        cls = self._get_module_class()
        env_vars = self._get_env_vars(params)
        vol_maps = self._get_vol_maps(params)

        try:
            host = self.runner.add_host(self.host_name, port=port, cls=cls, env_vars=env_vars,
                                        vol_maps=vol_maps, tmpdir=self.tmpdir)
            self.host = host
        except Exception as e:
            # pylint: disable=no-member
            raise wrappers.DaqException(e)

        try:
            pipe = host.activate(log_name=None)
            # For devcies with ips that are not in the same subnet as test hosts' ips.
            host_ip = self._get_host_ip(params)
            if host.intf() and host_ip:
                host.cmd('ip addr add %s dev %s' % (host_ip, host.intf()))
            self.log = host.open_log()
            if self._should_raise_test_exception('initialize'):
                LOGGER.error('%s inducing initialization failure', self)
                raise Exception('induced initialization failure')
            self.runner.monitor_stream(self.host_name, pipe.stdout, copy_to=self.log,
                                       hangup=self._complete,
                                       error=self._error)
            self.pipe = pipe
            if self._should_raise_test_exception('callback'):
                LOGGER.error('%s will induce callback failure', self)
                # Closing this now will cause error when attempting to write output.
                self.log.close()
        except Exception as e:
            host.terminate()
            self.runner.remove_host(host)
            self.host = None
            if self.pipe:
                self.runner.monitor_forget(self.pipe.stdout)
                self.pipe = None
            raise e
        LOGGER.info("%s running", self)

    def terminate(self):
        """Forcibly terminate this module"""
        LOGGER.info("%s terminating", self)
        return self._finalize()

    def _get_host_ip(self, params):
        target_subnet = ip_network(params['target_ip'])
        if not target_subnet.overlaps(self.runner.network.get_subnet()):
            for subnet_spec in self.external_subnets:
                subnet = ip_network(subnet_spec['subnet'])
                if target_subnet.overlaps(subnet):
                    target_ip = ip_address(params['target_ip'])
                    new_ip = target_ip + (-1 if target_ip == subnet.broadcast_address - 1 else 1)
                    return "%s/%s" % (str(new_ip), subnet.prefixlen)
        return None

    def _get_env_vars(self, params):
        def opt_param(key):
            return params.get(key) or ''  # Substitute empty string for None

        env_vars = [
            ("TARGET_NAME", self.host_name),
            ("TARGET_IP", params['target_ip']),
            ("TARGET_MAC", params['target_mac']),
            ("TARGET_PORT", opt_param('target_port')),
            ("GATEWAY_IP", params['gateway_ip']),
            ("GATEWAY_MAC", params['gateway_mac']),
            ("LOCAL_IP", opt_param('local_ip')),
        ]
        return env_vars

    def _get_vol_maps(self, params):
        vol_maps = [(params['scan_base'], os.path.join(self.basedir, "scans"))]
        kinds = ('inst', 'port', 'device', 'type', 'gw')
        maps = list(map(lambda kind: self._map_if_exists(params, kind), kinds))
        vol_maps.extend(filter(lambda vol_map: vol_map, maps))
        return vol_maps

    def _map_if_exists(self, params, kind):
        base = params.get('%s_base' % kind)
        if base and os.path.exists(base):
            abs_base = os.path.abspath(base)
            dst = os.path.join(self.basedir, 'config', kind)
            LOGGER.debug('%s mapping %s to %s', self, abs_base, dst)
            return (abs_base, dst)
        return None

    def _error(self, exception):
        LOGGER.error('%s test host error: %s', self, str(exception))
        if self._finalize() is None:
            LOGGER.warning('%s already terminated.', self)
        else:
            self.callback(exception=exception)

    def _finalize(self):
        assert self.host, 'test host %s already finalized' % self
        if self._finish_hook:
            self._finish_hook()
        self.runner.remove_host(self.host)
        if self.pipe:
            self.runner.monitor_forget(self.pipe.stdout)
            self.pipe = None
        return_code = self.host.terminate()
        LOGGER.info('%s test host finalize %s', self, return_code)
        self.host = None
        self.log.close()
        self.log = None
        if self._should_raise_test_exception('finalize'):
            LOGGER.error('%s inducing finalize failure', self)
            raise Exception('induced finalize failure')
        return return_code

    def _should_raise_test_exception(self, trigger_value):
        key = "%s_%s" % (self.test_name, self.device.mac.replace(':', ''))
        return self.runner.config.get('fail_module', {}).get(key) == trigger_value

    def _complete(self):
        try:
            assert self.pipe, 'complete without active pipe'
            self.pipe = None
            return_code = self._finalize()
            exception = None
        except Exception as e:
            return_code = -1
            exception = e
            LOGGER.exception(e)
        delay = (datetime.datetime.now() - self.start_time).total_seconds()
        LOGGER.debug("%s test host complete, return=%d (%s)",
                     self, return_code, exception)
        if return_code:
            LOGGER.info("%s failed %ss: %s %s",
                        self, delay, return_code, exception)
        else:
            LOGGER.info("%s passed %ss",
                        self, delay)
        self.callback(return_code=return_code, exception=exception)

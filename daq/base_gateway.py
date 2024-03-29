"""Gateway module for device testing"""

from abc import ABC, abstractmethod
import datetime
from ipaddress import ip_address, ip_network
import os
import shutil
from subprocess import PIPE
from typing import Callable, List

import netaddr
from clib.mininet_test_util import DEVNULL

import logger
from env import DAQ_RUN_DIR

LOGGER = logger.get_logger('gateway')

DEFAULT_TEST_HOSTS = 8

class BaseGateway(ABC):
    """Gateway collection class for managing testing services"""

    GATEWAY_OFFSET = 0
    FAKE_HOST_OFFSET = 1
    TEST_OFFSET_START = 2
    _PING_RETRY_COUNT = 5

    TEST_IP_FORMAT = '192.168.84.%d'

    def __init__(self, runner, name, port_set, env_params=None):
        self.name = name
        self.runner = runner
        assert port_set > 0, 'port_set %d, must be > 0' % port_set
        self.port_set = port_set
        self.fake_target = None
        self.host = None
        self.host_intf = None
        self.fake_host = None
        self.tmpdir = None
        self.targets = {}
        self.test_ports = set()
        self.ready = set()
        self.activated = False
        self.result_linger = False
        self.dhcp_monitor = None
        is_native = bool(self.runner.run_trigger.get('native_vlan'))
        max_hosts = self.runner.run_trigger.get('max_hosts') or DEFAULT_TEST_HOSTS
        num_host_ports = max_hosts if is_native else DEFAULT_TEST_HOSTS
        self._gw_set_size = num_host_ports + self.TEST_OFFSET_START
        self._env_params = env_params
        self._ext_intf = env_params.get('ext_intf') if env_params else None
        self._is_native = bool(self._ext_intf)

    def initialize(self):
        """Initialize the gateway host"""
        try:
            self._initialize()
        except Exception as e:
            LOGGER.error(
                'Gateway initialization failed, terminating: %s', str(e))
            self.terminate()
            raise

    def _initialize(self):
        host_name = 'gw%02d' % self.port_set
        host_port = 1 if self._is_native else self._switch_port(self.GATEWAY_OFFSET)
        LOGGER.info('Initializing gateway %s as %s/%d',
                    self.name, host_name, host_port)
        self.tmpdir = self._setup_tmpdir(host_name)
        cls = self._get_host_class()
        env_vars = self._get_env_vars()
        LOGGER.info('host env vars: %s', env_vars)
        vol_maps = [os.path.abspath(os.path.join(DAQ_RUN_DIR, 'config')) + ':/config/inst']
        host = self.runner.add_host(host_name, port=host_port, cls=cls, tmpdir=self.tmpdir,
                                    vol_maps=vol_maps, env_vars=env_vars)
        self.host = host
        host.activate()
        self.host_intf = self.runner.get_host_interface(host)
        LOGGER.info("Added networking host %s on port %d at %s as %s",
                    host_name, host_port, host.IP(), self.host_intf)

        if self._is_native:
            self._move_intf_to_host(self._ext_intf, host)
            return

        fake_name = 'fake%02d' % self.port_set
        fake_port = self._switch_port(self.FAKE_HOST_OFFSET)
        fake_host = self.runner.add_host(fake_name, port=fake_port)
        # Fake host does not use DHCP, so need to set default route manually.
        fake_host.cmd('route add -net 0.0.0.0 gw %s' % host.IP())
        self.fake_host = fake_host
        LOGGER.info("Added fake target %s on port %d at %s",
                    fake_name, fake_port, fake_host.IP())

        self.fake_target = self.TEST_IP_FORMAT % self.port_set
        LOGGER.debug('Adding fake target at %s to %s',
                     self.fake_target, self.host_intf)
        host.cmd('ip addr add %s dev %s' % (self.fake_target, self.host_intf))

        ping_retry = self._PING_RETRY_COUNT
        while not self._ping_test(self.host, self.fake_host):
            ping_retry -= 1
            LOGGER.info('Gateway %s warmup failed at %s with %d',
                        host_name, datetime.datetime.now(), ping_retry)
            assert ping_retry, 'warmup ping failure'

        assert self._ping_test(self.host, fake_host), 'fake ping failed'
        assert self._ping_test(fake_host, host), 'host ping failed'
        assert self._ping_test(fake_host, self.fake_target), 'fake ping failed'
        assert self._ping_test(
            self.host, fake_host, src_addr=self.fake_target), 'reverse ping failed'

    def _get_env_vars(self):
        env_vars = []
        if self._env_params:
            for key, value in self._env_params.items():
                env_vars.append(f'{key.upper()}={value or ""}')
        return env_vars

    def _move_intf_to_host(self, iface, host):
        result = self.runner.network.pri.cmd('ip link set %s netns %s' % (iface, host.pid))
        LOGGER.info('Move iface %s into %s/%s: %s', iface, host, host.pid, result)

    @abstractmethod
    def _get_host_class(self):
        pass

    def activate(self):
        """Mark this gateway as activated once all hosts are present"""
        self.activated = True

    def get_base_dir(self):
        """Return the gateways base directory for instance files"""
        return os.path.abspath(self.tmpdir)

    def allocate_test_port(self):
        """Get the test port to use for this gateway setup"""
        test_port = self._switch_port(self.TEST_OFFSET_START)
        while test_port in self.test_ports:
            test_port = test_port + 1
        limit_port = self._switch_port(self._gw_set_size)
        assert test_port < limit_port, 'no test ports available'
        self.test_ports.add(test_port)
        return test_port

    def release_test_port(self, test_port):
        """Release the given port from the gateway"""
        assert test_port in self.test_ports, 'test port not allocated'
        self.test_ports.remove(test_port)

    def _switch_port(self, offset):
        return self.port_set * self._gw_set_size + offset

    def _is_target_expected(self, target):
        return target and target['mac'] in self.targets

    def _dhcp_callback(self, state, target, exception=None):
        if exception:
            LOGGER.error('Gateway DHCP exception %s', exception)
        expected = self._is_target_expected(target)
        use_state = 'NEW' if (self._is_native and not expected) else state
        if expected or self._is_native or exception:
            self.runner.ip_notify(use_state, target, self, exception=exception)

    def _setup_tmpdir(self, base_name):
        tmpdir = os.path.join(DAQ_RUN_DIR, base_name)
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)
        return tmpdir

    def attach_target(self, device):
        """Attach the given target to this gateway; return number of attached targets."""
        assert device.mac not in self.targets, 'target %s already attached to gw' % device
        LOGGER.info('Attaching target %s to gateway %s group %s',
                    device, self.port_set, self.name)
        self.targets[device.mac] = device
        return len(self.targets)

    def detach_target(self, device):
        """Detach the given target from this gateway; return number of remaining targets."""
        assert device.mac in self.targets, 'target %s not attached to gw' % device
        LOGGER.info('Detaching target %s from gateway %s group %s: %s',
                    device, self.port_set, self.name, list(self.targets.keys()))
        del self.targets[device.mac]
        return len(self.targets)

    def target_ready(self, device):
        """Mark a target ready, and return set of ready targets"""
        if device not in self.ready:
            LOGGER.info('Ready target %s from gateway group %s',
                        device, self.name)
            self.ready.add(device)
        return self.ready

    def get_targets(self):
        """Return the host targets associated with this gateway"""
        return self.targets.values()

    def get_all_gw_ports(self):
        """Return all ports associated with gateway"""
        base_port = self._switch_port(0)
        limit_port = self._switch_port(self._gw_set_size)
        return list(range(base_port, limit_port))

    def get_possible_test_ports(self):
        """Return test ports associated with gateway"""
        test_port = self._switch_port(self.TEST_OFFSET_START)
        limit_port = self._switch_port(self._gw_set_size)
        return list(range(test_port, limit_port))

    def terminate(self):
        """Terminate this instance"""
        assert not self.targets, 'gw %s has targets %s' % (
            self.name, self.targets)
        LOGGER.info('Terminating gateway %d/%s', self.port_set, self.name)
        if self.dhcp_monitor:
            self.dhcp_monitor.cleanup()
        if self.host:
            try:
                self.host.terminate()
                self.runner.remove_host(self.host)
                self.host = None
            except Exception as e:
                LOGGER.error('Gateway %s terminating host: %s', self.name, e)
                LOGGER.exception(e)
        if self.fake_host:
            try:
                self.fake_host.terminate()
                self.runner.remove_host(self.fake_host)
                self.fake_host = None
            except Exception as e:
                LOGGER.error('Gateway %s terminating fake_host: %s', self.name, e)
                LOGGER.exception(e)

    def _get_scan_interface(self):
        return self.host, self.host_intf

    def _discover_host_hangup_callback(self, mac, log_fd, log_file, scan_callback):
        def process_line(line):
            sections = [section for section in line.split('\t') if section]
            if len(sections) >= 2:
                try:
                    device_ip = ip_address(sections[0])
                    if netaddr.EUI(mac) == netaddr.EUI(sections[1]):
                        return device_ip
                except (ValueError, netaddr.core.AddrFormatError):
                    pass
            return None
        log_fd.close()
        with open(log_file, 'r') as fd:
            lines = fd.read().split('\n')
            for line in lines:
                device_ip = process_line(line)
                if device_ip:
                    LOGGER.info('Host discovery for %s completed. Found ip %s.',
                                mac, device_ip)
                    return scan_callback(device_ip)
        LOGGER.info('Host discovery for %s completed. Found no ip.', mac)
        scan_callback(None)

    def discover_host(self, mac: str, all_subnets: List[ip_network], host_callback: Callable):
        """Discovers a host using arp-scan in a list of subnets."""
        cmd = 'arp-scan --retry=2 --bandwidth=512K --interface=%s --destaddr=%s -s %s %s'
        host, intf = self._get_scan_interface()
        scans = self.runner.run_trigger.get('arp_scan_count') or 2
        if scans <= 0:
            return
        subnets = list(all_subnets)
        LOGGER.info('Starting host discovery for %s', mac)

        def scan_callback(device_ip):
            nonlocal scans
            if device_ip:
                scans = 0
                host_callback(device_ip)
            else:
                recursive_discover()

        def recursive_discover():
            nonlocal subnets, scans
            if not subnets:
                if scans > 0:
                    scans -= 1
                    subnets = list(all_subnets)
                else:
                    host_callback(None)
                    return
            subnet = subnets.pop(0)
            hosts = subnet.hosts()
            address = next(hosts)
            # This handles the case where the local IP conflicts with the remote.
            # Not really a good general solution, but works in many cases.
            # TODO: Generalize a bit more to (e.g.) pick a random src IP.
            if scans % 2:
                address = next(hosts)
            log_file = os.path.join(self.tmpdir, str(subnet).replace('/', '_'))
            log_fd = open(log_file, 'w')
            LOGGER.info('Scanning %s subnet %s from %s for %s', scans, subnet, address, mac)
            host.cmd('ip addr add %s/%s dev %s' % (str(address), subnet.prefixlen, intf))
            full_cmd = cmd % (intf, mac, str(address), str(subnet))
            active_pipe = host.popen(full_cmd, stdin=DEVNULL, stdout=PIPE, env=os.environ)
            self.runner.monitor_stream(self.name, active_pipe.stdout, copy_to=log_fd,
                                       hangup=lambda: self._discover_host_hangup_callback(
                                           mac, log_fd, log_file, scan_callback))

        recursive_discover()

    def _ping_test(self, src, dst, src_addr=None):
        return self.runner.ping_test(src, dst, src_addr=src_addr)

    def __repr__(self):
        return 'Gateway group %s set %d' % (self.name, self.port_set)

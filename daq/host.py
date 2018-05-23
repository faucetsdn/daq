"""Represent a device-under-test"""

import logging
import os
import random
import re
import shutil
import time

from clib.docker_host import MakeDockerHost

from clib.tcpdump_helper import TcpdumpHelper

LOGGER = logging.getLogger('host')

class ConnectedHost():
    """Class managing a device-under-test"""

    NETWORKING_OFFSET = 0
    DUMMY_OFFSET = 1
    TEST_OFFSET = 2

    TEST_IP_FORMAT = '192.168.84.%d'
    MONITOR_SCAN_SEC = 20
    IMAGE_NAME_FORMAT = 'daq/test_%s'
    CONTAINER_PREFIX = 'daq'

    DHCP_MAC_PATTERN = '> ([0-9a-f:]+), ethertype IPv4'
    DHCP_IP_PATTERN = 'Your-IP ([0-9.]+)'
    DHCP_PATTERN = '(%s)|(%s)' % (DHCP_MAC_PATTERN, DHCP_IP_PATTERN)
    DHCP_TIMEOUT_SEC = 240
    DHCP_THRESHHOLD_SEC = 20

    ERROR_STATE = -1
    INIT_STATE = 0
    STARTUP_STATE = 1
    ACTIVE_STATE = 2
    DHCP_STATE = 3
    BASE_STATE = 4
    MONITOR_STATE = 6
    READY_STATE = 7
    TESTING_STATE = 8
    DONE_STATE = 9

    TEST_LIST = ['pass', 'fail', 'ping', 'bacnet', 'nmap', 'mudgee']
    TEST_ORDER = ['startup', 'sanity', 'dhcp', 'base',
                  'monitor'] + TEST_LIST + ['finish', 'info', 'timer']

    runner = None
    port_set = None
    pri_base = None
    target_ip = None
    target_mac = None
    networking = None
    dummy = None
    state = ERROR_STATE
    results = None
    running_test = None
    remaining_tests = None
    run_id = None
    test_name = 'unknown'
    test_start = None
    tcp_monitor = None
    dhcp_traffic = None
    docker_log = None
    fake_target = None
    docker_host = None

    def __init__(self, runner, port_set):
        self.runner = runner
        self.port_set = port_set
        self.pri_base = port_set * 10
        self.tmpdir = os.path.join('inst', 'run-port-%02d' % self.port_set)
        self.run_id = '%06x' % int(time.time())
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        self.scan_base = os.path.abspath(os.path.join(self.tmpdir, 'scans'))
        self._state_transition(self.INIT_STATE)
        self.results = {}
        self.record_result('startup', state='run')
        self.dhcp_try = 1
        LOGGER.info('Set %d created.', port_set)
        # There is a race condition here with ovs assigning ports, so wait a bit.
        time.sleep(2)
        self.remaining_tests = list(self.TEST_LIST)
        networking_name = 'gw%02d' % self.port_set
        networking_port = self.pri_base + self.NETWORKING_OFFSET
        LOGGER.debug("Adding networking host on port %d", networking_port)
        cls = MakeDockerHost('daq/networking', prefix=self.CONTAINER_PREFIX)
        try:
            self.networking = self.runner.add_host(networking_name, port=networking_port,
                                                   cls=cls, tmpdir=self.tmpdir)
            self.record_result('startup')
        except:
            self._terminate(trigger=False)
            raise

    def _state_transition(self, target, expected=None):
        message = 'state was %d expected %d' % (self.state, expected)
        assert expected is None or self.state == expected, message
        LOGGER.debug('Set %d state %s -> %d', self.port_set, self.state, target)
        self.state = target

    def _activate(self):
        self._state_transition(self.STARTUP_STATE, self.INIT_STATE)
        LOGGER.info('Set %d activating.', self.port_set)

        if not os.path.exists(self.scan_base):
            os.makedirs(self.scan_base)

        try:
            self.record_result('sanity', state='run')
            networking = self.networking
            networking.activate()
            self._startup_scan()

            dummy_name = 'dummy%02d' % self.port_set
            dummy_port = self.pri_base + self.DUMMY_OFFSET
            self.dummy = self.runner.add_host(dummy_name, port=dummy_port)
            dummy = self.dummy

            self.fake_target = self.TEST_IP_FORMAT % random.randint(10, 99)
            LOGGER.debug('Adding fake target at %s', self.fake_target)
            networking.cmd('ip addr add %s dev %s' %
                           (self.fake_target, networking.switch_link.intf2))

            # Dummy doesn't use DHCP, so need to set default route manually.
            dummy.cmd('route add -net 0.0.0.0 gw %s' % networking.IP())

            assert self._ping_test(networking, dummy), 'ping failed'
            assert self._ping_test(dummy, networking), 'ping failed'
            assert self._ping_test(dummy, self.fake_target), 'ping failed'
            assert self._ping_test(networking, dummy, src_addr=self.fake_target), 'ping failed'
            self.record_result('sanity')
            self._state_transition(self.ACTIVE_STATE, self.STARTUP_STATE)
        except Exception as e:
            LOGGER.error('Set %d sanity error: %s', self.port_set, e)
            LOGGER.exception(e)
            self.record_result('sanity', exception=e)
            self._terminate()

    def _terminate(self, trigger=True):
        LOGGER.info('Set %d terminate, trigger %s', self.port_set, trigger)
        self._state_transition(self.ERROR_STATE)
        self._dhcp_cleanup()
        self._monitor_cleanup()
        if self.networking:
            try:
                self.networking.terminate()
                self.runner.remove_host(self.networking)
                self.networking = None
            except Exception as e:
                LOGGER.error('Set %d terminating networking: %s', self.port_set, e)
                LOGGER.exception(e)
        if self.dummy:
            try:
                self.dummy.terminate()
                self.runner.remove_host(self.dummy)
                self.dummy = None
            except Exception as e:
                LOGGER.error('Set %d terminating dummy: %s', self.port_set, e)
                LOGGER.exception(e)
        if self.running_test:
            try:
                self.running_test.terminate()
                self.runner.remove_host(self.running_test)
                self.running_test = None
            except Exception as e:
                LOGGER.error('Set %d terminating test: %s', self.port_set, e)
                LOGGER.exception(e)
        if trigger:
            self.runner.target_set_complete(self)

    def idle_handler(self):
        """Trigger events from idle state"""
        if self.state == self.INIT_STATE:
            self._activate()
        elif self.state == self.ACTIVE_STATE:
            self._dhcp_monitor()
        elif self.state == self.BASE_STATE:
            self._base_start()

    def _ping_test(self, src, dst, src_addr=None):
        src_name = src if isinstance(src, str) else src.name
        src_ip = src if isinstance(src, str) else src.IP()
        from_msg = ' from %s' % src_addr if src_addr else ''
        LOGGER.info("Set %d ping test %s->%s%s", self.port_set, dst.name, src_name, from_msg)
        failure = "ping FAILED"
        assert src_ip != "0.0.0.0", "IP address not assigned, can't ping"
        src_opt = '-I %s' % src_addr if src_addr else ''
        try:
            output = dst.cmd('ping -c2', src_opt, src_ip, '> /dev/null 2>&1 || echo ', failure)
            return output.strip() != failure
        except Exception as e:
            LOGGER.info('Set %d ping failure: %s', self.port_set, e)
            return False

    def _startup_scan(self):
        assert not self.tcp_monitor, 'tcp_monitor already active'
        LOGGER.debug('Set %d startup pcap start', self.port_set)
        startup_file = os.path.join('/tmp', 'startup.pcap')
        tcp_filter = ''
        self.tcp_monitor = TcpdumpHelper(self.networking, tcp_filter, packets=None,
                                         timeout=None, pcap_out=startup_file, blocking=False)
        monitor = self.runner.monitor
        monitor.monitor('tcpdump', self.tcp_monitor.stream(), self.tcp_monitor.next_line,
                        hangup=lambda: self._monitor_error(Exception('startup scan hangup')),
                        error=self._monitor_error)

    def _dhcp_monitor(self):
        self._state_transition(self.DHCP_STATE, self.ACTIVE_STATE)
        self.record_result('dhcp', state='run')
        LOGGER.info('Set %d waiting for dhcp reply from %s...', self.port_set, self.networking.name)
        tcp_filter = "src port 67"
        self.dhcp_traffic = TcpdumpHelper(self.networking, tcp_filter, packets=None,
                                          timeout=self.DHCP_TIMEOUT_SEC, blocking=False)
        monitor = self.runner.monitor
        monitor.monitor(self.networking.name, self.dhcp_traffic.stream(), self._dhcp_line,
                        hangup=self._dhcp_hangup, error=self._dhcp_error)

    def _dhcp_line(self):
        dhcp_line = self.dhcp_traffic.next_line()
        if not dhcp_line:
            return
        match = re.search(self.DHCP_PATTERN, dhcp_line)
        if match:
            self.target_ip = match.group(4)
            if self.target_ip:
                message = 'dhcp IP %s found, but no MAC address: %s' % (self.target_ip, dhcp_line)
                assert self.target_mac, message
                self._dhcp_success()
            else:
                self.target_mac = match.group(2)

    def _dhcp_cleanup(self, forget=True):
        if self.dhcp_traffic:
            if forget:
                self.runner.monitor_forget(self.dhcp_traffic.stream())
            self.dhcp_traffic.terminate()
            self.dhcp_traffic = None

    def _dhcp_success(self):
        self._dhcp_cleanup()
        delta = int(time.time()) - self.test_start
        LOGGER.info('Set %d received dhcp reply after %ds: %s is at %s',
                    self.port_set, delta, self.target_mac, self.target_ip)
        weak_result = delta > self.DHCP_THRESHHOLD_SEC
        state = 'weak' if weak_result else None
        self.record_result('dhcp', info=self.target_mac, ip=self.target_ip, state=state)
        self._state_transition(self.BASE_STATE, self.DHCP_STATE)

    def _dhcp_hangup(self):
        try:
            raise Exception('dhcp hangup')
        except Exception as e:
            self._dhcp_error(e)

    def _dhcp_error(self, e):
        LOGGER.error('Set %d dhcp error: %s', self.port_set, e)
        self.record_result('dhcp', exception=e)
        self._dhcp_cleanup(forget=False)
        self._state_transition(self.ERROR_STATE, self.DHCP_STATE)
        self.runner.target_set_error(self.port_set, e)
        self._terminate()

    def _base_start(self):
        try:
            self._base_tests()
            self._monitor_cleanup()
            LOGGER.info('Set %d done with base.', self.port_set)
            self._monitor_scan()
        except Exception as e:
            self._monitor_cleanup()
            self._monitor_error(e)

    def _monitor_cleanup(self, forget=True):
        if self.tcp_monitor:
            LOGGER.debug('Set %d monitor scan cleanup (forget=%s)', self.port_set, forget)
            if forget:
                self.runner.monitor.forget(self.tcp_monitor.stream())
            self.tcp_monitor.terminate()
            self.tcp_monitor = None

    def _monitor_error(self, e):
        LOGGER.error('Set %d monitor error: %s', self.port_set, e)
        self._monitor_cleanup(forget=False)
        self.record_result(self.test_name, exception=e)
        self.runner.target_set_error(self.port_set, e)

    def _monitor_scan(self):
        self._state_transition(self.MONITOR_STATE, self.BASE_STATE)
        self.record_result('monitor', time=self.MONITOR_SCAN_SEC, state='run')
        LOGGER.info('Set %d background scan for %d seconds...',
                    self.port_set, self.MONITOR_SCAN_SEC)
        intf_name = self.runner.sec_name
        monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
        tcp_filter = 'vlan %d' % self.pri_base
        assert not self.tcp_monitor, 'tcp_monitor already active'
        self.tcp_monitor = TcpdumpHelper(self.runner.pri, tcp_filter, packets=None,
                                         intf_name=intf_name,
                                         timeout=self.MONITOR_SCAN_SEC,
                                         pcap_out=monitor_file, blocking=False)
        monitor = self.runner.monitor
        monitor.monitor('tcpdump', self.tcp_monitor.stream(), self.tcp_monitor.next_line,
                        hangup=self._monitor_complete, error=self._monitor_error)

    def _monitor_complete(self):
        LOGGER.info('Set %d monitor scan complete', self.port_set)
        self._monitor_cleanup(forget=False)
        self.record_result('monitor')
        self._state_transition(self.READY_STATE, self.MONITOR_STATE)
        self._run_next_test()

    def _base_tests(self):
        self.record_result('base', state='run')
        if not self._ping_test(self.networking, self.target_ip):
            LOGGER.debug('Set %d warmup ping failed', self.port_set)
        try:
            assert self._ping_test(self.networking, self.target_ip), 'simple ping failed'
            assert self._ping_test(self.networking, self.target_ip,
                                   src_addr=self.fake_target), 'target ping failed'
        except:
            self._monitor_cleanup()
            raise
        self.record_result('base')

    def _run_next_test(self):
        if self.remaining_tests:
            self._docker_test(self.remaining_tests.pop(0))
        else:
            self._state_transition(self.DONE_STATE, self.READY_STATE)
            self.record_result('finish')
            self._terminate()

    def _docker_test(self, test_name):
        LOGGER.info('Set %d running docker test %s', self.port_set, test_name)
        self.record_result(test_name, state='run')
        port = self.pri_base + self.TEST_OFFSET
        gateway = self.networking
        image = self.IMAGE_NAME_FORMAT % test_name
        host_name = '%s%02d' % (test_name, self.port_set)

        env_vars = ["TARGET_NAME=" + host_name,
                    "TARGET_IP=" + self.target_ip,
                    "TARGET_MAC=" + self.target_mac,
                    "GATEWAY_IP=" + gateway.IP(),
                    "GATEWAY_MAC=" + gateway.MAC()]
        vol_maps = [self.scan_base + ":/scans"]

        LOGGER.debug("Set %d running docker test %s", self.port_set, image)
        cls = MakeDockerHost(image, prefix=self.CONTAINER_PREFIX)
        host = self.runner.add_host(host_name, port=port, cls=cls, env_vars=env_vars,
                                    vol_maps=vol_maps, tmpdir=self.tmpdir)
        try:
            pipe = host.activate(log_name=None)
            self.docker_log = host.open_log()
            self._state_transition(self.TESTING_STATE, self.READY_STATE)
            self.runner.monitor.monitor(host_name, pipe.stdout, copy_to=self.docker_log,
                                        hangup=self._docker_complete,
                                        error=self._docker_error)
        except:
            host.terminate()
            self.runner.remove_host(host)
            raise
        self.docker_host = host
        return host

    def _docker_error(self, e):
        LOGGER.error('Set %d docker error: %s', self.port_set, e)
        self.record_result(self.test_name, exception=e)
        self._docker_finalize()
        self.runner.target_set_error(self.port_set, e)

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
        self._state_transition(self.READY_STATE, self.TESTING_STATE)
        try:
            error_code = self._docker_finalize()
            exception = None
        except Exception as e:
            error_code = -1
            exception = e
        LOGGER.debug("Set %d docker complete, return=%d (%s)", self.port_set, error_code, exception)
        self.record_result(self.test_name, code=error_code, exception=exception)
        if error_code:
            LOGGER.info("Set %d FAILED test %s with error %s: %s",
                        self.port_set, self.test_name, error_code, exception)
        else:
            LOGGER.info("Set %d PASSED test %s", self.port_set, self.test_name)
        self._run_next_test()

    def record_result(self, name, **kwargs):
        """Record a named result for this test"""
        current = int(time.time())
        if name != self.test_name:
            LOGGER.debug('Set %d starting test %s at %d', self.port_set, self.test_name, current)
            self.test_name = name
            self.test_start = current
        result = {
            'name': name,
            'runid': self.run_id,
            'started': self.test_start,
            'timestamp': current,
            'port': self.port_set
        }
        for arg in kwargs:
            result[arg] = None if kwargs[arg] is None else str(kwargs[arg])
        self.results[name] = result
        self.runner.gcp.publish_message('daq_runner', result)

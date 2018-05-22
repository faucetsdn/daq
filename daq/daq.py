#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

import logging
import math
import os
import random
import re
import shutil
import signal
import sys
import time
import traceback

from ConfigParser import ConfigParser
from StringIO import StringIO

from mininet import log as minilog
from mininet.log import LEVELS, MininetLogger
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, Host, Link
from mininet.link import Intf
from mininet.cli import CLI

from clib.docker_host import MakeDockerHost
from clib.mininet_test_topo import FaucetHostCleanup
import clib.mininet_test_util

from clib.tcpdump_helper import TcpdumpHelper
from faucet_event_client import FaucetEventClient
from stream_monitor import StreamMonitor
from host import ConnectedHost

from gcp import GcpManager

logger = logging.getLogger('daq')
altlog = logging.getLogger('mininet')


class DAQHost(FaucetHostCleanup, Host):
    """Base Mininet Host class, for Mininet-based tests."""
    pass


class DummyNode():
    def addIntf(self, node, port=None):
        pass

    def cmd(self, cmd, *args, **kwargs):
        pass


class DAQRunner():

    config = None
    net = None
    device_intfs = None
    target_sets = None
    active_ports = None
    result_sets = None
    pri = None
    sec = None
    sec_dpid = None
    sec_port = None
    sec_name = None
    gcp = None
    description = None
    version = None

    def __init__(self, config):
        self.config = config
        self.target_sets = {}
        self.result_sets = {}
        self.active_ports = {}
        self.gcp = GcpManager(self.config)
        raw_description = config.get('site_description', '')
        self.description = raw_description.strip("\"")
        self.version = os.environ['DAQ_VERSION']

    def addHost(self, name, cls=DAQHost, ip=None, env_vars=[], vol_maps=[],
                port=None, tmpdir=None):
        params = { 'ip': ip } if ip else {}
        params['tmpdir'] = os.path.join(tmpdir, 'nodes') if tmpdir else None
        params['env_vars'] = env_vars
        params['vol_maps'] = vol_maps
        host = self.net.addHost(name, cls, **params)
        try:
            logger.debug('Created host %s with pid %s/%s' % (name, host.pid, host.shell.pid))
            host.switch_link = self.net.addLink(self.pri, host, port1=port, fast=False)
            if self.net.built:
                host.configDefault()
                self.switchAttach(self.pri, host.switch_link.intf1)
        except:
            host.terminate()
            raise
        return host

    def switchAttach(self, switch, intf):
        switch.attach(intf)
        # This really should be done in attach, but currently only automatic on switch startup.
        switch.vsctl(switch.intfOpts(intf))

    def switchDelIntf(self, switch, intf):
        del switch.intfs[switch.ports[intf]]
        del switch.ports[intf]
        del switch.nameToIntf[intf.name]

    def removeHost(self, host):
        index = self.net.hosts.index(host)
        if index:
            del self.net.hosts[index]
        if host.switch_link:
            intf = host.switch_link.intf1
            self.pri.detach(intf)
            self.switchDelIntf(self.pri, intf)
            intf.delete()
            del self.net.links[self.net.links.index(host.switch_link)]

    def stopHost(self, host):
        logger.debug("Stopping host " + host.name)
        host.terminate()

    def make_device_intfs(self):
        intf_names = self.config['daq_intf'].split(',')
        intfs=[]
        for intf_name in intf_names:
            intf_name = intf_name[0:-1] if intf_name.endswith('!') else intf_name
            port_no = len(intfs) + 1
            intf = Intf(intf_name.strip(), node=DummyNode(), port=port_no)
            intf.port = port_no
            intfs.append(intf)
        return intfs

    def flush_faucet_events(self):
        logger.info('Flushing faucet event queue...')
        while self.faucet_events.next_event():
            pass

    def flap_interface_ports(self):
        if self.device_intfs:
            for device_intf in self.device_intfs:
                self.flap_interface_port(device_intf.name)

    def flap_interface_port(self, intf_name):
        if intf_name.startswith('faux') or intf_name == 'local':
            logger.info('Flapping device interface %s.' % intf_name)
            self.sec.cmd('ip link set %s down' % intf_name)
            time.sleep(0.5)
            self.sec.cmd('ip link set %s up' % intf_name)

    def create_secondary(self):
        self.sec_port = int(self.config['ext_port'] if 'ext_port' in self.config else 47)
        if 'ext_dpid' in self.config:
            self.sec_dpid = int(self.config['ext_dpid'], 0)
            self.sec_name = self.config['ext_intf']
            logger.info('Configuring external secondary with dpid %s on intf %s' % (self.sec_dpid, self.sec_name))
            sec_intf = Intf(self.sec_name, node=DummyNode(), port=1)
            self.pri.addIntf(sec_intf, port=1)
        else:
            self.sec_dpid = 2
            logger.info('Creating ovs secondary with dpid/port %s/%d' % (self.sec_dpid, self.sec_port))
            self.sec = self.net.addSwitch('sec', dpid=str(self.sec_dpid), cls=OVSSwitch)

            link = self.net.addLink(self.pri, self.sec, port1=1,
                    port2=self.sec_port, fast=False)
            logger.info('Added switch link %s <-> %s' % (link.intf1.name, link.intf2.name))
            self.sec_name = link.intf2.name

    def send_heartbeat(self):
        self.gcp.publish_message('daq_runner', {
            'name': 'status',
            'tests': ConnectedHost.TEST_ORDER,
            'ports': self.active_ports.keys(),
            'description': self.description,
            'version': self.version,
            'timestamp': int(time.time()),
        })

    def initialize(self):
        self.send_heartbeat()

        logger.debug("Creating miniet...")
        self.net = Mininet()

        logger.debug("Adding switches...")
        self.pri = self.net.addSwitch('pri', dpid='1', cls=OVSSwitch)

        logger.info("Starting faucet...")
        output = self.pri.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            logger.info('Faucet output: %s' % output)
            assert False, 'Faucet startup failed'

        self.create_secondary()

        targetIp = "127.0.0.1"
        logger.debug("Adding controller at %s" % targetIp)
        controller = self.net.addController('controller', controller=RemoteController,
                ip=targetIp, port=6633 )

        logger.info("Starting mininet...")
        self.net.start()

        if self.sec:
            self.device_intfs = self.make_device_intfs()
            for device_intf in self.device_intfs:
                logger.info("Attaching device interface %s on port %d." %
                        (device_intf.name, device_intf.port))
                self.sec.addIntf(device_intf, port=device_intf.port)
                self.switchAttach(self.sec, device_intf)

        logger.debug("Attaching event channel...")
        self.faucet_events = FaucetEventClient()
        self.faucet_events.connect(os.getenv('FAUCET_EVENT_SOCK'))

        logger.info("Waiting for system to settle...")
        time.sleep(3)

        logger.debug('Done with initialization')

    def cleanup(self):
        try:
            logger.debug("Stopping faucet...")
            self.pri.cmd('docker kill daq-faucet')
        except Exception as e:
            logger.error('Exception: %s' % e)
        try:
            logger.debug("Stopping mininet...")
            self.net.stop()
        except Exception as e:
            logger.error('Exception: %s' % e)
        logger.info("Done with runner.")

    def handle_faucet_event(self):
        target_dpid = int(self.sec_dpid)
        while True:
            event = self.faucet_events.next_event()
            logger.debug('Faucet event %s' % event)
            if not event:
                break
            (dpid, port, active) = self.faucet_events.as_port_state(event)
            logger.debug('Port state is dpid %s port %s active %s' % (dpid, port, active))
            if dpid == target_dpid:
                if active:
                    if port >= self.sec_port:
                        logger.debug('Ignoring out-of-range port %d' % port)
                    else:
                        self.active_ports[port] = True
                        self.trigger_target_set(port)
                else:
                    if port in self.active_ports:
                        del self.active_ports[port]
                    self.cancel_target_set(port)

    def handle_system_idle(self):
        for target_set in self.target_sets.values():
            try:
                target_set.idle_handler()
            except Exception as e:
                self.target_set_error(target_set.port_set, e)
        if not self.event_start and not self.one_shot:
            for port_set in self.active_ports.keys():
                if self.active_ports[port_set] and not port_set in self.target_sets:
                    self.trigger_target_set(port_set)

    def loop_hook(self):
        states = {}
        for key in self.target_sets.keys():
            states[key] = self.target_sets[key].state
        logger.debug('Active target sets/state: %s' % states)

    def terminate(self):
        for key in self.target_sets.keys():
            self.target_sets[key].terminate()

    def main_loop(self):
        self.one_shot = self.config.get('s')
        self.flap_ports = self.config.get('f')
        self.event_start = self.config.get('e')

        if self.flap_ports:
            self.flap_interface_ports()

        self.exception = False
        try:
            self.monitor = StreamMonitor(idle_handler=lambda: self.handle_system_idle(),
                                         loop_hook=lambda: self.loop_hook())
            self.monitor.monitor('faucet', self.faucet_events.sock, lambda: self.handle_faucet_event())
            if self.event_start:
                self.flush_faucet_events()
            logger.info('Entering main event loop.')
            self.monitor.event_loop()
        except Exception as e:
            logger.error('Event loop exception: %s' % e)
            logger.exception(e)
            self.exception = e
        except KeyboardInterrupt as e:
            logger.error('Keyboard Interrupt')
            logger.exception(e)

        if not self.one_shot:
            logger.info('Dropping into interactive command line')
            CLI(self.net)

        self.terminate()

    def trigger_target_set(self, port_set):
        assert not port_set in self.target_sets, 'target set %d already exists' % port_set
        try:
            logger.debug('Trigger target set %d' % port_set)
            self.target_sets[port_set] = ConnectedHost(self, port_set)
            self.send_heartbeat()
        except Exception as e:
            self.target_set_error(port_set, e)

    def target_set_error(self, port_set, e):
        logger.info('Set %d exception: %s' % (port_set, e))
        logger.exception(e)
        if port_set in self.target_sets:
            target_set = self.target_sets[port_set]
            target_set.record_result(target_set.test_name, exception=e)
            target_set.terminate(trigger=False)
            self.target_set_complete(target_set)
        else:
            self.target_set_finalize(port_set, { 'exception': str(e) })

    def target_set_complete(self, target_set):
        port_set = target_set.port_set
        results = target_set.results
        self.cancel_target_set(port_set)
        self.target_set_finalize(port_set, results)

    def target_set_finalize(self, port_set, results):
        logger.info('Set %d complete, %d results' % (port_set, len(results)))
        self.result_sets[port_set] = results
        logger.info('Remaining sets: %s' % self.target_sets.keys())

    def cancel_target_set(self, port_set):
        if port_set in self.target_sets:
            target_set = self.target_sets[port_set]
            del self.target_sets[port_set]
            target_set.terminate(trigger=False)
            logger.info('Set %d cancelled.' % port_set)
            if not self.target_sets and self.one_shot:
                self.monitor.forget(self.faucet_events.sock)

    def combine_results(self):
        results=[]
        for result_set_key in self.result_sets:
            result_set = self.result_sets[result_set_key]
            for result_key in result_set:
                result = result_set[result_key]
                exception = 'exception' if 'exception' in result and result['exception'] != None else None
                code = int(result['code']) if 'code' in result else 0
                name = result['name']
                status = exception if exception else code if name != 'fail' else not code
                if status != 0:
                    results.append('%02d:%s:%s' % (result_set_key, name, status))
        return results

    def finalize(self):
        failures = self.combine_results()
        if failures:
            logger.error('Test failures: %s' % failures)
        if self.exception:
            logger.error('Exiting b/c of exception: %s' % self.exception)
        if failures or self.exception:
            return 1
        return 0

def mininet_alt_logger(self, level, msg, *args, **kwargs ):
    stripped = msg.strip()
    if stripped:
        altlog._log(level, stripped, *args, **kwargs)

def configure_logging(config):
    daq_env = config.get('daq_loglevel')
    logging.basicConfig(level=LEVELS.get(daq_env, LEVELS['info']))

    mininet_env = config.get('mininet_loglevel')
    minilog.setLogLevel(mininet_env if mininet_env else 'info')

    MininetLogger._log = mininet_alt_logger

def write_pid_file():
    pid = str(os.getpid())
    f = open('inst/daq.pid', 'w')
    f.write(pid)
    f.close()

def read_config_into(filename, config):
    parser = ConfigParser()
    with open(filename) as stream:
        stream = StringIO("[top]\n" + stream.read())
        parser.readfp(stream)
    for item in parser.items('top'):
        config[item[0]] = item[1]

def parse_args(args):
    config = {}
    first = True
    for arg in args:
        if first:
            first = False
        elif arg[0] == '-':
            config[arg[1:]] = True
        elif '=' in arg:
            parts = arg.split('=', 1)
            config[parts[0]] = parts[1]
        else:
            read_config_into(arg, config)
    return config


if __name__ == '__main__':
    assert os.getuid() == 0, 'Must run DAQ as root.'

    config = parse_args(sys.argv)

    configure_logging(config)

    write_pid_file()

    runner = DAQRunner(config)
    runner.initialize()
    runner.main_loop()
    runner.cleanup()
    returncode = runner.finalize()
    sys.exit(returncode)

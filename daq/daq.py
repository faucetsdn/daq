#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

from __future__ import print_function

import logging
import os

from mininet import log as minilogger
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.node import OVSBridge


from tests.faucet_mininet_test_topo import FaucetHost, FaucetSwitch

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger( __name__ )

def createNetwork():
    logging.debug("Creating miniet...")
    net = Mininet()

    logging.debug("Adding hosts...")
    h1 = net.addHost('h1', cls=FaucetHost)
    h2 = net.addHost('h2', cls=FaucetHost)

    logging.debug("Adding switch and controller...")
    s1 = net.addSwitch('s1', cls=OVSBridge)

    logging.debug("Adding links...")
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    
    logging.debug("Starting mininet...")
    net.start()

    logging.debug("Ping test h1->h2")
    print(h1.cmd( 'ping -c1', h2.IP(), '> /dev/null || echo ping FAILED' ), end='')
    logging.debug("Ping test h2->h1")
    print(h2.cmd( 'ping -c1', h1.IP(), '> /dev/null || echo ping FAILED' ), end='')
    
    CLI(net)

    logging.debug("Stopping mininet...")
    net.stop()



if __name__ == '__main__':
    minilogger.setLogLevel('info')
    if os.getuid() != 0:
        logger.debug("You are NOT root")
    elif os.getuid() == 0:
        createNetwork()

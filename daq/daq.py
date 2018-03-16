#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, Host, Node
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Link, Intf, TCLink
from mininet.topo import Topo
from mininet.util import dumpNodeConnections
from mininet.util import isShellBuiltin
from mininet.node import OVSBridge
from subprocess import call, check_output
from subprocess import Popen, PIPE, STDOUT
import logging
import os 
import time
import select
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger( __name__ )

def createNetwork():
    logging.debug("Create Miniet")
    net = Mininet(link=TCLink)
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    s1 = net.addSwitch('s1', cls=OVSBridge)
    c1 = net.addController('c1', controller=RemoteController)
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    
    logging.debug("Start Mininet")
    net.start()

    logging.debug("Ping test h1->h2")
    print h1.cmd( 'ping -c1', h2.IP(), '> /dev/null && echo OK' )
    logging.debug("Ping test h2->h1")
    print h2.cmd( 'ping -c1', h1.IP(), '> /dev/null && echo OK' )
    
    CLI(net)

    logging.debug("Stopping Mininet")
    net.stop()



if __name__ == '__main__':
    setLogLevel('info')
    if os.getuid() != 0:
        logger.debug("You are NOT root")
    elif os.getuid() == 0:
        createNetwork()

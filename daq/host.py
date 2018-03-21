"""Topology components for FAUCET Mininet unit tests."""

import os
import pty
import re
import select
import time

# pylint: disable=import-error
from mininet.log import error, debug, info
from mininet.node import Host
from mininet.util import isShellBuiltin
from subprocess import call, check_output
from subprocess import Popen, PIPE, STDOUT

from tests.faucet_mininet_test_topo import FaucetHostCleanup


# TODO: mininet 2.2.2 leaks ptys (master slave assigned in startShell)
# override as necessary close them. Transclude overridden methods
# to avoid multiple inheritance complexity.

class DAQHost(FaucetHostCleanup, Host):
    """Base Mininet Host class, for Mininet-based tests."""

    pass


class DockerHost(Host):

    def __init__( self, name, image='daq/default', **kwargs ):
        self.image = image
        Host.__init__( self, name, **kwargs )


    def startShell( self ):
        "Start a shell process for running commands"
        if self.shell:
            error( "%s: shell is already running" )
            return

        self.container = "mininet-" + self.name

        kill_cmd = [ "docker", "rm", "-f", self.container ]
        kill_pipe = Popen( kill_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
        kill_pipe.stdin.close()
        kill_pipe.stdout.readlines()

        cmd = [ "docker", "run", "-ti", "--privileged", "--env", "PS1=" + chr(127), "--net=none", "-h", self.name,
                    "--name", self.container, self.image, 'bash', '--norc', '-is', 'mininet:' + self.name ]
        self.master, self.slave = pty.openpty()
        self.shell = Popen( cmd, stdin=self.slave, stdout=self.slave, stderr=self.slave, close_fds=False )
        self.stdin = os.fdopen(self.master, 'rw')
        self.stdout = self.stdin
        self.pollOut = select.poll() # pylint: disable=invalid-name
        self.pollOut.register(self.stdout) # pylint: disable=no-member
        self.outToNode[self.stdout.fileno()] = self # pylint: disable=no-member
        self.inToNode[self.stdin.fileno()] = self # pylint: disable=no-member
        self.execed = False
        self.lastCmd = None # pylint: disable=invalid-name
        self.lastPid = None # pylint: disable=invalid-name
        self.readbuf = ''
        while True:
            data = self.read(1024) # pylint: disable=no-member
            if data[-1] == chr(127):
                break
            self.pollOut.poll()
        self.waiting = False
        self.cmd('unset HISTFILE; stty -echo; set +m') # pylint: disable=no-member

        pid_cmd = ["docker","inspect","--format={{ .State.Pid }}", self.container]
        pid_pipe = Popen( pid_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=False )
        ps_out = pid_pipe.stdout.readlines()
        self.pid = int(ps_out[0])
        print 'done with docker setup pid %d' % self.pid


    def terminate(self):
        """Override Mininet terminate() to partially avoid pty leak."""
        if self.shell is not None:
            os.close(self.master)
            os.close(self.slave)
            self.shell.kill()
        self.cleanup() # pylint: disable=no-member


    def popen( self, *args, **kwargs ):
        """Return a Popen() object in node's namespace
           args: Popen() args, single list, or string
           kwargs: Popen() keyword args"""
        # Tell mnexec to execute command in our cgroup
        mncmd = [ 'docker', 'exec', self.container ]
        return Host.popen( self, *args, mncmd=mncmd, **kwargs )

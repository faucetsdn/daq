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

        call(["docker rm -f mininet-"+self.name], shell=True)
        cmd = [ "docker", "run", "-d", "--privileged", "--net=none", "-h", self.name,
                "--name=mininet-"+self.name, self.image,'tail','-f','/dev/null']
        docker_cmd = Popen( cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
        self.shell = True
        self.execed = False
        self.lastCmd = None
        self.waiting = False
        docker_cmd.stdin.close()

        dockerLines = docker_cmd.stdout.readlines()
        assert len(dockerLines) == 1, "Unexpected docker start lines"
        self.container = dockerLines[0].strip()

        pid_cmd = ["docker","inspect","--format={{ .State.Pid }}",self.container]
        inspect_cmd = Popen( pid_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=False )
        ps_out = inspect_cmd.stdout.readlines()
        self.pid = int(ps_out[0])
        inspect_cmd.stdin.close()


    def terminate( self ):
        "Sending docker stop"
        if self.shell:
            call(["docker stop mininet-"+self.name], shell=True)
        self.cleanup()

    
    def popen( self, *args, **kwargs ):
        """Return a Popen() object in node's namespace
           args: Popen() args, single list, or string
           kwargs: Popen() keyword args"""
        # Tell mnexec to execute command in our cgroup
        print 'docker popen args %s' % args
        mncmd = [ 'docker', 'exec', self.container ]
        return Host.popen( self, *args, mncmd=mncmd, **kwargs )


    def sendCmd( self, *args, **kwargs ):
        """Send a command, followed by a command to echo a sentinel,
           and return without waiting for the command to complete.
           args: command and arguments, or string
           printPid: print command's PID? (False)"""
        assert self.shell and not self.waiting, "bad cmd state"
        printPid = kwargs.get( 'printPid', False )
        assert not printPid, "docker print pid not supported"
        # Allow sendCmd( (a) )
        if isinstance( args, tuple ):
            cmd = ' '.join(args)
        # Allow sendCmd( [ list ] )
        elif len( args ) == 1 and isinstance( args[ 0 ], list ):
            cmd = args[ 0 ]
        # Allow sendCmd( cmd, arg1, arg2... )
        elif len( args ) > 0:
            cmd = args
        # Convert to list
        if isinstance( cmd, str ):
            cmd = cmd.split()
        self.lastCmd = cmd
        # if a builtin command is backgrounded, it still yields a PID
        if len( cmd ) > 0 and cmd[ -1 ] == '&':
            assert False,'docker background execution not supported'

        # Add sential for end so monitor command knows when it's done.
        cmd_string = ' '.join(cmd) + '; printf "\\177"'

        docker_cmd = [ "docker", "exec", self.container, "sh", "-c", cmd_string ]
        self.pipe = Popen( docker_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
        self.stdin = self.pipe.stdin
        self.stdout = self.pipe.stdout
        self.pid = self.pipe.pid
        self.pollOut = select.poll()
        self.pollOut.register( self.stdout )
        # Maintain mapping between file descriptors and nodes
        # This is useful for monitoring multiple nodes
        # using select.poll()
        self.outToNode[ self.stdout.fileno() ] = self
        self.inToNode[ self.stdin.fileno() ] = self
        self.execed = False
        self.lastCmd = None
        self.lastPid = None
        self.readbuf = ''
        self.waiting = True



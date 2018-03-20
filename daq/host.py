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

        kill_cmd = [ "docker", "rm", "-f", "mininet-" + self.name ]
        kill_pipe = Popen( kill_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
        kill_pipe.stdin.close()
        kill_pipe.stdout.readlines()

        run_cmd = [ "docker", "run", "-d", "--privileged", "--net=none", "-h", self.name,
            "--name=mininet-"+self.name, self.image,'tail','-f','/dev/null']
        run_pipe = Popen( run_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
        self.shell = True
        self.execed = False
        self.lastCmd = None
        self.waiting = False

        run_lines = run_pipe.stdout.readlines()
        assert len(run_lines) == 1, "Unexpected docker start lines: %s" % run_lines
        self.container = run_lines[0].strip()
        run_pipe.stdin.close()

        inspect_cmd = ["docker","inspect","--format={{ .State.Pid }}",self.container]
        inspect_pipe = Popen( inspect_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=False )
        inspect_out = inspect_pipe.stdout.readlines()
        self.pid = int(inspect_out[0])
        inspect_pipe.stdin.close()


    def terminate( self ):
        "Sending docker stop"
        if self.shell:
            os.close(self.master)
            os.close(self.slave)
            call(["docker stop mininet-"+self.name], shell=True)
        self.cleanup()

    
    def popen( self, *args, **kwargs ):
        """Return a Popen() object in node's namespace
           args: Popen() args, single list, or string
           kwargs: Popen() keyword args"""
        # Tell mnexec to execute command in our cgroup
        mncmd = [ 'docker', 'exec', self.container ]
        return Host.popen( self, *args, mncmd=mncmd, **kwargs )


    def sendInt(self, intr=None):
        assert self.shell and self.waiting
        os.close(self.slave)
        self.pipe.terminate()


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
        cmd_string = ' '.join(cmd)
        self.lastCmd = cmd_string
        cmd_sentinal = cmd_string + '; printf "\\177"'

        # Spawn a shell subprocess in a pseudo-tty, to disable buffering
        # in the subprocess and insulate it from signals (e.g. SIGINT)
        # received by the parent
        self.master, self.slave = pty.openpty()
        docker_cmd = [ "docker", "exec", self.container, "sh", "-c", cmd_sentinal ]
        self.pipe = Popen( docker_cmd, stdin=self.slave, stdout=self.slave,
            stderr=self.slave, close_fds=False )
        self.stdin = os.fdopen(self.master, 'rw')
        self.stdout = self.stdin
        self.pollOut = select.poll()
        self.pollOut.register( self.stdout )
        # Maintain mapping between file descriptors and nodes
        # This is useful for monitoring multiple nodes
        # using select.poll()
        self.outToNode[ self.stdout.fileno() ] = self
        self.inToNode[ self.stdin.fileno() ] = self
        self.execed = False
        self.lastPid = self.pipe.pid
        self.readbuf = ''
        self.waiting = True



import subprocess
import re

from clib import mininet_test_util

class NullLogger():
    def debug(self, *args):
        pass


class TcpHelper():

    pipe = None
    tcpdump_started = False
    last_line = None
    funcs = None
    logger = None

    def __init__(self, tcpdump_host, tcpdump_filter, funcs=None,
                 vflags='-v', duration_sec=10, packets=2, root_intf=False,
                 pcap_out=None, intf_name=None, logger=NullLogger()):
        self.intf_name = intf_name if intf_name else tcpdump_host.intf().name
        self.logger = logger
        self.funcs = funcs
        if root_intf:
            self.intf_name = self.intf_name.split('.')[0]

        tcpdump_flags=vflags
        tcpdump_flags+= ' -c %u' % packets if packets else ''
        tcpdump_flags+= ' -w %s' % pcap_out if pcap_out else ''
        tcpdump_cmd = 'tcpdump -i %s %s -e -n -U %s' % (self.intf_name, tcpdump_flags, tcpdump_filter)
        if duration_sec:
            pipe_cmd = mininet_test_util.timeout_soft_cmd(tcpdump_cmd, duration_sec)
        else:
            pipe_cmd = tcpdump_cmd

        logger.debug(pipe_cmd)
        self.pipe = tcpdump_host.popen(
            pipe_cmd,
            stdin=mininet_test_util.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True)

    def stream(self):
        return self.pipe.stdout if self.pipe else None

    def close(self):
        self.pipe.kill()
        self.pipe = None

    def wait(self):
        self.logger.debug('waiting for command completion')
        assert self.pipe, 'tcp helper pipe not valid'
        self.pipe.communicate()
        result = self.pipe.wait()
        if result == 124:
            # Mask result from timeout command.
            result = 0
        return result

    def next_line(self):
        while True:
            line = self.pipe.stdout.readline()
            assert len(line) > 0 or self.tcpdump_started, 'tcpdump did not start: %s' % self.last_line
            if self.tcpdump_started:
                return line
            elif re.search('listening on %s' % self.intf_name, line):
                self.tcpdump_started = True
                # When we see tcpdump start, then call provided functions.
                if self.funcs is not None:
                    for func in self.funcs:
                        func()
            else:
                self.last_line = line

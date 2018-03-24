import subprocess
import re

from tests import faucet_mininet_test_util

class TcpHelper():

    pipe = None
    tcpdump_started = False
    last_line = None
    funcs = None

    def __init__(self, tcpdump_host, tcpdump_filter, funcs=None,
                 vflags='-v', duration_sec=10, packets=2, root_intf=False):
        self.intf_name = tcpdump_host.intf().name
        self.funcs = funcs
        if root_intf:
            self.intf_name = self.intf_name.split('.')[0]
        tcpdump_cmd = faucet_mininet_test_util.timeout_soft_cmd(
            'tcpdump -i %s -e -n -U %s -c %u %s' % (
                self.intf_name, vflags, packets, tcpdump_filter),
            duration_sec)
        self.pipe = tcpdump_host.popen(
            tcpdump_cmd,
            stdin=faucet_mininet_test_util.DEVNULL,
            stderr=subprocess.STDOUT,
            close_fds=True)

    def stream(self):
        return self.pipe.stdout

    def next_line(self):
        line = self.pipe.stdout.readline()
        assert len(line) > 0 or self.tcpdump_started, 'tcpdump did not start: %s' % self.last_line
        if self.tcpdump_started:
            return line
        elif re.search('listening on %s' % self.intf_name, line):
            self.tcpdump_started = True
            # when we see tcpdump start, then call provided functions.
            if self.funcs is not None:
                for func in self.funcs:
                    func()
        else:
            self.last_line = line

import json
import os
import select
import socket
import time

class FaucetEventClient():
    """A general client interface to the FAUCET event API"""

    FAUCET_RETRIES=10

    sock = None
    buffer = None
    previous_state = None

    def connect(self, sock_path):
        """Make connection to sock to receive events"""

        self.previous_state = {}
        self.buffer = b''

        retries = self.FAUCET_RETRIES
        while not os.path.exists(sock_path):
            assert retries > 0, "Could not find socket path %s" % sock_path
            retries -= 1
            time.sleep(1)

        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(sock_path)
        except socket.error as err:
            assert False, "Failed to connect because: %s" % err

    def has_data(self):
        read_socks, write_socks, error_socks = select.select([ self.sock ], [], [], 0)
        return read_socks

    def has_event(self, blocking=False):
        while True:
            if '\n' in self.buffer:
                return True
            elif self.has_data() or blocking:
                self.buffer += self.sock.recv(1024)
            else:
                return False

    def next_event(self):
        while True:
            if self.has_event(blocking=True):
                line, remainder = self.buffer.split('\n', 1)
                self.buffer = remainder
                return json.loads(line)

    def as_port_state(self, event):
        if not 'PORT_CHANGE' in event:
            return (None, None)
        port_no = event['PORT_CHANGE']['port_no']
        port_active = event['PORT_CHANGE']['status']
        if port_no in self.previous_state and self.previous_state[port_no] == port_active:
            return (None, None)
        self.previous_state[port_no] = port_active
        return (port_no, port_active)

    def close(self):
        self.sock.close()
        self.sock = None
        self.buffer = None

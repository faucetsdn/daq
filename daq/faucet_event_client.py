import json
import os
import socket
import time

class FaucetEventClient():
    """A general client interface to the FAUCET event API"""

    FAUCET_RETRIES=10

    sock = None
    buffer = b''

    def connect(self, sock_path):
        """Make connection to sock to receive events"""

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

    def next_event(self):
        while True:
            line, remainder = self.buffer.split('\n', 1) if self.buffer else (None, self.buffer)
            self.buffer = remainder
            if line:
                yield json.loads(line)
            else:
                self.buffer += self.sock.recv(1024)

    def is_port_active_event(self, event):
        port_active_event = ('PORT_CHANGE' in event and
                             event['PORT_CHANGE']['status'] and
                             event['PORT_CHANGE']['reason'] != 'DELETE')
        return event['PORT_CHANGE']['port_no'] if port_active_event else None

    def close(self):
        self.sock.close()
        self.sock = None
        self.buffer = None

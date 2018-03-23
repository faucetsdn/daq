import json
import os
import socket
import time

class FaucetEventClient():
    """A general client interface to the FAUCET event API"""

    sock = None
    buffer = b''

    def connect(self, sock_path):
        """Make connection to sock to receive events"""

        retries = 3
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

    def is_port_add_event(self, event):
        if not 'PORT_CHANGE' in event:
            return None
        if event['PORT_CHANGE']['reason'] != "ADD":
            return None
        return event['PORT_CHANGE']['port_no']
        
    def close(self):
        self.sock.close()
        self.sock = None
        self.buffer = None

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
            elif blocking or self.has_data():
                self.buffer += self.sock.recv(1024)
            else:
                return False

    def filter_state_update(self, event):
        (dpid, port, active) = self.as_port_state(event)
        if dpid and port:
            state_key = '%s-%d' % (dpid, port)
            if state_key in self.previous_state and self.previous_state[state_key] == active:
                return None
            self.previous_state[state_key] = active
            return event

        (dpid, states) = self.as_ports_status(event)
        if dpid:
            for port in states:
                self.prepend_event(self.make_port_state(dpid, port, states[port]))
            return None
        return event

    def prepend_event(self, event):
        self.buffer = '%s\n%s' % (json.dumps(event), self.buffer)

    def next_event(self, blocking=False):
        while self.has_event(blocking=blocking):
            line, remainder = self.buffer.split('\n', 1)
            self.buffer = remainder
            event = json.loads(line)
            event = self.filter_state_update(event)
            if event:
                return event
        return None

    def as_ports_status(self, event):
        if not 'PORTS_STATUS' in event:
            return (None, None)
        return (event['dp_id'], event['PORTS_STATUS'])

    def make_port_state(self, dpid, port, state):
        port_change = {}
        port_change['port_no'] = port
        port_change['status'] = state
        port_change['reason'] = 'MODIFY'
        event = {}
        event['dp_id'] = dpid
        event['PORT_CHANGE'] = port_change
        return event

    def as_port_state(self, event):
        if not 'PORT_CHANGE' in event:
            return (None, None, None)
        dpid = event['dp_id']
        reason = event['PORT_CHANGE']['reason']
        port_no = int(event['PORT_CHANGE']['port_no'])
        port_active = event['PORT_CHANGE']['status'] and not reason == 'DELETE'
        return (dpid, port_no, port_active)

    def close(self):
        self.sock.close()
        self.sock = None
        self.buffer = None

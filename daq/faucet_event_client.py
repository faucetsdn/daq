"""Simple client for working with the faucet event socket"""

import json
import os
import select
import socket
import time

class FaucetEventClient():
    """A general client interface to the FAUCET event API"""

    FAUCET_RETRIES = 10

    def __init__(self):
        self.sock = None
        self.buffer = None
        self.previous_state = None

    def connect(self, sock_path):
        """Make connection to sock to receive events"""

        self.previous_state = {}
        self.buffer = ''

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

    def disconnect(self):
        """Disconnect this event socket"""
        self.sock.close()
        self.sock = None

    def has_data(self):
        """Check to see if the event socket has any data to read"""
        read, dummy_write, dummy_error = select.select([self.sock], [], [], 0)
        return read

    def has_event(self, blocking=False):
        """Check if there are any queued events"""
        while True:
            if '\n' in self.buffer:
                return True
            if blocking or self.has_data():
                self.buffer += self.sock.recv(1024).decode('utf-8')
            else:
                return False

    def filter_state_update(self, event):
        """Filter out state updates to only detect meaningful changes"""
        (dpid, port, active) = self.as_port_state(event)
        if dpid and port:
            state_key = '%s-%d' % (dpid, port)
            if state_key in self.previous_state and self.previous_state[state_key] == active:
                return None
            self.previous_state[state_key] = active
            return event

        (dpid, status) = self.as_ports_status(event)
        if dpid:
            for port in status:
                self.prepend_event(self.make_port_state(dpid, port, status[port]))
            return None
        return event

    def prepend_event(self, event):
        """Prepend a (synthetic) event to the event queue"""
        self.buffer = '%s\n%s' % (json.dumps(event), self.buffer)

    def next_event(self, blocking=False):
        """Return the next event from the queue"""
        while self.has_event(blocking=blocking):
            line, remainder = self.buffer.split('\n', 1)
            self.buffer = remainder
            event = json.loads(line)
            event = self.filter_state_update(event)
            if event:
                return event
        return None

    def as_ports_status(self, event):
        """Convert the event to port status info, if applicable"""
        if not event or 'PORTS_STATUS' not in event:
            return (None, None)
        return (event['dp_id'], event['PORTS_STATUS'])

    def make_port_state(self, dpid, port, status):
        """Make a synthetic port state event"""
        port_change = {}
        port_change['port_no'] = port
        port_change['status'] = status
        port_change['reason'] = 'MODIFY'
        event = {}
        event['dp_id'] = dpid
        event['PORT_CHANGE'] = port_change
        return event

    def as_port_state(self, event):
        """Convert event to a port state info, if applicable"""
        if not event or 'PORT_CHANGE' not in event:
            return (None, None, None)
        dpid = event['dp_id']
        reason = event['PORT_CHANGE']['reason']
        port_no = int(event['PORT_CHANGE']['port_no'])
        port_active = event['PORT_CHANGE']['status'] and reason != 'DELETE'
        return (dpid, port_no, port_active)

    def as_port_learn(self, event):
        """Convert to port learning info, if applicable"""
        if not event or 'L2_LEARN' not in event:
            return (None, None, None)
        dpid = event['dp_id']
        port_no = int(event['L2_LEARN']['port_no'])
        eth_src = event['L2_LEARN']['eth_src']
        return (dpid, port_no, eth_src)

    def close(self):
        """Close the faucet event socket"""
        self.sock.close()
        self.sock = None
        self.buffer = None

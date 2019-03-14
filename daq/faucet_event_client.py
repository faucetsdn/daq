"""Simple client for working with the faucet event socket"""

import json
import logging
import os
import select
import socket
import threading
import time

LOGGER = logging.getLogger('faucet')

class FaucetEventClient():
    """A general client interface to the FAUCET event API"""

    FAUCET_RETRIES = 10
    _PORT_DEBOUNCE_SEC = 5

    def __init__(self, config):
        self.config = config
        self.sock = None
        self.buffer = None
        self._buffer_lock = threading.Lock()
        self.previous_state = None
        self._port_debounce_sec = int(config.get('port_debounce_sec', self._PORT_DEBOUNCE_SEC))
        self._port_timers = {}

    def connect(self):
        """Make connection to sock to receive events"""

        sock_path = os.getenv('FAUCET_EVENT_SOCK')

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
                data = self.sock.recv(1024).decode('utf-8')
                with self._buffer_lock:
                    self.buffer += data
            else:
                return False

    def _filter_faucet_event(self, event):
        (dpid, port, active) = self.as_port_state(event)
        if dpid and port:
            if not event.get('debounced'):
                self._debounce_port_event(dpid, port, active)
            elif self._process_state_update(dpid, port, active):
                return event
            return None

        (dpid, status) = self.as_ports_status(event)
        if dpid:
            for port in status:
                # Prepend events so they functionally replace the current one in the queue.
                self._prepend_event(self._make_port_state(dpid, port, status[port]))
            return None
        return event

    def _process_state_update(self, dpid, port, active):
        state_key = '%s-%d' % (dpid, port)
        if state_key in self.previous_state and self.previous_state[state_key] == active:
            return False
        LOGGER.debug('Port change %s active %s', state_key, active)
        self.previous_state[state_key] = active
        return True

    def _debounce_port_event(self, dpid, port, active):
        if not self._port_debounce_sec:
            self._handle_debounce(dpid, port, active)
            return
        state_key = '%s-%d' % (dpid, port)
        if state_key in self._port_timers:
            LOGGER.debug('Port cancel %s', state_key)
            self._port_timers[state_key].cancel()
        if active:
            self._handle_debounce(dpid, port, active)
            return
        LOGGER.debug('Port timer %s = %s', state_key, active)
        timer = threading.Timer(self._port_debounce_sec,
                                lambda: self._handle_debounce(dpid, port, active))
        timer.start()
        self._port_timers[state_key] = timer

    def _handle_debounce(self, dpid, port, active):
        LOGGER.debug('Port handle %s-%s as %s', dpid, port, active)
        self._append_event(self._make_port_state(dpid, port, active, debounced=True))

    def _prepend_event(self, event):
        with self._buffer_lock:
            self.buffer = '%s\n%s' % (json.dumps(event), self.buffer)

    def _append_event(self, event):
        event_str = json.dumps(event)
        with self._buffer_lock:
            index = self.buffer.rfind('\n')
            if index == len(self.buffer) - 1:
                self.buffer = '%s%s\n' % (self.buffer, event_str)
            elif index == -1:
                self.buffer = '%s\n%s' % (event_str, self.buffer)
            else:
                self.buffer = '%s\n%s%s' % (self.buffer[:index], event_str, self.buffer[index:])
            LOGGER.debug('appended %s\n%s*', event_str, self.buffer)

    def next_event(self, blocking=False):
        """Return the next event from the queue"""
        while self.has_event(blocking=blocking):
            with self._buffer_lock:
                line, remainder = self.buffer.split('\n', 1)
                self.buffer = remainder
            try:
                event = json.loads(line)
            except Exception as e:
                LOGGER.info('Error (%s) parsing\n%s*\nwith\n%s*', str(e), line, remainder)
            event = self._filter_faucet_event(event)
            if event:
                return event
        return None

    def _make_port_state(self, dpid, port, status, debounced=False):
        port_change = {}
        port_change['port_no'] = port
        port_change['status'] = status
        port_change['reason'] = 'MODIFY'
        event = {}
        event['dp_id'] = dpid
        event['PORT_CHANGE'] = port_change
        event['debounced'] = debounced
        return event

    def as_config_change(self, event):
        """Convert the event to dp change info, if applicable"""
        if not event or 'CONFIG_CHANGE' not in event:
            return (None, None)
        return (event['dp_id'], event['CONFIG_CHANGE'].get('restart_type'))

    def as_ports_status(self, event):
        """Convert the event to port status info, if applicable"""
        if not event or 'PORTS_STATUS' not in event:
            return (None, None)
        return (event['dp_id'], event['PORTS_STATUS'])

    def as_port_state(self, event):
        """Convert event to a port state info, if applicable"""
        if not event or 'PORT_CHANGE' not in event:
            return (None, None, None)
        dpid = event['dp_id']
        port_no = int(event['PORT_CHANGE']['port_no'])
        reason = event['PORT_CHANGE']['reason']
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
        with self._buffer_lock:
            self.buffer = None

"""Utility class to monitor a bunch of input streams and trigger events"""

import fcntl
import logging
import os
import select

LOGGER = logging.getLogger('stream')

class StreamMonitor():
    """Monitor set of stream objects"""

    def __init__(self, timeout_ms=None, idle_handler=None, loop_hook=None):
        self.timeout_ms = timeout_ms
        self.idle_handler = idle_handler
        self.loop_hook = loop_hook
        self.poller = select.poll()
        self.callbacks = {}
        self.dirty = False

    def get_fd(self, target):
        """Return the fd from a stream object, or fd directly"""
        return target.fileno() if 'fileno' in dir(target) else target

    # pylint: disable=too-many-arguments
    def monitor(self, name, desc, callback=None, hangup=None, copy_to=None, error=None):
        """Start monitoring a specific descriptor"""
        fd = self.get_fd(desc)
        assert fd not in self.callbacks, 'Duplicate descriptor fd %d' % fd
        if copy_to:
            assert not callback, 'Both callback and copy_to set'
            self.make_nonblock(desc)
            callback = lambda: self.copy_data(name, desc, copy_to)
        LOGGER.debug('Monitoring start %s fd %d', name, fd)
        self.callbacks[fd] = (name, callback, hangup, error)
        self.poller.register(fd, select.POLLHUP | select.POLLIN)
        self.log_monitors()

    def copy_data(self, name, data_source, data_sink):
        """Function to just copy data to a given sink"""
        LOGGER.debug('Monitoring copying data for %s from fd %d to fd %d',
                     name, self.get_fd(data_source), self.get_fd(data_sink))
        data = data_source.read(1024)
        data_sink.write(data.decode('utf-8'))

    def make_nonblock(self, data_source):
        """Make the given source non-blocking"""
        fd = self.get_fd(data_source)
        LOGGER.debug('Monitoring mking fd %d non-blocking for copy_to', fd)
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def forget(self, desc):
        """Stop monitoring the given descriptor"""
        fd = self.get_fd(desc)
        assert fd in self.callbacks, 'Missing descriptor fd %d' % fd
        LOGGER.debug('Monitoring forget fd %d', fd)
        del self.callbacks[fd]
        self.poller.unregister(fd)
        self.dirty = True
        self.log_monitors()

    def log_monitors(self):
        """Log all active monitors"""
        log_str = ''
        for fd in self.callbacks:
            name = self.callbacks[fd][0]
            log_str = log_str + ', %s fd %d' % (name, fd)
        LOGGER.debug('Monitoring fds %s', log_str[2:])

    def trigger_callback(self, fd):
        """Trigger a data callback for the given fd"""
        name = self.callbacks[fd][0]
        callback = self.callbacks[fd][1]
        on_error = self.callbacks[fd][3]
        try:
            if callback:
                LOGGER.debug('Monitoring callback fd %d (%s) start', fd, name)
                callback()
                LOGGER.debug('Monitoring callback fd %d (%s) done', fd, name)
            else:
                LOGGER.debug('Monitoring flush fd %d (%s)', fd, name)
                os.read(fd, 1024)
        except Exception as e:
            if fd in self.callbacks:
                self.forget(fd)
            self.error_handler(fd, e, name, on_error)

    def trigger_hangup(self, fd, event):
        """Trigger hangup callback for the given fd"""
        name = self.callbacks[fd][0]
        callback = self.callbacks[fd][2]
        on_error = self.callbacks[fd][3]
        try:
            self.forget(fd)
            if callback:
                LOGGER.debug('Monitoring hangup fd %d because %d (%s)', fd, event, name)
                callback()
                LOGGER.debug('Monitoring hangup fd %d done (%s)', fd, name)
            else:
                LOGGER.debug('Monitoring no hangup fd %d because %d (%s)', fd, event, name)
        except Exception as e:
            self.error_handler(fd, e, name, on_error)

    def error_handler(self, fd, e, name, handler):
        """Error handler for the given fd"""
        msg = '' if handler else ' (no handler)'
        LOGGER.error('Monitoring error handling %s fd %d%s: %s', name, fd, msg, e)
        if handler:
            try:
                handler(e)
            except Exception as handler_exception:
                LOGGER.error('Monitoring exception %s fd %d done: %s', name, fd, handler_exception)
                LOGGER.exception(handler_exception)
        else:
            LOGGER.exception(e)

    def process_poll_result(self, event, fd):
        """Process an individual poll result"""
        if event & select.POLLNVAL:
            assert False, 'POLLNVAL on fd %d' % fd
        elif event & select.POLLIN:
            self.trigger_callback(fd)
        elif event & (select.POLLHUP | select.POLLERR):
            self.trigger_hangup(fd, event)
        else:
            assert False, "Unknown event type %d on fd %d" % (event, fd)

    def event_loop(self):
        """Main event loop. Returns True if there are still active streams to monitor."""
        while self.callbacks:
            fds = self.poller.poll(0)
            try:
                if not fds and self.idle_handler:
                    self.idle_handler()
                    # Check corner case when idle_handler removes all callbacks.
                    if not self.callbacks:
                        return False
                if self.loop_hook:
                    self.loop_hook()
            except Exception as e:
                LOGGER.error('Monitoring exception in callback: %s', e)
                LOGGER.exception(e)
            self.log_monitors()
            self.dirty = False
            fds = self.poller.poll(self.timeout_ms)
            LOGGER.debug('Monitoring found fds %s', fds)
            if fds:
                for fd, event in fds:
                    self.process_poll_result(event, fd)
                    if self.dirty:
                        LOGGER.debug('Monitoring set modified, re-issuing poll...')
                        break
            else:
                LOGGER.debug('Monitoring no fds found')
                return True
        return False

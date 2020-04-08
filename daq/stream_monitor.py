"""Utility class to monitor a bunch of input streams and trigger events"""

import fcntl
import os
import select

import logger

LOGGER = logger.get_logger('stream')

class StreamMonitor:
    """Monitor set of stream objects"""

    def __init__(self, timeout_sec=None, idle_handler=None, loop_hook=None):
        self.timeout_sec = timeout_sec
        self.idle_handler = idle_handler
        self.loop_hook = loop_hook
        self.poller = select.poll()
        self.callbacks = {}

    def get_fd(self, target):
        """Return the fd from a stream object, or fd directly"""
        return target.fileno() if 'fileno' in dir(target) else target

    # pylint: disable=too-many-arguments
    def monitor(self, name, desc, callback=None, hangup=None, copy_to=None,
                error=None):
        """Start monitoring a specific descriptor"""
        fd = self.get_fd(desc)
        assert fd not in self.callbacks, 'Duplicate descriptor fd %d' % fd
        if copy_to:
            assert not callback, 'Both callback and copy_to set'
            self.make_nonblock(desc)
            callback = lambda: self.copy_data(name, desc, copy_to)
        LOGGER.debug('Monitoring start %s fd %d', name, fd)
        self.callbacks[fd] = (name, callback, hangup, error, desc)
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
        self.log_monitors()

    def log_monitors(self, as_info=False):
        """Log all active monitors"""
        log_str = ''
        count = 0
        for fd in self.callbacks:
            name = self.callbacks[fd][0]
            log_str = log_str + ', %s fd %d' % (name, fd)
            count += 1

        log_func = LOGGER.info if as_info else LOGGER.debug
        log_func('Monitoring %d fds %s', count, log_str[2:])

        return count

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
                LOGGER.debug('Monitoring callback flush fd %d (%s)', fd, name)
                os.read(fd, 1024)
        except Exception as e:
            LOGGER.error('Monitoring callback exception (%s): %s', name, str(e))
            self.error_handler(e, name, on_error)

    def trigger_hangup(self, fd, event):
        """Trigger hangup callback for the given fd"""
        name = self.callbacks[fd][0]
        callback = self.callbacks[fd][2]
        on_error = self.callbacks[fd][3]
        self.callbacks[fd][4].close()
        try:
            self.forget(fd)
            if callback:
                LOGGER.debug('Monitoring hangup because %d (%s)', event, name)
                callback()
                LOGGER.debug('Monitoring hangup done (%s)', name)
            else:
                LOGGER.debug('Monitoring hangup flush because %d (%s)', event, name)
        except Exception as e:
            LOGGER.error('Monitoring hangup exception (%s): %s', name, str(e))
            self.error_handler(e, name, on_error)

    def error_handler(self, e, name, handler):
        """Call given error handler"""
        msg = '' if handler else ' (no handler)'
        LOGGER.debug('Monitoring error handling %s %s: %s', name, msg, e)
        if handler:
            try:
                handler(e)
            except Exception as handler_exception:
                LOGGER.error('Monitoring exception %s fail: %s', name, handler_exception)
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
        """Main event loop. Returns True if there are active streams to monitor."""
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
        fds = self.poller.poll(self.timeout_sec * 10e3 if self.timeout_sec else None)
        LOGGER.debug('Monitoring found fds %s', fds)
        if fds:
            for fd, event in fds:
                if fd in self.callbacks: # Monitoring set could be modified
                    self.process_poll_result(event, fd)
        return len(self.callbacks) > 0

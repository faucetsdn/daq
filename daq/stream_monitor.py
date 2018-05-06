import logging
import errno
import fcntl
import os

from select import poll, POLLIN, POLLHUP, POLLNVAL, POLLERR

class StreamMonitor():
    """Monitor dict of stream objects
       timeoutms_ms: timeout for poll()
       yields: stream object with data, None if timeout
       terminates: when all EOFs received"""

    DEFAULT_TIMEOUT_MS = None
    timeout_ms = None
    poller = None
    callbacks = None
    idle_handler = None
    loop_hook = None

    def __init__(self, timeout_ms=None, idle_handler=None, loop_hook=None):
        self.timeout_ms = timeout_ms
        self.idle_handler = idle_handler
        self.loop_hook = loop_hook
        self.poller = poll()
        self.callbacks = {}

    def get_fd(self, target):
        return target.fileno() if 'fileno' in dir(target) else target

    def monitor(self, name, desc, callback=None, hangup=None, copy_to=None, error=None):
        fd = self.get_fd(desc)
        assert not fd in self.callbacks, 'Duplicate descriptor fd %d' % fd
        if copy_to:
            assert not callback, 'Both callback and copy_to set'
            self.make_nonblock(desc)
            callback = lambda: self.copy_data(name, desc, copy_to)
        logging.debug('Start monitoring %s fd %d' % (name, fd))
        self.callbacks[fd] = (name, callback, hangup, error)
        self.poller.register(fd, POLLHUP | POLLIN)
        self.log_monitors()

    def copy_data(self, name, data_source, data_sink):
        logging.debug('Copying data for %s from fd %d to fd %d' % (name, self.get_fd(data_source), self.get_fd(data_sink)))
        data = data_source.read(1024)
        data_sink.write(data)
        logging.debug('Copied %d from fd %d to fd %d' % (len(data), self.get_fd(data_source), self.get_fd(data_sink)))

    def make_nonblock(self, data_source):
        fd = self.get_fd(data_source)
        logging.debug('Making fd %d non-blocking for copy_to' % fd)
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def forget(self, desc):
        fd = self.get_fd(desc)
        assert fd in self.callbacks, 'Missing descriptor fd %d' % fd
        logging.debug('Stop monitoring fd %d' % fd)
        del self.callbacks[fd]
        self.poller.unregister(fd)
        self.log_monitors()

    def log_monitors(self):
        log_str = ''
        for fd in self.callbacks.keys():
            name = self.callbacks[fd][0]
            log_str = log_str + ', %s fd %d' % (name, fd)
        logging.debug('Monitoring %s' % log_str[2:])

    def trigger_callback(self, fd):
        name = self.callbacks[fd][0]
        callback = self.callbacks[fd][1]
        on_error = self.callbacks[fd][3]
        try:
            if callback:
                logging.debug('Data callback fd %d (%s)' % (fd, name))
                callback()
            else:
                logging.debug('Data flush fd %d (%s)' % (fd, name))
                os.read(fd, 1024)
        except Exception as e:
            if fd in self.callbacks:
                self.forget(fd)
            self.error_handler(fd, e, name)

    def trigger_hangup(self, fd, event):
        name = self.callbacks[fd][0]
        callback = self.callbacks[fd][2]
        on_error = self.callbacks[fd][3]
        try:
            self.forget(fd)
            if callback:
                logging.debug('Hangup callback fd %d because %d (%s)' % (fd, event, name))
                callback()
            else:
                logging.debug('No hangup callback fd %d because %d (%s)' % (fd, event, name))
        except Exception as e:
            self.error_handler(fd, e, name)

    def error_handler(self, fd, e, name):
        logging.error('Error handling %s fd %d: %s' % (name, fd, e))
        if handler:
            handler(e)

    def event_loop(self):
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
                logging.error('Exception in callback: %s' % e)
                logging.exception(e)
            self.log_monitors()
            fds = self.poller.poll(self.timeout_ms)
            if fds:
                for fd, event in fds:
                    if event & POLLNVAL:
                        assert False, 'POLLNVAL on fd %d' % fd
                    elif event & (POLLHUP | POLLERR):
                        self.trigger_hangup(fd, event)
                    elif event & POLLIN:
                        self.trigger_callback(fd)
                    else:
                        assert False, "Unknown event type %d on fd %d" % (event, fd)
            else:
                logging.debug('No monitored fds found')
                return True
        return False

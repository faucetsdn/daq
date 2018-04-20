import logging
import errno
import fcntl
import os

from select import poll, POLLIN, POLLHUP, POLLNVAL

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

    def __init__(self, timeout_ms=None, idle_handler=None):
        self.timeout_ms = timeout_ms
        self.idle_handler = idle_handler
        self.poller = poll()
        self.callbacks = {}

    def get_fd(self, target):
        return target.fileno() if 'fileno' in dir(target) else target

    def monitor(self, desc, callback=None, hangup=None, copy_to=None):
        fd = self.get_fd(desc)
        assert not fd in self.callbacks, 'duplicate descriptor %d' % fd
        if copy_to:
            assert not callback, 'both callback and copy_to set'
            self.make_nonblock(desc)
            callback = lambda: self.copy_data(desc, copy_to)
        self.callbacks[fd] = (callback, hangup)
        self.poller.register(fd, POLLHUP | POLLIN)

    def copy_data(self, data_source, data_sink):
        data_sink.write(data_source.read(1024))

    def make_nonblock(self, data_source):
        fd = self.get_fd(data_source)
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def forget(self, desc):
        fd = self.get_fd(desc)
        assert fd in self.callbacks, 'missing descriptor %d' % fd
        del self.callbacks[fd]
        self.poller.unregister(fd)

    def trigger_callback(self, fd):
        callback = self.callbacks[fd][0]
        try:
            if callback:
                callback()
            else:
                os.read(fd, 1024)
        except Exception as e:
            logging.error('Error handling callback: %s' % e)

    def trigger_hangup(self, fd):
        callback = self.callbacks[fd][1]
        self.forget(fd)
        try:
            if callback:
                callback()
        except Exception as e:
            logging.error('Error handling hangup: %s' % e)

    def event_loop(self):
        while self.callbacks:
            fds = self.poller.poll(0)
            if not fds and self.idle_handler:
                self.idle_handler()
                # Check corner case when idle_handler removes all callbacks.
                if not self.callbacks:
                    return False
            logging.debug('Entering poll loop %s' % self.callbacks.keys())
            fds = self.poller.poll(self.timeout_ms)
            if fds:
                for fd, event in fds:
                    if event & POLLIN:
                        self.trigger_callback(fd)
                    elif event & POLLHUP or event & POLLNVAL:
                        self.trigger_hangup(fd)
                    else:
                        assert False, "Unknown event type %d on fd %d" % (event, fd)
            else:
                return True
        return False

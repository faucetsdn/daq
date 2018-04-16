from select import poll, POLLIN, POLLHUP

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

    def monitor(self, desc, callback):
        fd = self.get_fd(desc)
        assert not fd in self.callbacks, 'duplicate descriptor %d' % fd
        self.callbacks[fd] = callback
        self.poller.register(fd, POLLIN | POLLHUP)

    def forget(self, desc):
        fd = self.get_fd(desc)
        assert fd in self.callbacks, 'missing descriptor %d' % fd
        del self.callbacks[fd]
        self.poller.unregister(fd)

    def trigger_callback(self, fd):
        self.callbacks[fd]()

    def event_loop(self):
        while self.callbacks:
            fds = self.poller.poll(0)
            if not fds and self.idle_handler:
                self.idle_handler()
                # Check corner case when idle_handler removes all callbacks.
                if not self.callbacks:
                    return False
            fds = self.poller.poll(self.timeout_ms)
            if fds:
                for fd, event in fds:
                    if event & POLLIN:
                        self.trigger_callback(fd)
                    elif event & POLLHUP:
                        self.forget(fd)
                    else:
                        assert False, "Unknown event type %d on fd %d" % (event, fd)
            else:
                return True
        return False

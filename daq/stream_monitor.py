from select import poll, POLLIN, POLLHUP

class StreamMonitor():
    """Monitor dict of stream objects
       timeoutms_ms: timeout for poll()
       yields: stream object with data, None if timeout
       terminates: when all EOFs received"""

    DEFAULT_TIMEOUT_MS = 10000
    timeout_ms = None
    poller = None
    fd_to_stream = None

    def __init__(self, timeout_ms=DEFAULT_TIMEOUT_MS):
        self.timeout_ms = timeout_ms
        self.poller = poll()
        self.fd_to_stream = {}

    def get_fd(self, stream):
        return stream.fileno()

    def add_stream(self, stream):
        fd = self.get_fd(stream)
        self.fd_to_stream[fd] = stream
        self.poller.register(fd, POLLIN)

    def remove_stream(self, stream):
        fd = self.get_fd(stream)
        self.poller.unregister(fd)
        del self.fd_to_stream[fd]

    def generator(self):
        while self.fd_to_stream:
            fds = self.poller.poll(self.timeout_ms)
            if fds:
                for fd, event in fds:
                    stream = self.fd_to_stream[fd]
                    if event & POLLIN:
                        yield stream
                    elif event & POLLHUP:
                        self.remove_stream(stream)
                        yield stream
                    else:
                        assert False, "Unknown event type %d on fd %d" % (event, fd)
            else:
                yield None

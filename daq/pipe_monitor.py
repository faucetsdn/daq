from select import poll, POLLIN, POLLHUP

class PipeMonitor():
    """Monitor dict of stream objects
       timeoutms_ms: timeout for poll()
       yields: stream object with data, None if timeout
       terminates: when all EOFs received"""

    DEFAULT_TIMEOUT_MS = 10000
    timeout_ms = None
    poller = None
    fd_to_pipe = None

    def __init__(self, timeout_ms=DEFAULT_TIMEOUT_MS):
        self.timeout_ms = timeout_ms
        self.poller = poll()
        self.fd_to_pipe = {}

    def get_fd(self, pipe):
        return pipe.fileno()

    def add_pipe(self, pipe):
        fd = self.get_fd(pipe)
        self.fd_to_pipe[fd] = pipe
        self.poller.register(fd, POLLIN)

    def remove_pipe(self, pipe):
        fd = self.get_fd(pipe)
        self.poller.unregister(fd)
        del self.fd_to_pipe[fd]

    def monitor_pipes(self):
        while self.fd_to_pipe:
            fds = self.poller.poll(self.timeout_ms)
            if fds:
                for fd, event in fds:
                    pipe = self.fd_to_pipe[fd]
                    if event & POLLIN:
                        yield pipe
                    elif event & POLLHUP:
                        self.remove_pipe(pipe)
                        yield pipe
                    else:
                        assert False, "Unknown event type %d on fd %d" % (event, fd)
            else:
                yield None

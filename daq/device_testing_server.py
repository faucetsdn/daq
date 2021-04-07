"""gRPC server to receive devices state"""

from concurrent import futures
from queue import Queue
import threading
import grpc

import daq.logger as logger
import daq.proto.device_testing_pb2_grpc as server_grpc


LOGGER = logger.get_logger('devserv')


DEFAULT_MAX_WORKERS = 10
DEFAULT_SERVER_PORT = 47808
DEFAULT_BIND_ADDRESS = '0.0.0.0'

class DeviceTestingServicer(server_grpc.DeviceTestingServicer):
    """gRPC servicer to receive devices state"""

    def __init__(self, on_result):
        super().__init__()
        self._on_result = on_result
        self._lock = threading.Lock()

    # pylint: disable=invalid-name
    def StartSession(self, request, context):
        listener_q = Queue()
        LOGGER.info('Attaching response channel')
        while True:
            item = listener_q.get()
            if item is False:
                break
            yield item


class SessionServer:
    """Devices state server"""

    def __init__(self, on_result, address=None, port=None, max_workers=None):
        self._server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=max_workers or DEFAULT_MAX_WORKERS))

        self._servicer = DeviceTestingServicer(on_result)
        server_grpc.add_DeviceTestingServicer_to_server(self._servicer, self._server)

        server_address_port = f'{address or DEFAULT_BIND_ADDRESS}:{port or DEFAULT_SERVER_PORT}'
        self._server.add_insecure_port(server_address_port)

    def start(self):
        """Start the server"""
        self._server.start()

    def stop(self):
        """Stop the server"""
        self._server.stop(grace=None)


def _receive_result(result):
    LOGGER.info('Received result', result)


if __name__ == '__main__':
    SERVER = SessionServer(_receive_result)
    SERVER.start()

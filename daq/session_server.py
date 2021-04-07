"""gRPC server to receive devices state"""

from concurrent import futures
import logging
import sys
import threading
import time
import grpc

import logger
import proto.session_server_pb2_grpc as server_grpc
from proto.session_server_pb2 import SessionParams, SessionProgress

from utils import dict_proto

LOGGER = logger.get_logger('devserv')


DEFAULT_MAX_WORKERS = 10
DEFAULT_SERVER_PORT = 47808
DEFAULT_BIND_ADDRESS = '0.0.0.0'
DEFAULT_SERVER_ADDRESS = '127.0.0.1'
DEFAULT_RPC_TIMEOUT_SEC = 10

class SessionServerServicer(server_grpc.SessionServerServicer):
    """gRPC servicer to receive devices state"""

    def __init__(self, on_session):
        super().__init__()
        self._on_session = on_session
        self._lock = threading.Lock()

    # pylint: disable=invalid-name
    def StartSession(self, request, context):
        """Start a session servicer"""
        self._on_session(request)
        results = ['a', 'b', 'c']
        for result in results:
            LOGGER.info('Sending progress ' + result)
            yield SessionProgress(endpoint_ip=result)


class SessionServer:
    """Devices state server"""

    def __init__(self, on_session, address=None, port=None, max_workers=None):
        self._server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=max_workers or DEFAULT_MAX_WORKERS))

        self._servicer = SessionServerServicer(on_session)
        server_grpc.add_SessionServerServicer_to_server(self._servicer, self._server)

        self._address = f'{address or DEFAULT_BIND_ADDRESS}:{port or DEFAULT_SERVER_PORT}'
        self._server.add_insecure_port(self._address)

    def start(self):
        """Start the server"""
        LOGGER.info('Starting sesson server on ' + self._address)
        self._server.start()

    def stop(self):
        """Stop the server"""
        self._server.stop(grace=None)


class TestingSessionServerClient:
    """Test-only client as a session server."""

    def __init__(self, server_address=DEFAULT_SERVER_ADDRESS, server_port=DEFAULT_SERVER_PORT,
                 rpc_timeout_sec=DEFAULT_RPC_TIMEOUT_SEC):
        self._initialize_stub(server_address, server_port)
        self._rpc_timeout_sec = rpc_timeout_sec

    def _initialize_stub(self, sever_address, server_port):
        address = f'{sever_address}:{server_port}'
        LOGGER.info('Connecting to server ' + address)
        channel = grpc.insecure_channel(address)
        self._stub = server_grpc.SessionServerStub(channel)

    def start_session(self, mac):
        """Send device result of a device to server"""
        devices_state = {
            'device_mac': mac
        }
        LOGGER.info('Connecting to stream for mac ' + mac)
        return self._stub.StartSession(dict_proto(devices_state, SessionParams),
                                       timeout=self._rpc_timeout_sec)

if __name__ == '__main__':
    """Snippet for testing basic client/server operation from the command line."""

    def _receive_session(result):
        LOGGER.info('Received session %s', result.device_mac)

    logger.set_config(level=logging.INFO)
    if sys.argv[1] == 'server':
        SERVER = SessionServer(_receive_session)
        SERVER.start()
        LOGGER.info('Blocking for test')
        time.sleep(1000)
    elif sys.argv[1] == 'client':
        CLIENT = TestingSessionServerClient()
        RESULTS = CLIENT.start_session('123')
        LOGGER.info('Session result: ' + str(list(RESULTS)))

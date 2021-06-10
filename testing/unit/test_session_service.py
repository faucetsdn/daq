"""Unit tests for session server"""
from __future__ import absolute_import
import time
import unittest
from unittest.mock import MagicMock

from session_server import DEFAULT_SERVER_PORT, SessionServer, TestingSessionServerClient
from forch.proto.shared_constants_pb2 import PortBehavior
from daq.proto.session_server_pb2 import SessionResult


_TEST_MAC_ADDRESS = 'aa:bb:cc:dd:ee:ff'
_BASE_PORT = DEFAULT_SERVER_PORT
_LOCAL_IP = '127.0.0.3'


class BaseSessionServerTest(unittest.TestCase):
    """Base session server test class for setup."""
    port = _BASE_PORT

    def setUp(self):
        self._server_results = []
        self._on_session_end = MagicMock(return_value=None)
        self._server = SessionServer(on_session=self._new_connection,
                                     on_session_end=self._on_session_end, server_port=self.port,
                                     local_ip=_LOCAL_IP)
        self._server.start()

    def tearDown(self):
        self._server.stop()

    def _new_connection(self, result):
        print('receive result')
        self._server_results.append(result)


class SessionServerTest(BaseSessionServerTest):
    """Test basic session server operation"""
    port = _BASE_PORT

    def _new_connection(self, result):
        super()._new_connection(result)
        self._server.send_device_result(_TEST_MAC_ADDRESS, PortBehavior.passed)
        self._server.close_stream(_TEST_MAC_ADDRESS)

    # pylint: disable=no-member
    def test_server_connect(self):
        """Simple server connetion test"""
        client = TestingSessionServerClient(server_port=self.port)
        session = client.start_session(_TEST_MAC_ADDRESS)
        print('session running')
        results = list(session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].endpoint.ip, _LOCAL_IP)
        self.assertEqual(results[1].result.code, SessionResult.ResultCode.STARTED)
        self.assertEqual(len(self._server_results), 1)
        self.assertEqual(self._server_results[0].device_mac, _TEST_MAC_ADDRESS)
        self._on_session_end.assert_called_once_with(self._server_results[0])


class SessionServerDisallowSameClient(BaseSessionServerTest):
    """Test session server behavior with multiples of the same clients."""

    port = _BASE_PORT + 1

    def _new_connection(self, result):
        super()._new_connection(result)
        self._server.send_device_result(_TEST_MAC_ADDRESS, PortBehavior.passed)

    def tearDown(self):
        self._server.close_stream(_TEST_MAC_ADDRESS)
        return super().tearDown()

    def test_disallow_same_client(self):
        """Test when the same client connects twice, the second session is terminated."""
        client = TestingSessionServerClient(server_port=self.port)
        results = client.start_session(_TEST_MAC_ADDRESS)
        client = TestingSessionServerClient(server_port=self.port)
        results = client.start_session(_TEST_MAC_ADDRESS)
        time.sleep(1)
        self.assertIn("already registered", repr(results))


class SessionServerClientDisconnect(BaseSessionServerTest):
    """Test session server behavior when clients disconnect."""

    port = _BASE_PORT + 2

    def _new_connection(self, result):
        super()._new_connection(result)
        self._server.send_device_result(_TEST_MAC_ADDRESS, PortBehavior.passed)

    # pylint: disable=no-member,protected-access
    def test_client_disconnect(self):
        """Test when client disconnects the session is terminated."""
        # Connection not timed out.
        client = TestingSessionServerClient(server_port=self.port)
        session = client.start_session(_TEST_MAC_ADDRESS)
        time.sleep(1)
        self._server.send_device_heartbeats()
        time.sleep(1)
        self._server.close_stream(_TEST_MAC_ADDRESS)
        results = list(session)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].endpoint.ip, _LOCAL_IP)
        self.assertEqual(results[1].result.code, SessionResult.ResultCode.STARTED)
        self.assertEqual(results[2].result.code, SessionResult.ResultCode.PASSED)
        self.assertEqual(results[3].result.code, SessionResult.ResultCode.PENDING)

        # Connection timed out
        session = client.start_session(_TEST_MAC_ADDRESS)
        self._server._disconnect_timeout_sec = 0
        time.sleep(1)
        self._server.send_device_heartbeats()
        time.sleep(1)
        results = list(session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].endpoint.ip, _LOCAL_IP)
        self.assertEqual(results[1].result.code, SessionResult.ResultCode.STARTED)
        self.assertEqual(results[2].result.code, SessionResult.ResultCode.PASSED)

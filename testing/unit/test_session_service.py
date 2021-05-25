"""Unit tests for session server"""

import unittest

from session_server import SessionServer, TestingSessionServerClient
from forch.proto.shared_constants_pb2 import PortBehavior
from daq.proto.session_server_pb2 import SessionResult


TEST_MAC_ADDRESS = 'aa:bb:cc:dd:ee:ff'


class SessionServerTest(unittest.TestCase):
    """Test basic session server operation"""

    def setUp(self):
        self._server_results = []
        self._server = SessionServer(self._new_connection)
        self._server.start()
        self._server.connect(TEST_MAC_ADDRESS, self._callback)

    def tearDown(self):
        self._server.stop()

    def _callback(self, port_event):
        pass

    def _new_connection(self, result):
        print('receive result')
        self._server_results.append(result)
        self._server.send_device_result(TEST_MAC_ADDRESS, PortBehavior.passed)
        self._server.close_stream(TEST_MAC_ADDRESS)

    # pylint: disable=no-member
    def test_server_connect(self):
        """Simple server connetion test"""
        client = TestingSessionServerClient()
        session = client.start_session(TEST_MAC_ADDRESS)
        print('session running')
        results = list(session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].endpoint.ip, 'ip-' + TEST_MAC_ADDRESS)
        self.assertEqual(results[1].result.code, SessionResult.ResultCode.STARTED)
        self.assertEqual(len(self._server_results), 1)
        self.assertEqual(self._server_results[0].device_mac, TEST_MAC_ADDRESS)

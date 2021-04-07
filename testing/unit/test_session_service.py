"""Unit tests for session server"""

import os
import time
import unittest
from unittest.mock import patch

import proto.session_server_pb2_grpc as server_grpc
from proto.session_server_pb2 import SessionParams, SessionProgress

from session_server import SessionServer, SessionServerClient
from utils import proto_dict


TEST_MAC_ADDRESS = 'aa:bb:cc:dd:ee:ff'


class SessionServerTest(unittest.TestCase):
    """Test basic session server operation"""

    def setUp(self):
        self._server = SessionServer(self._receive_result)
        self._server.start()
        self._server_results = []

    def tearDown(self):
        self._server.stop()

    def _receive_result(self, result):
        print('receive result')
        self._server_results.append(result)
        
    def test_server_connect(self):
        client = SessionServerClient()
        session = client.start_session(TEST_MAC_ADDRESS)
        print('session running')
        results = list(session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[1].endpoint_ip, 'b')
        self.assertEqual(len(self._server_results), 1)
        self.assertEqual(self._server_results[0].device_mac, TEST_MAC_ADDRESS)


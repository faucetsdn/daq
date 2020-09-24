"""gRPC client to send device testing result"""

import grpc

from forch.proto.grpc.device_testing_pb2_grpc import DeviceTestingStub
from forch.proto.device_testing_state_pb2 import DeviceTestingState

_SERVER_ADDRESS_DEFAULT = '127.0.0.1'
_SERVER_PORT_DEFAULT = 50051


class DeviceTestingClient:
    """gRPC client to send device testing result"""
    def __init__(self, server_address=_SERVER_ADDRESS_DEFAULT, server_port=_SERVER_PORT_DEFAULT):
        self._initialize_stub(server_address, server_port)

    def _initialize_stub(self, sever_address, server_port):
        channel = grpc.insecure_channel(f'{sever_address}:{server_port}')
        self._stub = DeviceTestingStub(channel)

    def send_testing_result(self, mac, testing_result):
        """Send testing result of a device to server"""
        self._stub.ReportTestingState(DeviceTestingState(mac=mac, port_behavior=testing_result))

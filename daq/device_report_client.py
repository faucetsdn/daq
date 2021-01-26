"""gRPC client to send device result"""

import threading
import grpc

from forch.proto.grpc.device_report_pb2_grpc import DeviceReportStub
from forch.proto.devices_state_pb2 import DevicesState, Device

from utils import dict_proto

_SERVER_ADDRESS_DEFAULT = '127.0.0.1'
_SERVER_PORT_DEFAULT = 50051


class DeviceReportClient:
    """gRPC client to send device result"""
    def __init__(self, server_address=_SERVER_ADDRESS_DEFAULT, server_port=_SERVER_PORT_DEFAULT):
        self._initialize_stub(server_address, server_port)

    def _initialize_stub(self, sever_address, server_port):
        channel = grpc.insecure_channel(f'{sever_address}:{server_port}')
        self._stub = DeviceReportStub(channel)

    def send_device_result(self, mac, device_result):
        """Send device result of a device to server"""
        devices_state = {
            'device_mac_behaviors': {
                mac: {'port_behavior': device_result}
            }
        }
        self._stub.ReportDevicesState(dict_proto(devices_state, DevicesState))

    def _port_event_handler(self, mac, callback):
        device = {
            "mac": mac
        }
        for port_event in self._stub.GetPortState(dict_proto(device, Device)):
            callback(port_event)

    def get_port_events(self, mac, callback):
        """Gets remote port events"""
        threading.Thread(target=self._port_event_handler, args=(mac, callback)).start()

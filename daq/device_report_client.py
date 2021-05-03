"""gRPC client to send device results"""

import threading
import grpc

from forch.proto.grpc.device_report_pb2_grpc import DeviceReportStub
from forch.proto.devices_state_pb2 import DevicesState, Device

from utils import dict_proto

DEFAULT_SERVER_ADDRESS = '127.0.0.1'
DEFAULT_SERVER_PORT = 50051
DEFAULT_RPC_TIMEOUT_SEC = 10

class DeviceReportClient:
    """gRPC client to send device results"""
    def __init__(self, server_address=DEFAULT_SERVER_ADDRESS, server_port=DEFAULT_SERVER_PORT,
                 rpc_timeout_sec=None):
        channel = grpc.insecure_channel(f'{server_address}:{server_port}')
        self._stub = DeviceReportStub(channel)
        self._active_requests = []
        self._rpc_timeout_sec = (
            rpc_timeout_sec if rpc_timeout_sec is not None else DEFAULT_RPC_TIMEOUT_SEC)

    def start(self):
        """Start the client"""

    def send_device_result(self, mac, device_result):
        """Send device result of a device to server"""
        devices_state = {
            'device_mac_behaviors': {
                mac: {'port_behavior': device_result}
            }
        }
        self._stub.ReportDevicesState(dict_proto(devices_state, DevicesState),
                                      timeout=self._rpc_timeout_sec)

    def _port_event_handler(self, callback, result_generator, cancel_request):
        for port_event in result_generator:
            callback(port_event)
        self._active_requests.remove(cancel_request)

    def connect(self, mac, callback):
        """Connect to remote and start streaming port events back"""
        device = {"mac": mac}
        result_generator = self._stub.GetPortState(dict_proto(device, Device))

        def cancel_request():
            result_generator.cancel()

        self._active_requests.append(cancel_request)
        threading.Thread(target=self._port_event_handler,
                         args=(callback, result_generator, cancel_request)).start()

    def terminate(self):
        """Terminates all onging grpc calls"""
        for handler in self._active_requests:
            handler()

    def send_device_heartbeats(self):
        """Null function for sending device heartbeats"""

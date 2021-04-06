"""gRPC server to receive devices state"""

import abc
from concurrent import futures
from queue import Queue
import threading
import grpc

#import logger

#LOGGER = logger.get_logger('devtesting')

import proto.device_testing_pb2 as device_testing_pb2

DEFAULT_MAX_WORKERS = 10
DEFAULT_SERVER_PORT = 47808
DEFALUT_BIND_ADDRESS = '0.0.0.0'

class SessionProgressServicer(device_report_pb2.SessionProgressServicer):
    """gRPC servicer to receive devices state"""

    def __init__(self, on_receiving_result):
        super().__init__()
        self._on_receiving_result = on_receiving_result
        self._logger = get_logger('drserver')
        self._port_device_mapping = {}
        self._port_events_listeners = {}
        self._mac_assignments = {}
        self._lock = threading.Lock()

    def _get_port_event(self, device):
        port_state = PortBehavior.PortState.up if device.port_up else PortBehavior.PortState.down
        return DevicePortEvent(state=port_state, device_vlan=device.vlan,
                               assigned_vlan=device.assigned)

    def _get_device(self, mac_addr):
        for device in self._port_device_mapping.values():
            if device.mac == mac_addr:
                return device
        return None

    def _send_device_port_event(self, device):
        if not device or device.mac not in self._port_events_listeners:
            return
        port_event = self._get_port_event(device)
        self._logger.info('Sending %d DevicePortEvent %s %s %s %s',
                          len(self._port_events_listeners[device.mac]), device.mac,
                          # pylint: disable=no-member
                          port_event.state, device.vlan, device.assigned)
        for queue in self._port_events_listeners[device.mac]:
            queue.put(port_event)

    def process_port_state(self, dp_name, port, state):
        """Process faucet port state events"""
        with self._lock:
            device = self._port_device_mapping.setdefault((dp_name, port), DeviceEntry())
        device.port_up = state
        if not state:
            device.assigned = None
            device.vlan = None
        self._send_device_port_event(device)

    def process_port_learn(self, dp_name, port, mac, vlan):
        """Process faucet port learn events"""
        with self._lock:
            device = self._port_device_mapping.setdefault((dp_name, port), DeviceEntry())
        device.mac = mac
        device.vlan = vlan
        device.port_up = True
        device.assigned = self._mac_assignments.get(mac)
        self._send_device_port_event(device)

    def process_port_assign(self, mac, assigned):
        """Process assigning a device to a vlan"""
        self._mac_assignments[mac] = assigned
        with self._lock:
            for mapping in self._port_device_mapping:
                device = self._port_device_mapping.get(mapping)
                if device.mac == mac:
                    device.assigned = assigned
                    self._send_device_port_event(device)
                    return

    # pylint: disable=invalid-name
    def ReportDevicesState(self, request, context):
        """RPC call for client to send devices state"""
        if not request:
            self._logger.warning('Received empty request in gRPC ReportDevicesState')
            return Empty()

        self._logger.info(
            'Received DevicesState of %d devices', len(request.device_mac_behaviors))
        # Closes DevicePortEvent streams in GetPortState
        for mac in request.device_mac_behaviors.keys():
            for queue in self._port_events_listeners.get(mac, []):
                queue.put(False)
        self._on_receiving_result(request)

        return Empty()

    # pylint: disable=invalid-name
    def GetPortState(self, request, context):
        listener_q = Queue()
        self._logger.info('Attaching response channel for device %s', request.mac)
        self._port_events_listeners.setdefault(request.mac, []).append(listener_q)
        device = self._get_device(request.mac)
        if device:
            yield self._get_port_event(device)
        while True:
            item = listener_q.get()
            if item is False:
                break
            yield item
        self._port_events_listeners[request.mac].remove(listener_q)


class SessionServer:
    """Devices state server"""

    def __init__(self, on_receiving_result, address=None, port=None, max_workers=None):
        self._server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=max_workers or DEFAULT_MAX_WORKERS))

        self._servicer = SessionProgressServicer(on_receiving_result)
        device_report_pb2.add_SessionProgressServicer_to_server(self._servicer, self._server)

        server_address_port = f'{address or DEFAULT_BIND_ADDRESS}:{port or DEFAULT_SERVER_PORT}'
        self._server.add_insecure_port(server_address_port)

    def start(self):
        """Start the server"""
        self._server.start()

    def stop(self):
        """Stop the server"""
        self._server.stop(grace=None)


def _receive_result(result):
    logger.info('Received result', result)


if __name__ == '__main__':
    SERVER = SessionServer(_receive_result)
    SERVER.start()

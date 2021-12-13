"""Server to handle incoming session requests"""

import grpc
import threading
import traceback

from device_coupler.utils import get_logger
from device_coupler.ovs_helper import OvsHelper

from daq.proto.session_server_pb2 import SessionParams, SessionResult
from daq.proto.session_server_pb2_grpc import SessionServerStub


DEFAULT_SERVER_ADDRESS = '127.0.0.1'
CONNECT_TIMEOUT_SEC = 60

# pylint: disable=too-many-arguments
class DeviceReportClient():
    """gRPC client to send device result"""

    def __init__(self, target, tunnel_ip, ovs_bridge):
        self._logger = get_logger('daqclient')
        self._logger.info('Using target %s', target)
        self._channel = grpc.insecure_channel(target)
        self._stub = None
        self._mac_sessions = {}
        self._lock = threading.Lock()
        self._tunnel_ip = tunnel_ip
        self._endpoint_handler = OvsHelper()
        self._ovs_bridge = ovs_bridge

    def start(self):
        """Start the client handler"""
        grpc.channel_ready_future(self._channel).result(timeout=CONNECT_TIMEOUT_SEC)
        self._stub = SessionServerStub(self._channel)

    def stop(self):
        """Stop client handler"""

    def _connect(self, mac, vlan, assigned):
        self._logger.info('Connecting %s to %s/%s', mac, vlan, assigned)
        session_params = SessionParams()
        session_params.device_mac = mac
        session_params.device_vlan = vlan
        session_params.assigned_vlan = assigned
        session_params.endpoint.ip = self._tunnel_ip or DEFAULT_SERVER_ADDRESS
        session = self._stub.StartSession(session_params)
        thread = threading.Thread(target=lambda: self._process_progress(mac, session))
        thread.start()
        self._logger.info('Connection of %s to %s/%s succeeded', mac, vlan, assigned)
        return session

    def disconnect(self, mac):
        with self._lock:
            session = self._mac_sessions.get(mac, {}).get('session')
            if session:
                session.cancel()
                mac_session = self._mac_sessions.pop(mac)
                index = mac_session['index']
                if self._endpoint_handler:
                    interface = "vxlan%s" % index
                    self._endpoint_handler.remove_vxlan_endpoint(interface, self._ovs_bridge)
                self._logger.info('Device %s disconnected', mac)
            else:
                self._logger.warning('Attempt to disconnect unconnected device %s', mac)

    def _convert_and_handle(self, mac, progress):
        endpoint = progress.endpoint
        result_code = progress.result.code
        assert not (endpoint.ip and result_code), 'both endpoint.ip and result.code defined'
        if result_code:
            result_name = SessionResult.ResultCode.Name(result_code)
            self._logger.info('Device report %s as %s', mac, result_name)
            return not result_name == 'STARTED' and not result_name == 'PENDING'
        if endpoint.ip:
            self._logger.info('Device report %s endpoint %s (handler=%s)',
                              mac, endpoint.__dir__, bool(self._endpoint_handler))
            # TODO: Associate mac to ip and interface
            if self._endpoint_handler:
                # TODO: Change the way indexes work. Check for VXLAN port being sent
                index = endpoint.vni
                device = self._mac_sessions[mac]
                device['index'] = index
                interface = "vxlan%s" % index
                self._endpoint_handler.remove_vxlan_endpoint(interface, self._ovs_bridge)
                self._endpoint_handler.create_vxlan_endpoint(interface, endpoint.ip, index)
                self._endpoint_handler.add_iface_to_bridge(self._ovs_bridge, interface, tag=device['device_vlan'])
        return False

    def _process_progress(self, mac, session):
        try:
            for progress in session:
                if self._convert_and_handle(mac, progress):
                    break
            self._logger.info('Progress complete for %s', mac)
        except Exception as e:
            self._logger.error('Progress exception: %s', e)
            self._logger.error('Traceback: %s', traceback.format_exc())
        self.disconnect(mac)

    def _process_session_ready(self, mac, device_vlan, assigned_vlan):
        if mac in self._mac_sessions:
            self._logger.info('Ignoring b/c existing session %s', mac)
            return
        self._logger.info('Device %s ready on %s/%s', mac, device_vlan, assigned_vlan)

        good_device_vlan = device_vlan and device_vlan != assigned_vlan
        if good_device_vlan:
            self._mac_sessions[mac] = {}
            self._mac_sessions[mac]['device_vlan'] = device_vlan
            self._mac_sessions[mac]['assigned_vlan'] = assigned_vlan
            self._mac_sessions[mac]['session'] = self._connect(mac, device_vlan, assigned_vlan)
        self._logger.info('Successfully wrapped _process_session_ready with mac session %s',
                          self._mac_sessions[mac])

    def process_device_discovery(self, mac, device_vlan, assigned_vlan):
        """Process discovery of device to be tested"""
        with self._lock:
            self._process_session_ready(mac, device_vlan, assigned_vlan)

"""Module to send gRPC requests to DAQ and manage test sessions"""

from __future__ import absolute_import

import grpc
import threading
import traceback

from device_coupler.utils import get_logger
from device_coupler.ovs_helper import OvsHelper

from daq.proto.session_server_pb2 import SessionParams, SessionResult
from daq.proto.session_server_pb2_grpc import SessionServerStub


DEFAULT_SERVER_ADDRESS = '127.0.0.1'
CONNECT_TIMEOUT_SEC = 60


class DAQClient():
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
        # Assigned VLAN is always set to 0 for non-FOT DAQ Client
        self._assigned_vlan = 0

    def start(self):
        """Start the client handler"""
        grpc.channel_ready_future(self._channel).result(timeout=CONNECT_TIMEOUT_SEC)
        self._stub = SessionServerStub(self._channel)

    def stop(self):
        """Stop client handler"""
        for mac in self._mac_sessions.keys():
            self._disconnect(mac)

    def _connect(self, mac, vlan):
        self._logger.info('Connecting %s with VLAN %s', mac, vlan)
        session_params = SessionParams()
        session_params.device_mac = mac
        session_params.device_vlan = vlan
        session_params.assigned_vlan = self._assigned_vlan
        session_params.endpoint.ip = self._tunnel_ip or DEFAULT_SERVER_ADDRESS
        session = self._stub.StartSession(session_params)
        thread = threading.Thread(target=lambda: self._run_test_session(mac, session))
        thread.start()
        self._logger.info('Connection of %s with VLAN %s succeeded', mac, vlan)
        return session

    def _disconnect(self, mac):
        with self._lock:
            session = self._mac_sessions.get(mac, {}).get('session')
            if session:
                session.cancel()
                mac_session = self._mac_sessions.pop(mac)
                index = mac_session['index']
                interface = "vxlan%s" % index
                self._endpoint_handler.remove_vxlan_endpoint(interface, self._ovs_bridge)
                self._logger.info('Session terminated for %s', mac)
            else:
                self._logger.warning('Attempt to disconnect unconnected device %s', mac)

    def _is_session_running(self, mac, progress):
        result = self._process_session_progress(mac, progress)
        return result not in ('PASSED', 'FAILED', 'ERROR')

    def _process_session_progress(self, mac, progress):
        endpoint = progress.endpoint
        result_code = progress.result.code
        assert not (endpoint.ip and result_code), 'both endpoint.ip and result.code defined'
        if result_code:
            result_name = SessionResult.ResultCode.Name(result_code)
            self._logger.info('Device report %s as %s', mac, result_name)
            return result_name
        if endpoint.ip:
            self._logger.info('Device report %s endpoint ip: %s)',
                              mac, endpoint.ip)
            # TODO: Change the way indexes work. Check for VXLAN port being sent
            index = endpoint.vni
            device = self._mac_sessions[mac]
            device['index'] = index
            interface = "vxlan%s" % index
            self._endpoint_handler.remove_vxlan_endpoint(interface, self._ovs_bridge)
            self._endpoint_handler.create_vxlan_endpoint(interface, endpoint.ip, index)
            self._endpoint_handler.add_iface_to_bridge(
                self._ovs_bridge, interface, tag=device['device_vlan'])
        return None

    def _run_test_session(self, mac, session):
        try:
            for progress in session:
                if not self._is_session_running(mac, progress):
                    break
            self._logger.info('Progress complete for %s', mac)
        except Exception as e:
            self._logger.error('Progress exception: %s', e)
            self._logger.error('Traceback: %s', traceback.format_exc())
        self._disconnect(mac)

    def _initiate_test_session(self, mac, device_vlan):
        if mac in self._mac_sessions:
            if device_vlan == self._mac_sessions[mac]['device_vlan']:
                self._logger.info('Test session for %s already exists. Ignoring.', mac)
                return
            self._logger.info('MAC learned on VLAN %s. Terminating current session.', device_vlan)
            self._disconnect(mac)

        self._logger.info('Initiating test session for %s on VLAN %s', mac, device_vlan)

        if device_vlan:
            self._mac_sessions[mac] = {}
            self._mac_sessions[mac]['device_vlan'] = device_vlan
            self._mac_sessions[mac]['session'] = self._connect(mac, device_vlan)
        self._logger.info('Initiated test session %s', self._mac_sessions[mac])

    def process_device_discovery(self, mac, device_vlan):
        """Process discovery of device to be tested"""
        # TODO: End existing test session and start new one if discovered on another vlan
        with self._lock:
            self._initiate_test_session(mac, device_vlan)

    def process_device_expiry(self, mac):
        """Process expiry of device"""
        self._logger.info('Terminating session for %s', mac)
        self._disconnect(mac)

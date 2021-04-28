"""Authenticator module"""
from __future__ import absolute_import
from eap_module import EapModule
from heartbeat_scheduler import HeartbeatScheduler
from radius_module import RadiusModule, RadiusPacketInfo, RadiusSocketInfo, port_id_to_int
from message_parser import IdentityMessage, FailureMessage
from utils import get_logger, get_interface_name, get_interface_ip, get_interface_mac, enable_debug_logs

import json
import threading
import time


class AuthStateMachine:
    """Authenticator state machine"""
    START = "start"
    SUPPLICANT = "Talk to Supplicant"
    RADIUS = "Talk to RADIUS server"
    FAIL = "Test Failed"
    SUCCESS = "Test Succeeded"

    def __init__(self, src_mac, auth_mac, idle_time, retry_count,
                 eap_send_callback, radius_send_callback, auth_callback):
        self.state = None
        self._state_lock = threading.Lock()
        self._timer_lock = threading.RLock()
        self.logger = get_logger('AuthSM')
        self.src_mac = src_mac
        self.eap_send_callback = eap_send_callback
        self.radius_send_callback = radius_send_callback
        self.auth_callback = auth_callback
        self.identity = None
        self.authentication_mac = auth_mac
        self.radius_state = None
        self._idle_time = idle_time
        self._max_retry_count = retry_count
        self._current_timeout = None
        self._retry_func = None
        self._retry_args = None
        self._current_retries = None

    def initialize(self):
        """Initialize state machine"""
        self._state_transition(self.START)
        self._set_timeout(self._idle_time)
        self._set_retry_actions(retry_func=self.eap_send_callback, retry_args=[self.src_mac])

    def _state_transition(self, target, expected=None):
        with self._state_lock:
            if expected is not None:
                message = 'state was %s expected %s' % (self.state, expected)
                assert self.state == expected, message
            self.logger.debug('Transition for %s: %s -> %s', self.src_mac, self.state, target)
            self.state = target

    def received_eapol_start(self):
        """Received EAPOL start on EAP socket"""
        self._state_transition(self.SUPPLICANT, self.START)
        self._set_timeout(self._idle_time)
        self._set_retry_actions(retry_func=self.eap_send_callback, retry_args=[self.src_mac])
        self.eap_send_callback(self.src_mac)

    def received_eap_request(self, eap_message):
        """Received EAP request"""
        if isinstance(eap_message, IdentityMessage) and not self.identity:
            self.identity = eap_message.identity
        self._state_transition(self.RADIUS, self.SUPPLICANT)
        port_id = port_id_to_int(self.authentication_mac)
        radius_packet_info = RadiusPacketInfo(
            eap_message, self.src_mac, self.identity, self.radius_state, port_id)
        self._set_timeout(self._idle_time)
        self._set_retry_actions(
            retry_func=self.radius_send_callback, retry_args=[radius_packet_info])
        self.radius_send_callback(radius_packet_info)

    def received_radius_response(self, payload, radius_state, packet_type):
        """Received RADIUS access channel"""
        self.radius_state = radius_state
        if packet_type == 'RadiusAccessReject':
            self._state_transition(self.FAIL, self.RADIUS)
            eap_message = FailureMessage(self.src_mac, 255)
            self.auth_callback(self.src_mac, False)
        else:
            eap_message = payload
            if packet_type == 'RadiusAccessAccept':
                self._state_transition(self.SUCCESS, self.RADIUS)
                self.auth_callback(self.src_mac, True)
            else:
                self._state_transition(self.SUPPLICANT, self.RADIUS)
                self._set_timeout(self._idle_time)
                self._set_retry_actions(
                    retry_func=self.eap_send_callback, retry_args=[self.src_mac, eap_message])
        self.eap_send_callback(self.src_mac, eap_message)

    def _set_timeout(self, timeout_time=None, clear=False):
        with self._timer_lock:
            if clear:
                self._current_timeout = None
            else:
                self._current_timeout = time.time() + timeout_time

    def _set_retry_actions(self, retry_func=None, retry_args=None):
        self._retry_func = retry_func
        self._retry_args = list(retry_args)
        self._current_retries = 0

    def _clear_retry_actions(self):
        self._retry_func = None
        self._retry_args = None
        self._current_retries = 0

    def handle_timer(self):
        """Handle timer and check if timeout is exceeded"""
        with self._timer_lock:
            if self._current_timeout:
                if time.time() > self._current_timeout:
                    if self._current_retries < self._max_retry_count:
                        self._current_retries += 1
                        self._set_timeout(self._idle_time)
                        self._retry_func(*self._retry_args)
                    else:
                        self._handle_timeout()

    def _handle_timeout(self):
        self._state_transition(self.FAIL)
        self._set_timeout(clear=True)
        eap_message = FailureMessage(self.src_mac, 255)
        self.auth_callback(self.src_mac, False)
        self.eap_send_callback(self.src_mac, eap_message)


class Authenticator:
    """Authenticator to manage Authentication flow"""

    HEARTBEAT_INTERVAL = 3
    IDLE_TIME = 9
    RETRY_COUNT = 3
    RADIUS_PORT = 1812
    EAPOL_IDLE_TIME = 180

    def __init__(self, config_file):
        self.state_machines = {}
        self.results = {}
        self.eap_module = None
        self.radius_module = None
        self.logger = get_logger('Authenticator')
        self._config_file = config_file
        self._threads = []
        self._radius_socket_info = None
        self._radius_secret = None
        self._radius_id = None
        self._interface = None
        self._idle_time = None
        self._max_retry_count = None
        self._current_timeout = None
        self._debug = False

        self._setup()

    def _load_config(self):
        with open(self._config_file, 'r') as file_stream:
            full_config = json.load(file_stream)
        config = full_config.get('modules').get('dot1x')

        self._debug = config.get('debug')
        if self._debug:
            enable_debug_logs(self.logger)

        self.logger.debug('Loaded config from %s:\n %s', self._config_file, config)

        self._interface = config.get('interface', get_interface_name())

        radius_config = config.get('radius_server', {})
        radius_socket_info = radius_config.get('radius_socket_info', {})

        listen_ip = radius_socket_info.get('listen_ip', get_interface_ip(self._interface))
        listen_port = radius_socket_info.get('listen_port', 0)
        remote_ip = radius_socket_info.get('remote_ip', '127.0.0.1')
        remote_port = radius_socket_info.get('remote_port', self.RADIUS_PORT)

        self._radius_socket_info = RadiusSocketInfo(listen_ip, listen_port, remote_ip, remote_port)
        self._radius_secret = radius_config.get('secret', 'SECRET')
        self._radius_id = radius_config.get('id', get_interface_mac(self._interface))

    def _setup(self):
        self._load_config()
        self.radius_module = RadiusModule(
            self._radius_socket_info, self._radius_secret,
            self._radius_id, self.received_radius_response)
        self.eap_module = EapModule(self._interface, self.received_eap_request)

        if self._debug:
            enable_debug_logs(self.radius_module.logger)
            enable_debug_logs(self.eap_module.logger)

        # TODO: Take value from config and then revert to default
        interval = self.HEARTBEAT_INTERVAL

        # TODO: Take value from config and then revert to default
        self._idle_time = self.IDLE_TIME
        self._max_retry_count = self.RETRY_COUNT

        self.sm_timer = HeartbeatScheduler(interval)
        self.sm_timer.add_callback(self.handle_sm_timeout)

        self._current_timeout = time.time() + self.EAPOL_IDLE_TIME

    def start_threads(self):
        self.logger.info('Starting SM timer')
        self.sm_timer.start()

        self.logger.info('Listening for EAP and RADIUS.')

        def build_thread(method):
            self._threads.append(threading.Thread(target=method))

        build_thread(self.radius_module.receive_radius_messages)
        build_thread(self.radius_module.send_radius_messages)
        build_thread(self.eap_module.receive_eap_messages)
        build_thread(self.eap_module.send_eap_messages)

        for thread in self._threads:
            thread.start()

        for thread in self._threads:
            thread.join()

        self.logger.info('Done listening for EAP and RADIUS packets.')

    def _end_authentication(self):
        self.logger.info('Stopping timer')
        if self.sm_timer:
            self.sm_timer.stop()
        self.logger.info('Shutting down modules.')
        self.radius_module.shut_down_module()
        self.eap_module.shut_down_module()

    def received_eap_request(self, src_mac, eap_message, is_eapol):
        if is_eapol:
            if not (src_mac in self.state_machines or src_mac in self.results):
                self.logger.info('Starting authentication for %s' % (src_mac))
                auth_mac = self.eap_module.get_auth_mac()
                state_machine = AuthStateMachine(
                    src_mac, auth_mac,
                    self._idle_time, self._max_retry_count,
                    self.send_eap_response, self.send_radius_request,
                    self.process_test_result)
                state_machine.initialize()
                self.state_machines[src_mac] = state_machine
                state_machine.received_eapol_start()
            else:
                self.logger.warning(
                    'Authentication for %s is in progress or has been completed' % (src_mac))
        else:
            state_machine = self.state_machines[src_mac]
            state_machine.received_eap_request(eap_message)

    def received_radius_response(self, src_mac, radius_attributes, packet_type):
        eap_message = radius_attributes.eap_message
        radius_state = radius_attributes.state
        state_machine = self.state_machines[src_mac]
        state_machine.received_radius_response(eap_message, radius_state, packet_type)

    def send_eap_response(self, src_mac, message=None):
        if not message:
            self.eap_module.send_eapol_response(src_mac)
        else:
            self.eap_module.send_eap_message(src_mac, message)

    def send_radius_request(self, radius_packet_info):
        self.radius_module.send_radius_packet(radius_packet_info)

    def process_test_result(self, src_mac, is_success):
        if is_success:
            self.logger.info('Authentication successful for %s' % (src_mac))
        else:
            if src_mac:
                self.logger.info('Authentication failed for %s' % (src_mac))
            else:
                self.logger.info('Authentication failed. Received no EAPOL packets.')
        if src_mac:
            self.results[src_mac] = is_success
            self.state_machines.pop(src_mac)
        # TODO: We currently finalize results as soon as we get a result for a src_mac.
        # Needs to be changed if we support multiple devices.
        self._end_authentication()

    def run_authentication_test(self):
        self.start_threads()
        result_str = ""
        test_result = ""
        if not self.results:
            result_str = "Authentication failed. No EAPOL messages received."
            test_result = "skip"
        else:
            test_result = "pass"
            for src_mac, is_success in self.results.items():
                if is_success:
                    result = 'succeeded'
                else:
                    result = 'failed'
                    test_result = "fail"
                result_str += "Authentication for %s %s." % (src_mac, result)
        return result_str, test_result

    def handle_sm_timeout(self):
        if not self.state_machines and self._current_timeout:
            if time.time() > self._current_timeout:
                self.process_test_result(None, False)
        else:
            for state_machine in self.state_machines.values():
                state_machine.handle_timer()


def main():
    authenticator = Authenticator()
    print(authenticator.run_authentication_test())


if __name__ == '__main__':
    main()

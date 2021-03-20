"""Authenticator module"""
from __future__ import absolute_import
from eap_module import EapModule
from radius_module import RadiusModule, RadiusPacketInfo, RadiusSocketInfo, port_id_to_int
from message_parser import IdentityMessage, FailureMessage
from utils import get_logger

import threading


class AuthStateMachine:
    """Authenticator state machine"""
    START = "start"
    SUPPLICANT = "Talk to Supplicant"
    RADIUS = "Talk to RADIUS server"
    FAIL = "Test Failed"
    SUCCESS = "Test Succeeded"

    def __init__(self, src_mac, auth_mac, eap_send_callback, radius_send_callback, auth_callback):
        self.state = self.START
        self._state_lock = threading.Lock()
        self.logger = get_logger('AuthStateMachine')
        self.src_mac = src_mac
        self.eap_send_callback = eap_send_callback
        self.radius_send_callback = radius_send_callback
        self.auth_callback = auth_callback
        self.identity = None
        self.authentication_mac = auth_mac
        self.radius_state = None
        self.logger = get_logger('AuthSM')

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
        self.eap_send_callback(self.src_mac)

    def received_eap_request(self, eap_message):
        """Received EAP request"""
        if isinstance(eap_message, IdentityMessage) and not self.identity:
            self.identity = eap_message.identity
        self._state_transition(self.RADIUS, self.SUPPLICANT)
        port_id = port_id_to_int(self.authentication_mac)
        radius_packet_info = RadiusPacketInfo(
            eap_message, self.src_mac, self.identity, self.radius_state, port_id)
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
        self.eap_send_callback(self.src_mac, eap_message)


class Authenticator:
    """Authenticator to manage Authentication flow"""

    def __init__(self):
        self.state_machines = {}
        self.results = {}
        self.eap_module = None
        self.radius_module = None
        self.logger = get_logger('Authenticator')
        self._threads = []

        self._setup()

    def _setup(self):
        radius_socket_info = RadiusSocketInfo('10.20.0.3', 0, '127.0.0.1', 1812)
        self.radius_module = RadiusModule(
            radius_socket_info, 'SECRET', '02:42:ac:18:00:70', self.received_radius_response)
        self.eap_module = EapModule('dot1x01-eth0', self.received_eap_request)

    def start_threads(self):
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
                    self.send_eap_response, self.send_radius_request,
                    self.process_test_result)
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
            self.logger.info('Authentication failed for %s' % (src_mac))
        self.results[src_mac] = is_success
        self.state_machines.pop(src_mac)
        # TODO: We currently finalize results as soon as we get a result for a src_mac.
        # Needs to be changed if we support multiple devices.
        self._end_authentication()

    def run_authentication_test(self):
        self.start_threads()
        result_str = ""
        for src_mac, is_success in self.results.items():
            result = 'succeeded' if is_success else 'failed'
            result_str += "Authentication for %s %s." % (src_mac, result)
        return result_str


def main():
    authenticator = Authenticator()
    print(authenticator.run_authentication_test())


if __name__ == '__main__':
    main()

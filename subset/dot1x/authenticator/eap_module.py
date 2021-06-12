"""EAP module to send/receive EAP packets"""
from __future__ import absolute_import
from message_parser import MessageParser, MessagePacker, IdentityMessage, EapolStartMessage
from mac_address import MacAddress
from eap_socket import EapSocket
from eap import Eap
from utils import MessageParseError, get_logger

from queue import Queue
import threading
import time


class EapModule:
    """Module to send, receive and process EAP packets"""

    def __init__(self, interface, auth_callback=None):
        self.eap_socket = None
        self.logger = get_logger('EapModule')
        self.interface = interface
        self.auth_callback = auth_callback
        self.authenticator_mac = None
        self.outbound_message_queue = Queue()
        self.shut_down = False

        self.setup_eap_socket()

    def setup_eap_socket(self):
        """Setup EAP socket"""
        self.eap_socket = EapSocket(self.interface, 'eap_socket')
        self.eap_socket.setup()

    def receive_eap_messages(self):
        """receive eap messages from supplicant."""
        while not self.shut_down:
            time.sleep(0)
            self.logger.debug("Waiting for eap messages")
            packed_message = self.eap_socket.receive()
            if not packed_message:
                continue
            self.logger.debug("Received packed_message: %s", str(packed_message))
            try:
                eap, dst_mac = MessageParser.ethernet_parse(packed_message)
            except MessageParseError as exception:
                self.logger.warning(
                    "MessageParser.ethernet_parse threw exception.\n"
                    " packed_message: '%s'.\n"
                    " exception: '%s'.",
                    packed_message,
                    exception)
                continue

            self.logger.debug("Received eap message: %s" % (str(eap)))

            is_eapol = False
            if isinstance(eap, EapolStartMessage):
                is_eapol = True
                self.authenticator_mac = self.eap_socket.eap_address
            if self.auth_callback:
                self.auth_callback(str(eap.src_mac), eap, is_eapol)

        self.logger.info('Done receiving EAP messages')

    def get_auth_mac(self):
        return str(self.authenticator_mac)

    def send_eapol_response(self, src_mac):
        """Respond to a EAPOL and read response"""
        src_mac_address = MacAddress.from_string(src_mac)
        port_id = self.authenticator_mac
        _id = 255
        data = IdentityMessage(src_mac, _id, Eap.REQUEST, "")
        self.send_packed_eap_message(MessagePacker.ethernet_pack(data, port_id, src_mac_address))

    def send_eap_message(self, src_mac, data):
        src_mac_address = MacAddress.from_string(src_mac)
        port_id = self.authenticator_mac
        self.logger.debug('Packing eap message: src_mac: %s port_id: %s data: %s',
                          src_mac_address, port_id, data)
        packed_message = MessagePacker.ethernet_pack(data, port_id, src_mac_address)
        self.send_packed_eap_message(packed_message)

    def send_packed_eap_message(self, eap_message):
        self.logger.debug('Sending packed eap message %s', eap_message)
        self.outbound_message_queue.put(eap_message)

    def send_eap_messages(self):
        """send EAP messages forever."""
        while not self.shut_down:
            time.sleep(0)
            outbound_packet = self.outbound_message_queue.get()
            if outbound_packet:
                self.eap_socket.send(outbound_packet)

        self.logger.info('Done sending EAP messages')

    def shut_down_module(self):
        """Stop listening for and sending packets"""
        self.shut_down = True
        self.outbound_message_queue.put(None)
        self.eap_socket.shutdown()


def main():
    eap_module = EapModule('dot1x01-eth0')
    t1 = threading.Thread(target=eap_module.receive_eap_messages, daemon=True)

    t1.start()
    t1.join()


if __name__ == '__main__':
    main()

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

    def __init__(self, interface, auth_callback = None):
        self.eap_socket = None
        self.logger = get_logger('EapModule')
        self.interface = interface
        self.auth_callback = auth_callback
        self.authenticator_mac = None
        self.outbound_message_queue = Queue()

        self.setup_eap_socket()

    def setup_eap_socket(self):
        """Setup EAP socket"""
        log_prefix = "EapModule.EapSocket"
        self.eap_socket = EapSocket(self.interface, 'eap_socket')
        self.eap_socket.setup()

    def receive_eap_messages(self):
        """receive eap messages from supplicant forever."""
        while True:
            time.sleep(0)
            self.logger.debug("Waiting for eap messages")
            packed_message = self.eap_socket.receive()
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
                self.authenticator_mac = dst_mac
                #self.send_eapol_response(str(eap.src_mac))
            if self.auth_callback:
                self.auth_callback(str(eap.src_mac), eap, is_eapol)

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
        packed_message = MessagePacker.ethernet_pack(data, port_id, src_mac_address)
        self.send_packed_eap_message(packed_message)

    def send_packed_eap_message(self, eap_message):
        self.outbound_message_queue.put(eap_message)

    def send_eap_messages(self):
        """send RADIUS messages to RADIUS Server forever."""
        while True:
            time.sleep(0)
            outbound_packet = self.outbound_message_queue.get()
            self.eap_socket.send(outbound_packet)


def main():
    eap_module = EapModule('eth0')
    t1 = threading.Thread(target=eap_module.receive_eap_messages, daemon=True)

    t1.start()
    t1.join()

if __name__ == '__main__':
    main()


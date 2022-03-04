"""RADIUS module to send/receive RADIUS packets"""
from __future__ import absolute_import
from eap import Eap
from message_parser import MessagePacker, IdentityMessage
from mac_address import MacAddress
from radius import Radius
from radius_socket import RadiusSocket
from radius_attributes import State, CalledStationId, NASIdentifier, NASPortType, EAPMessage
from utils import MessageParseError, get_logger

import collections
import os
import struct
import threading
import time
from queue import Queue

RadiusSocketInfo = collections.namedtuple(
    'RadiusSocketInfo', 'source_ip, source_port, server_ip, server_port')
RadiusPacketInfo = collections.namedtuple(
    'RadiusPacketInfo', 'payload, src_mac, identity, state, port_id')
RadiusPacketAttributes = collections.namedtuple('RadiusPacketAttributes', 'eap_message, state')


def port_id_to_int(port_id):
    """"Convert a port_id str '00:00:00:aa:00:01 to integer'"""
    dp, port_half_1, port_half_2 = str(port_id).split(':')[3:]
    port = port_half_1 + port_half_2
    return int.from_bytes(
        struct.pack('!HH', int(dp, 16),  # pytype: disable=attribute-error
                    int(port, 16)), 'big')


class RadiusModule:
    """Module to send, receive and process EAP packets"""

    def __init__(self, socket_info, secret, module_id, auth_callback=None):
        self.socket_info = socket_info
        self.radius_secret = secret
        self.radius_socket = None
        self.logger = get_logger('RadiusModule')
        self.setup_radius_socket()
        self.outbound_message_queue = Queue()
        self.next_radius_id = 0
        self.radius_secret = secret
        self.packet_id_to_request_authenticator = {}
        self.packet_id_to_mac = {}
        self.module_id = module_id
        self.auth_callback = auth_callback
        self.shut_down = False

    def setup_radius_socket(self):
        """Setup RADIUS socket"""
        self.radius_socket = RadiusSocket(self.socket_info.source_ip, self.socket_info.source_port,
                                          self.socket_info.server_ip, self.socket_info.server_port)
        self.radius_socket.setup()

    def send_radius_messages(self):
        """send RADIUS messages to RADIUS Server forever."""
        while not self.shut_down:
            time.sleep(0)
            outbound_packet = self.outbound_message_queue.get()
            if outbound_packet:
                packed_message = self._encode_radius_response(outbound_packet)
                self.radius_socket.send(packed_message)
                self.logger.info("sent radius message %s" % (packed_message))

        self.logger.info('Done sending RADIUS packets')

    def receive_radius_messages(self):
        """receive radius messages from supplicant."""
        while not self.shut_down:
            time.sleep(0)
            self.logger.debug("Waiting for radius packets")
            packed_message = self.radius_socket.receive()
            if self.shut_down:
                continue
            self.logger.debug("Received packed_message: %s", str(packed_message))
            try:
                radius = self._decode_radius_response(packed_message)
            except MessageParseError as exception:
                self.logger.warning(
                    "MessageParser.radius_parse threw exception.\n"
                    " packed_message: '%s'.\n"
                    " exception: '%s'.",
                    packed_message,
                    exception)
                continue
            self.logger.debug("Received RADIUS message: %s" % (str(radius)))
            packet_type = type(radius).__name__
            eap_message = None
            state = None
            for attribute in radius.attributes.attributes:
                if isinstance(attribute, EAPMessage):
                    eap_message = attribute.data()
                if isinstance(attribute, State):
                    state = attribute.data()
            radius_attributes = RadiusPacketAttributes(eap_message, state)
            src_mac, port_id = self.packet_id_to_mac[radius.packet_id].values()
            self.logger.debug(
                "src_mac %s port_id %s attributes %s"
                % (src_mac, port_id, str(radius_attributes)))
            if self.auth_callback:
                self.auth_callback(src_mac, radius_attributes, packet_type)

        self.logger.info('Done receiving RADIUS packets')

    def _decode_radius_response(self, packed_message):
        return Radius.parse(
            packed_message, self.radius_secret, self.packet_id_to_request_authenticator)

    def _encode_radius_response(self, packet_info):
        self.logger.debug(
            "Sending Radius Packet. Mac %s, identity: %s "
            % (packet_info.src_mac, packet_info.identity))

        self.logger.debug(
            "Sending to RADIUS payload %s with state %s"
            % (packet_info.payload.__dict__, packet_info.state))

        radius_packet_id = self.get_next_radius_packet_id()
        self.packet_id_to_mac[radius_packet_id] = {
            'src_mac': packet_info.src_mac, 'port_id': packet_info.port_id}

        request_authenticator = self.generate_request_authenticator()
        self.packet_id_to_request_authenticator[radius_packet_id] = request_authenticator
        self.extra_radius_request_attributes = self._prepare_extra_radius_attributes()

        return MessagePacker.radius_pack(packet_info.payload, packet_info.src_mac,
                                         packet_info.identity,
                                         radius_packet_id, request_authenticator, packet_info.state,
                                         self.radius_secret,
                                         packet_info.port_id,
                                         self.extra_radius_request_attributes)

    def send_opening_packet(self):
        mac = '02:42:ac:17:00:6f'
        _id = 208
        identity = 'user'
        payload = IdentityMessage(
            MacAddress.from_string("01:80:C2:00:00:03"), _id, Eap.RESPONSE, identity)
        state = None
        port_id = port_id_to_int('01:80:c2:00:00:03')
        self.send_radius_packet(RadiusPacketInfo(payload, mac, identity, state, port_id))

    def send_radius_packet(self, radius_packet_info):
        self.outbound_message_queue.put(radius_packet_info)

    def get_next_radius_packet_id(self):
        """Calulate the next RADIUS Packet ID
        Returns:
            int
        """
        radius_id = self.next_radius_id
        self.next_radius_id = (self.next_radius_id + 1) % 256

        return radius_id

    def generate_request_authenticator(self):
        """Workaround until we get this extracted for easy mocking"""
        return os.urandom(16)

    def _prepare_extra_radius_attributes(self):
        """Create RADIUS Attirbutes to be sent with every RADIUS request"""
        attr_list = [CalledStationId.create(self.module_id),
                     NASPortType.create(15),
                     NASIdentifier.create(self.module_id)]
        return attr_list

    def shut_down_module(self):
        """Stop listening for and sending packets"""
        self.shut_down = True
        self.outbound_message_queue.put(None)
        self.radius_socket.shutdown()


def main():
    socket_info = RadiusSocketInfo('172.24.0.112', 0, '172.24.0.113', 1812)
    radius_module = RadiusModule(socket_info, 'SECRET', '02:42:ac:18:00:70')
    t1 = threading.Thread(target=radius_module.receive_radius_messages, daemon=True)
    t2 = threading.Thread(target=radius_module.send_radius_messages, daemon=True)

    radius_module.send_opening_packet()

    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == '__main__':
    main()

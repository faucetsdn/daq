""""""
from __future__ import absolute_import
from auth_8021x import Auth8021x
from eap import Eap, EapIdentity, EapMd5Challenge, EapSuccess, EapFailure, EapLegacyNak, \
    EapTTLS, EapTLS, EapPEAP, PARSERS_TYPES
from ethernet_packet import EthernetPacket
from radius import RadiusAttributesList, RadiusAccessRequest, Radius
from radius_attributes import CallingStationId, UserName, MessageAuthenticator, EAPMessage, \
    NASPort, UserPassword, State
from utils import MessageParseError


class EapMessage:
    src_mac = None
    message_id = None

    def __init__(self, src_mac, message_id):
        self.src_mac = src_mac
        self.message_id = message_id

    def __str__(self):
        _id = self.message_id
        if _id is None:
            _id = -1
        return "'%s': src_mac: '%s', id: '%d'" % (self.__class__.__name__, self.src_mac, _id)


class SuccessMessage(EapMessage):

    @classmethod
    def build(cls, src_mac, eap):
        return cls(src_mac, eap.packet_id)


class FailureMessage(EapMessage):

    @classmethod
    def build(cls, src_mac, eap):
        return cls(src_mac, eap.packet_id)


class IdentityMessage(EapMessage):
    def __init__(self, src_mac, message_id, code, identity):
        super().__init__(src_mac, message_id)
        self.code = code
        self.identity = identity

    def __str__(self):
        return "%s, code: '%d', identity: '%s'" % (super().__str__(), self.code, self.identity)

    @classmethod
    def build(cls, src_mac, eap):
        return cls(src_mac, eap.packet_id, eap.code, eap.identity)


class LegacyNakMessage(EapMessage):
    def __init__(self, src_mac, message_id, code, desired_auth_types):
        super().__init__(src_mac, message_id)
        self.code = code
        self.desired_auth_types = desired_auth_types

    def __str__(self):
        return "%s, code: '%d', desired_auth_types: '%s'" \
               % (super().__str__(), self.code, self.desired_auth_types)

    @classmethod
    def build(cls, src_mac, eap):
        return cls(src_mac, eap.packet_id, eap.code, eap.desired_auth_types)


class Md5ChallengeMessage(EapMessage):
    def __init__(self, src_mac, message_id, code, challenge, extra_data):
        super().__init__(src_mac, message_id)
        self.code = code
        self.challenge = challenge
        self.extra_data = extra_data

    def __str__(self):
        return "%s, code: '%d', challenge: '%s', extra_data: '%s'" \
               % (super().__str__(), self.code, self.challenge, self.extra_data)

    @classmethod
    def build(cls, src_mac, eap):
        return cls(src_mac, eap.packet_id, eap.code, eap.challenge, eap.extra_data)


class TlsMessageBase(EapMessage):
    """TLS and TTLS will extend this class, but TTLS cannot be same type as TLS"""

    def __init__(self, src_mac, message_id, code, flags, extra_data):
        super().__init__(src_mac, message_id)
        self.code = code
        self.flags = flags
        self.extra_data = extra_data

    def __str__(self):
        return "%s, code: '%d', flags: '%s', extra_data: '%s'" \
               % (super().__str__(), self.code, self.flags, self.extra_data)

    @classmethod
    def build(cls, src_mac, eap):
        return cls(src_mac, eap.packet_id, eap.code, eap.flags, eap.extra_data)


class TlsMessage(TlsMessageBase):
    pass


class TtlsMessage(TlsMessageBase):
    pass


class PeapMessage(TlsMessageBase):
    pass


class EapolStartMessage(EapMessage):
    def __init__(self, src_mac):
        super().__init__(src_mac, None)

    @classmethod
    def build(cls, src_mac):
        return cls(src_mac)


class EapolLogoffMessage(EapMessage):
    def __init__(self, src_mac):
        super().__init__(src_mac, None)

    @classmethod
    def build(cls, src_mac):
        return cls(src_mac)


EAP_MESSAGES = {
    Eap.IDENTITY: IdentityMessage,
    Eap.MD5_CHALLENGE: Md5ChallengeMessage,
    Eap.LEGACY_NAK: LegacyNakMessage,
    Eap.TLS: TlsMessage,
    Eap.TTLS: TtlsMessage,
    Eap.PEAP: PeapMessage,
}

AUTH_8021X_MESSAGES = {
    0: "eap",
    1: "eapol start",
}


class MessageParser:
    @staticmethod
    def one_x_parse(data, src_mac):
        """Parses the 1x header (version and packet type) part of the packet, and the payload.
        Args:
            data:
            src_mac (MacAddress): source mac address of the data packet.
        Raises:
            MessageParseError: the data cannot be parsed."""
        auth_8021x = Auth8021x.parse(data)
        if auth_8021x.packet_type == 0:
            return MessageParser.eap_parse(auth_8021x.data, src_mac)
        elif auth_8021x.packet_type == 1:
            return EapolStartMessage.build(src_mac)
        elif auth_8021x.packet_type == 2:
            return EapolLogoffMessage.build(src_mac)
        raise MessageParseError("802.1x has bad type, expected 0: %s" % auth_8021x)

    @staticmethod
    def eap_parse(data, src_mac):
        """Parses the actual EAP payload
        Args:
            data:
            src_mac (MacAddress): source mac address of the data packet
        Raises:
            MessageParseError: the data cannot be parsed."""
        eap = Eap.parse(data)

        if isinstance(eap, tuple(PARSERS_TYPES.values())):
            return EAP_MESSAGES[eap.PACKET_TYPE].build(src_mac, eap)
        elif isinstance(eap, EapSuccess):
            return SuccessMessage.build(src_mac, eap)
        elif isinstance(eap, EapFailure):
            return FailureMessage.build(src_mac, eap)
        else:
            raise MessageParseError("Got bad Eap packet: %s" % eap)

    @staticmethod
    def ethernet_parse(packed_message):
        """Parses the ethernet header part, and payload
        Args:
            packed_message:
        Returns:
            ***Message & destination mac address.
        Raises:
            MessageParseError: the packed_message cannot be parsed."""
        ethernet_packet = EthernetPacket.parse(packed_message)
        if ethernet_packet.ethertype != 0x888e:
            raise MessageParseError("Ethernet packet with bad ethertype received: %s" %
                                    ethernet_packet)

        return MessageParser.one_x_parse(ethernet_packet.data, ethernet_packet.src_mac), \
            ethernet_packet.dst_mac

    @staticmethod
    def radius_parse(packed_message, secret, radius_lifecycle):
        """Parses a RADIUS packet
        Returns:
            RadiusPacket
        Raises:
            MessageParseError: the packed_message cannot be parsed"""
        parsed_radius = Radius.parse(packed_message, secret,
                                     radius_lifecycle=radius_lifecycle)
        return parsed_radius


class MessagePacker:
    @staticmethod
    def ethernet_pack(message, src_mac, dst_mac):
        """Packs a ethernet packet.
        Args:
            message: EAP payload
            src_mac (MacAddress):
            dst_mac (MacAddress):
        Returns:
            packed ethernet packet (bytes)
        """
        data = MessagePacker.pack(message)
        ethernet_packet = EthernetPacket(dst_mac=dst_mac, src_mac=src_mac,
                                         ethertype=0x888e, data=data)
        return ethernet_packet.pack()

    @staticmethod
    def radius_mab_pack(src_mac, radius_packet_id, request_authenticator, secret, nas_port):
        """"""

        attr_list = []
        no_dots_mac = str(src_mac).replace(':', "")
        attr_list.append(UserName.create(no_dots_mac))
        attr_list.append(CallingStationId.create(str(src_mac).replace(':', '-')))

        if nas_port:
            attr_list.append(NASPort.create(nas_port))

        ciphertext = UserPassword.encrypt(secret, request_authenticator, no_dots_mac)
        attr_list.append(UserPassword.create(ciphertext))

        attr_list.append(MessageAuthenticator.create(
            bytes.fromhex("00000000000000000000000000000000")))

        attributes = RadiusAttributesList(attr_list)
        access_request = RadiusAccessRequest(radius_packet_id, request_authenticator, attributes)
        return access_request.build(secret)

    @staticmethod
    def radius_pack(eap_message, src_mac, username, radius_packet_id,
                    request_authenticator, state, secret, nas_port=None, extra_attributes=None):
        """
        Packs up a RADIUS message to send to a RADIUS Server.
        Args:
            eap_message (Message): e.g. IdentityMessage
            src_mac (MacAddress): supplicants mac address
            username (str): supplicants username
            radius_packet_id (int):
            request_authenticator (bytes):
            state (State): RADIUS State
            secret (str): RADIUS secret used between Chewie and RADIUS Server
            extra_attributes (list): list of extra RADIUS attributes to send along with the above.

        Returns:
            packed RADIUS packet (bytes)
        """
        if not extra_attributes:
            extra_attributes = []

        attr_list = []
        attr_list.append(UserName.create(username))
        attr_list.append(CallingStationId.create(str(src_mac)))

        if nas_port:
            attr_list.append(NASPort.create(nas_port))

        attr_list.extend(extra_attributes)

        attr_list.append(EAPMessage.create(eap_message))

        if state:
            attr_list.append(State.create(state))

        attr_list.append(MessageAuthenticator.create(
            bytes.fromhex("00000000000000000000000000000000")))

        attributes = RadiusAttributesList(attr_list)
        access_request = RadiusAccessRequest(radius_packet_id, request_authenticator, attributes)
        return access_request.build(secret)

    @staticmethod
    def eap_pack(message):
        """
        Pack an EAP message.
        Args:
            message (Message):

        Returns:
            version (int), packet_type (int), packed eap (bytes)
        """
        if isinstance(message, IdentityMessage):

            eap = EapIdentity(message.code, message.message_id, message.identity)
            version = 1
            packet_type = 0
            data = eap.pack()
        elif isinstance(message, LegacyNakMessage):
            eap = EapLegacyNak(message.code, message.message_id, message.desired_auth_types)
            version = 1
            packet_type = 0
            data = eap.pack()
        elif isinstance(message, Md5ChallengeMessage):
            eap = EapMd5Challenge(message.code, message.message_id,
                                  message.challenge, message.extra_data)
            version = 1
            packet_type = 0
            data = eap.pack()
        elif isinstance(message, TlsMessage):
            eap = EapTLS(message.code, message.message_id, message.flags, message.extra_data)
            version = 1
            packet_type = 0
            data = eap.pack()
        elif isinstance(message, TtlsMessage):
            eap = EapTTLS(message.code, message.message_id, message.flags, message.extra_data)
            version = 1
            packet_type = 0
            data = eap.pack()
        elif isinstance(message, PeapMessage):
            eap = EapPEAP(message.code, message.message_id, message.flags, message.extra_data)
            version = 1
            packet_type = 0
            data = eap.pack()
        elif isinstance(message, SuccessMessage):
            eap = EapSuccess(message.message_id)
            version = 1
            packet_type = 0
            data = eap.pack()
        elif isinstance(message, FailureMessage):
            eap = EapFailure(message.message_id)
            version = 1
            packet_type = 0
            data = eap.pack()
        elif isinstance(message, EapolStartMessage):
            version = 1
            packet_type = 1
            data = b""
        elif isinstance(message, EapolLogoffMessage):
            version = 1
            packet_type = 2
            data = b""
        else:
            raise ValueError("Cannot pack message: %s" % message)
        return version, packet_type, data

    @staticmethod
    def pack(message):
        """
        packs the EAPOL
        Args:
            message (Message): EAP message

        Returns:
            Packed EAPOL packet (bytes)
        """
        version, packet_type, data = MessagePacker.eap_pack(message)
        auth_8021x = Auth8021x(version=version, packet_type=packet_type, data=data)
        return auth_8021x.pack()

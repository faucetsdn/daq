"""Module for parsing & packing EAP"""

# Ignore arguments differ on overridden functions due to changing inheritance hierarchies
# pylint: disable=arguments-differ

import struct
from utils import MessageParseError

EAP_HEADER_LENGTH = 1 + 1 + 2
EAP_TYPE_LENGTH = 1

PARSERS = {}
PARSERS_TYPES = {}


class Eap:
    """Class for parsing & packing EAP messages"""
    REQUEST = 1
    RESPONSE = 2
    SUCCESS = 3
    FAILURE = 4

    IDENTITY = 1
    LEGACY_NAK = 3
    MD5_CHALLENGE = 4
    TLS = 13
    TTLS = 21
    PEAP = 25

    code = None
    packet_id = None
    PACKET_TYPE = None

    @staticmethod
    def parse(packed_message):
        """

        Args:
            packed_message:
        Returns:
            Eap*** object.
        Raises:
            MessageParseError if packed_message cannot be parsed.
        """
        try:
            code, packet_id, length = struct.unpack("!BBH", packed_message[:EAP_HEADER_LENGTH])
        except struct.error as exception:
            raise MessageParseError("unable to unpack EAP header (4 bytes)") from exception

        if code in (Eap.REQUEST, Eap.RESPONSE):
            try:
                packet_type, = struct.unpack("!B",
                                             packed_message[EAP_HEADER_LENGTH:
                                                            EAP_HEADER_LENGTH + EAP_TYPE_LENGTH])
            except struct.error as exception:
                raise MessageParseError("EAP unable to unpack packet_type byte") \
                    from exception

            data = packed_message[EAP_HEADER_LENGTH + EAP_TYPE_LENGTH:length]
            try:
                return PARSERS[packet_type](code, packet_id, data)
            except KeyError as exception:
                raise MessageParseError("EAP packet_type: %s not supported" % packet_type) \
                    from exception
        elif code == Eap.SUCCESS:
            return EapSuccess(packet_id)
        elif code == Eap.FAILURE:
            return EapFailure(packet_id)
        raise MessageParseError("Got Eap packet with bad code: %s" % packed_message)

    def pack(self, packed_body):
        """Pack an EAP Message"""
        header = struct.pack("!BBHB", self.code, self.packet_id,
                             EAP_HEADER_LENGTH + EAP_TYPE_LENGTH + len(packed_body),
                             self.PACKET_TYPE)
        return header + packed_body


def register_parser(cls):
    """Register a packet type to the parser"""
    PARSERS[cls.PACKET_TYPE] = cls.parse
    PARSERS_TYPES[cls.PACKET_TYPE] = cls
    return cls


# pylint: disable=missing-docstring
@register_parser
class EapIdentity(Eap):
    PACKET_TYPE = Eap.IDENTITY

    def __init__(self, code, packet_id, identity):
        self.code = code
        self.packet_id = packet_id
        self.identity = identity

    @classmethod
    def parse(cls, code, packet_id, packed_message):
        """
        Returns:
            EapIdentity.
        Raises:
            MessageParseError if packed message cannot be decoded.
        """
        try:
            identity = packed_message.decode()
        except UnicodeDecodeError as exception:
            raise MessageParseError("%s unable to decode identity" % cls.__name__) from exception
        return cls(code, packet_id, identity)

    def pack(self):
        packed_identity = self.identity.encode()
        return super(EapIdentity, self).pack(packed_identity)

    def __repr__(self):
        return "%s(identity=%s)" % \
               (self.__class__.__name__, self.identity)


@register_parser
class EapMd5Challenge(Eap):
    """EAP MD5-Challenge Packet"""

    PACKET_TYPE = Eap.MD5_CHALLENGE

    def __init__(self, code, packet_id, challenge, extra_data):
        self.code = code
        self.packet_id = packet_id
        self.challenge = challenge
        self.extra_data = extra_data

    @classmethod
    def parse(cls, code, packet_id, packed_message):
        """
        Returns:
            EapMd5Challenge.
        Raises:
            MessageParseError if cannot unpack packed_message
        """
        try:
            value_length, = struct.unpack("!B", packed_message[:1])
        except struct.error as exception:
            raise MessageParseError("%s unable to unpack first byte" % cls.__name__) \
                from exception
        challenge = packed_message[1:1 + value_length]
        extra_data = packed_message[1 + value_length:]
        return cls(code, packet_id, challenge, extra_data)

    def pack(self):
        value_length = struct.pack("!B", len(self.challenge))
        packed_md5_challenge = value_length + self.challenge + self.extra_data
        return super(EapMd5Challenge, self).pack(packed_md5_challenge)

    def __repr__(self):
        return "%s(challenge=%s, extra_data=%s)" % \
               (self.__class__.__name__, self.challenge, self.extra_data)


class EapSuccess(Eap):
    """EAP Success Packet"""
    def __init__(self, packet_id):
        self.packet_id = packet_id

    @classmethod
    def parse(cls, packet_id):
        return cls(packet_id)

    def pack(self):
        return struct.pack("!BBH", Eap.SUCCESS, self.packet_id, EAP_HEADER_LENGTH)

    def __repr__(self):
        return "%s(packet_id=%s)" % \
               (self.__class__.__name__, self.packet_id)


class EapFailure(Eap):
    """EAP Failure Packet"""
    def __init__(self, packet_id):
        self.packet_id = packet_id

    @classmethod
    def parse(cls, packet_id):
        return cls(packet_id)

    def pack(self):
        return struct.pack("!BBH", Eap.FAILURE, self.packet_id, EAP_HEADER_LENGTH)

    def __repr__(self):
        return "%s(packet_id=%s)" % \
               (self.__class__.__name__, self.packet_id)


@register_parser
class EapLegacyNak(Eap):
    """EAP Legacy-NAK Packet"""
    PACKET_TYPE = Eap.LEGACY_NAK

    def __init__(self, code, packet_id, desired_auth_types):
        self.code = code
        self.packet_id = packet_id
        self.desired_auth_types = desired_auth_types

    @classmethod
    def parse(cls, code, packet_id, packed_msg):
        """
        Returns:
            EapLegacyNak.
        Raises:
            MessageParseError if cannot unpack packed_message
        """
        value_len = len(packed_msg)
        try:
            desired_auth_types = struct.unpack("!%ds" % value_len, packed_msg)
        except struct.error as exception:
            raise MessageParseError("%s unable to unpack." % cls.__name__) from exception
        return cls(code, packet_id, desired_auth_types)

    def pack(self):
        packed_legacy_nak = struct.pack("!%ds" % len(self.desired_auth_types),
                                        *self.desired_auth_types)  # pytype: disable=wrong-arg-types
        return super(EapLegacyNak, self).pack(packed_legacy_nak)

    def __repr__(self):
        return "%s(packet_id=%s, desired_auth_types=%s)" % \
               (self.__class__.__name__, self.packet_id, self.desired_auth_types)


class EapTLSBase(Eap):
    """EAPTLS & EAPTTLS have the same packet format."""

    def __init__(self, code, packet_id, flags, extra_data):
        self.code = code
        self.packet_id = packet_id
        self.flags = flags
        self.extra_data = extra_data

    @classmethod
    def parse(cls, code, packet_id, packed_msg):
        """
        Returns:
            A child of EapTLSBase e.g. EapTLS, EAPTTLS.
        Raises:
            MessageParseError if cannot unpack packed_message
        """
        value_len = len(packed_msg)
        fmt_str = "!B"
        if value_len > 1:
            fmt_str += "%ds" % (value_len - 1)
        try:
            unpacked = struct.unpack(fmt_str, packed_msg)
        except struct.error as exception:
            raise MessageParseError("%s unable to unpack" % cls.__name__) from exception
        extra_data = b""
        if value_len > 1:
            flags, extra_data = unpacked
        else:
            flags = unpacked[0]

        return cls(code, packet_id, flags, extra_data)

    def pack(self):
        if self.extra_data:
            packed = struct.pack("!B%ds" % len(self.extra_data), self.flags, self.extra_data)
        else:
            packed = struct.pack("!B", self.flags)
        return super().pack(packed)

    def __repr__(self):
        return "%s(packet_id=%s, flags=%s, extra_data=%s)" % \
               (self.__class__.__name__, self.packet_id, self.flags, self.extra_data)


@register_parser
class EapTLS(EapTLSBase):
    """EAP TLS Packet"""
    PACKET_TYPE = Eap.TLS


@register_parser
class EapTTLS(EapTLSBase):
    """EAP TTLS Packet"""
    PACKET_TYPE = Eap.TTLS


@register_parser
class EapPEAP(EapTLSBase):
    """PEAP Packet"""
    PACKET_TYPE = Eap.PEAP

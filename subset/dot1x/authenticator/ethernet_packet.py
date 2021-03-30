"""This module is used to allow parsing and packing of Ethernet Packets"""
import struct

from mac_address import MacAddress
from utils import MessageParseError

ETHERNET_HEADER_LENGTH = 6 + 6 + 2


class EthernetPacket:
    """Packet/parsers for an IEEE 802.3 Ethernet frame"""

    def __init__(self, dst_mac, src_mac, ethertype, data):
        self.dst_mac = dst_mac
        self.src_mac = src_mac
        self.ethertype = ethertype
        self.data = data

    @classmethod
    def parse(cls, packed_message):
        """construct an EthernetPacket from a packed_message
        Args:
            packed_message (bytes):
        Returns:
            EthernetPacket
        Raises:
            MessageParseError: if packed_message cannot be successfully parsed.
        """
        try:
            dst_mac, src_mac, ethertype = struct.unpack("!6s6sH",
                                                        packed_message[:ETHERNET_HEADER_LENGTH])
        except struct.error as exception:
            raise MessageParseError("Unable to parse Ethernet header (14bytes)") from exception
        data = packed_message[ETHERNET_HEADER_LENGTH:]
        return cls(MacAddress(dst_mac), MacAddress(src_mac), ethertype, data)

    def pack(self):
        """Pack up the ethernet packet to bytes.
        Returns:
            bytes
        """
        header = struct.pack("!6s6sH", self.dst_mac.address, self.src_mac.address, self.ethertype)
        return header + self.data

    def __repr__(self):
        return "%s(dst_mac=%s, src_mac=%s, ethertype=0x%04X)" % \
               (self.__class__.__name__, self.dst_mac, self.src_mac, self.ethertype)

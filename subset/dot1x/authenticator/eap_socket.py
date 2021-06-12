"""Handle the EAP socket"""

from __future__ import absolute_import
import struct
from abc import ABC, abstractmethod
from fcntl import ioctl
import errno
import socket

from mac_address import MacAddress
from utils import get_logger, get_interface_mac


class PromiscuousSocket(ABC):
    """Abstract Raw Socket in Promiscuous Mode"""
    SIOCGIFINDEX = 0x8933
    PACKET_MR_PROMISC = 1
    SOL_PACKET = 263
    PACKET_ADD_MEMBERSHIP = 1

    @abstractmethod
    def send(self, data):  # pylint: disable=missing-docstring
        pass

    @abstractmethod
    def receive(self):  # pylint: disable=missing-docstring
        pass

    @abstractmethod
    def setup(self):  # pylint: disable=missing-docstring
        pass

    def __init__(self, interface_name, log_prefix):
        self.socket = None
        self.interface_index = None
        self.interface_name = interface_name
        self.logger = get_logger(log_prefix)
        self.eap_address = MacAddress.from_string(get_interface_mac(interface_name))

    def _setup(self, socket_filter):
        """Set up the socket"""
        self.logger.debug("Setting up socket on interface: %s", self.interface_name)
        try:
            self.open(socket_filter)
            self.get_interface_index()
            self.set_interface_promiscuous()
        except socket.error as err:
            self.logger.error("Unable to setup socket: %s", str(err))
            raise err

    def open(self, socket_filter):
        """Setup EAP socket"""
        self.socket = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket_filter)
        self.socket.bind((self.interface_name, 0))

    def get_interface_index(self):
        """Get the interface index of the EAP Socket"""
        # http://man7.org/linux/man-pages/man7/netdevice.7.html
        request = struct.pack('16sI', self.interface_name.encode("utf-8"), 0)
        response = ioctl(self.socket, self.SIOCGIFINDEX, request)
        _ifname, self.interface_index = struct.unpack('16sI', response)

    def set_interface_promiscuous(self):
        """Sets the EAP interface to be able to receive EAP messages"""
        request = struct.pack("IHH8s", self.interface_index, self.PACKET_MR_PROMISC,
                              len(self.eap_address.address), self.eap_address.address)
        self.socket.setsockopt(self.SOL_PACKET, self.PACKET_ADD_MEMBERSHIP, request)

    def shutdown(self):
        """Shutdown socket"""
        self.socket.close()


class EapSocket(PromiscuousSocket):
    """Handle the EAP socket"""

    def setup(self):
        """Set up the socket"""
        self._setup(socket.htons(0x888e))
        self.socket.settimeout(2.0)

    def send(self, data):
        """send on eap socket.
            data (bytes): data to send"""
        self.socket.send(data)

    def receive(self):
        """receive from eap socket"""
        # While socket hasn't been closed
        while self.socket.fileno() != -1:
            try:
                return self.socket.recv(4096)
            except socket.timeout:
                # Socket timed out. Expected. Move on.
                continue
            except OSError as exception:
                # socket closed
                if exception.errno == errno.EBADFD:
                    break
            except Exception:
                raise

"""Handle the RADIUS socket"""
from __future__ import absolute_import
import errno
import socket
from utils import get_logger


class RadiusSocket:
    """Handle the RADIUS socket"""

    def __init__(self, listen_ip, listen_port, server_ip,  # pylint: disable=too-many-arguments
                 server_port):
        self.socket = None
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.server_ip = server_ip
        self.server_port = server_port
        self.logger = get_logger('rsocket')

    def setup(self):
        """Setup RADIUS Socket"""
        self.logger.debug("Setting up radius socket.")
        try:
            self.socket = socket.socket(socket.AF_INET,
                                        socket.SOCK_DGRAM)
            self.socket.bind((self.listen_ip, self.listen_port))
        except socket.error as err:
            self.logger.error("Unable to setup socket: %s", str(err))
            raise err

    def send(self, data):
        """Sends on the radius socket
            data (bytes): what to send"""
        self.socket.sendto(data, (self.server_ip, self.server_port))

    def receive(self):
        """Receives from the radius socket"""
        return self.socket.recv(4096)

    def shutdown(self):
        """Shut down socket"""
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError as exception:
            if exception.errno == errno.ENOTCONN:
                # Socket isn't connected. Can't send FIN
                pass
            else:
                raise
        self.socket.close()

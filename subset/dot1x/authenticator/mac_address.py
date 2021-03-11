"""MAC address helper"""

import re

# pylint: disable=too-few-public-methods

_MAC_REGEX = re.compile(r'(?:[0-9a-f]{1,2}:){5}[0-9a-f]{1,2}\Z', re.IGNORECASE)


class MacAddress:
    """Class for comparing mac addresses"""

    def __init__(self, address):
        self.address = address

    @classmethod
    def from_string(cls, address_string):
        """Create a MacAddress from a string.

        Args:
            address_string (str): Colon-delimited MAC address.

        Returns:
            MacAddress

        Raises:
            ValueError: If address_string is invalid.
        """
        if not _MAC_REGEX.match(address_string):
            raise ValueError("'%s' does not appear to be a MAC address" % address_string)
        address = bytes(int(x, 16) for x in address_string.split(':'))
        return cls(address)

    def __str__(self):
        address_string = ":".join("%02x" % x for x in self.address)
        return address_string

    def __eq__(self, other):
        return self.address == other.address

    def __hash__(self):
        return hash(self.address)

    def __repr__(self):
        return "%s.from_string(\"%s\")" % (self.__class__.__name__, self.__str__())

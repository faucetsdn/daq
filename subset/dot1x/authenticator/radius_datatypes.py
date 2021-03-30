"""Radius Attribute Datatypes"""
import struct

import math
from utils import MessageParseError


class DataType():
    """Parent datatype class, subclass should provide implementation for abstractmethods.
    May """
    DATA_TYPE_VALUE = None
    AVP_HEADER_LEN = 1 + 1
    MAX_DATA_LENGTH = 253
    MIN_DATA_LENGTH = 1

    bytes_data = None  # bytes version of raw_data

    def parse(self, packed_value):
        """"""
        return

    def pack(self, attribute_type):
        """"""
        return

    def data(self):
        """Subclass should override this as needed.
        Returns:
             The python type (int, str, bytes) of the bytes_data.
         This will perform any decoding as required instead of using the unprocessed bytes_data.
        """
        return self.bytes_data

    def data_length(self):
        """
        Returns:
             length of the data field, and not total length of the attribute (including the
         type and length).
        If total is required use full_length.
        """
        return 0

    def full_length(self):
        """
        Returns:
            Length of the whole field include the header (type and length)
        """
        return self.data_length() + self.AVP_HEADER_LEN

    @classmethod
    def is_valid_length(cls, packed_value):
        length = len(packed_value)
        if length < cls.MIN_DATA_LENGTH \
                or length > cls.MAX_DATA_LENGTH \
                or len(packed_value) > cls.MAX_DATA_LENGTH \
                or length != len(packed_value):
            raise ValueError("RADIUS data type '%s' length must be: %d <= actual_length(%d) <= %d"
                             ""
                             % (cls.__name__, cls.MIN_DATA_LENGTH, length, cls.MAX_DATA_LENGTH))


class Integer(DataType):
    DATA_TYPE_VALUE = 1
    MAX_DATA_LENGTH = 4
    MIN_DATA_LENGTH = 4

    def __init__(self, bytes_data=None, raw_data=None):
        if raw_data:
            try:
                bytes_data = raw_data.to_bytes(self.MAX_DATA_LENGTH, "big")
            except OverflowError:
                raise ValueError("Integer must be >= 0  and <= 2^32-1, was %d" %
                                 raw_data)
        self.bytes_data = bytes_data

    @classmethod
    def parse(cls, packed_value):

        try:
            cls.is_valid_length(packed_value)
            return cls(bytes_data=struct.unpack("!4s", packed_value)[0])
        except (ValueError, struct.error)as exception:
            raise MessageParseError("%s unable to unpack." % cls.__name__) from exception

    def pack(self, attribute_type):
        return struct.pack("!4s", self.bytes_data)

    def data(self):
        return int.from_bytes(self.bytes_data, 'big')  # pytype: disable=attribute-error

    def data_length(self):
        return 4


class Enum(DataType):
    DATA_TYPE_VALUE = 2
    MAX_DATA_LENGTH = 4
    MIN_DATA_LENGTH = 4

    def __init__(self, bytes_data=None, raw_data=None):
        if raw_data:
            try:
                bytes_data = raw_data.to_bytes(self.MAX_DATA_LENGTH, "big")
            except OverflowError:
                raise ValueError("Integer must be >= 0  and <= 2^32-1, was %d" % raw_data)
        self.bytes_data = bytes_data

    @classmethod
    def parse(cls, packed_value):
        try:
            cls.is_valid_length(packed_value)
            return cls(bytes_data=struct.unpack("!4s", packed_value)[0])
        except (ValueError, struct.error)as exception:
            raise MessageParseError("%s unable to unpack." % cls.__name__) from exception

    def pack(self, attribute_type):
        return struct.pack("!4s", self.bytes_data)

    def data(self):
        return int.from_bytes(self.bytes_data, 'big')  # pytype: disable=attribute-error

    def data_length(self):
        return 4


class Text(DataType):
    DATA_TYPE_VALUE = 4

    def __init__(self, bytes_data=None, raw_data=None):
        if raw_data is not None:
            bytes_data = raw_data.encode()
            self.is_valid_length(bytes_data)
        self.bytes_data = bytes_data

    @classmethod
    def parse(cls, packed_value):
        try:
            cls.is_valid_length(packed_value)
            return cls(struct.unpack("!%ds" % len(packed_value), packed_value)[0])
        except (ValueError, struct.error) as exception:
            raise MessageParseError("%s unable to unpack." % cls.__name__) from exception

    def pack(self, attribute_type):
        return struct.pack("!%ds" % len(self.bytes_data), self.bytes_data)

    def data(self):
        return self.bytes_data.decode("UTF-8")

    def data_length(self):
        return len(self.bytes_data)


class String(DataType):
    # how is this different from Text?? - text is utf8
    DATA_TYPE_VALUE = 5

    def __init__(self, bytes_data=None, raw_data=None):
        if raw_data is not None:
            if isinstance(raw_data, bytes):
                bytes_data = raw_data
            else:
                bytes_data = raw_data.encode()
            self.is_valid_length(bytes_data)
        self.bytes_data = bytes_data

    @classmethod
    def parse(cls, packed_value):
        try:
            cls.is_valid_length(packed_value)
            return cls(struct.unpack("!%ds" % len(packed_value), packed_value)[0])
        except (ValueError, struct.error) as exception:
            raise MessageParseError("%s unable to unpack." % cls.__name__) from exception

    def pack(self, attribute_type):
        return struct.pack("!%ds" % len(self.bytes_data), self.bytes_data)

    def data_length(self):
        return len(self.bytes_data)


class Concat(DataType):
    """AttributeTypes that use Concat must override their pack()"""

    DATA_TYPE_VALUE = 6

    def __init__(self, bytes_data=None, raw_data=None):
        if raw_data:
            bytes_data = bytes.fromhex(raw_data)
            # self.is_valid_length(data)
        self.bytes_data = bytes_data

    @classmethod
    def parse(cls, packed_value):
        # TODO how do we want to do valid length checking here?
        #
        # Parsing is (generally) for packets coming from the radius server.
        # Packing is (generally) for packets going to the radius server.
        #
        # Therefore we error out if length is too long
        # (you are not allowed to have AVP that are too long)
        try:
            return cls(struct.unpack("!%ds" % len(packed_value), packed_value)[0])
        except struct.error as exception:
            raise MessageParseError("%s unable to unpack." % cls.__name__) from exception

    def pack(self, attribute_type):

        def chunks(data):
            length = self.MAX_DATA_LENGTH
            list_length = len(data)
            return_chunks = []
            for i in range(0, list_length, self.MAX_DATA_LENGTH):
                if i + self.MAX_DATA_LENGTH > list_length:
                    length = list_length % self.MAX_DATA_LENGTH

                chunk = data[i:i + length]
                chunk_length = len(chunk)
                packed = struct.pack("!BB%ds" % chunk_length, attribute_type,
                                     chunk_length + self.AVP_HEADER_LEN,
                                     chunk)
                return_chunks.append(packed)
            return return_chunks

        packed = b"".join(chunks(self.bytes_data))
        return packed

    def data(self):
        return self.bytes_data

    def full_length(self):
        return self.AVP_HEADER_LEN * \
               (math.ceil(len(self.bytes_data) / self.MAX_DATA_LENGTH + 1)) \
               + len(self.bytes_data) - self.AVP_HEADER_LEN

    def data_length(self):
        return len(self.bytes_data)


class Vsa(DataType):
    DATA_TYPE_VALUE = 14
    VENDOR_ID_LEN = 4
    MIN_DATA_LENGTH = 5

    def __init__(self, bytes_data=None, raw_data=None):
        if raw_data:
            bytes_data = raw_data
            self.is_valid_length(bytes_data)
        self.bytes_data = bytes_data

    @classmethod
    def parse(cls, packed_value):
        # TODO Vsa.parse does not currently separate the vendor-id from the vsa-data
        # we could do that at some point (e.g. if we wanted to use Vendor-Specific)
        try:
            cls.is_valid_length(packed_value)
            return cls(struct.unpack("!%ds" % len(packed_value), packed_value)[0])
        except (ValueError, struct.error) as exception:
            raise MessageParseError("%s unable to unpack." % cls.__name__) from exception

    def pack(self, attribute_type):
        return struct.pack("!%ds" % (self.data_length()), self.bytes_data)

    def data_length(self):
        return len(self.bytes_data)

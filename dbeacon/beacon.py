"""
Copyright (c) Jordan Maxwell, All Rights Reserved.
See LICENSE file in the project root for full license information.
"""

import struct
from enum import Enum

from dbeacon import utils

# ------------------------------------------------------------------------------------------------------- #

class BeaconIdentifiers(Enum):
    """
    Enum of known iBeacon identifiers.
    """

    WaltDisneyWorldPark = 'bc85ceaa-e2e2-435d-b049-9b70d5151c3b'
    DisneyLandPark = 'be5202c7-4017-4489-9cb2-d73d62cd529d'

# ------------------------------------------------------------------------------------------------------- #

class BeaconDeviceTypes(Enum):
    """
    Enum of known beacon device types.
    """

    DroidIdentificationBeacon = 3
    LocationBeacon = 10
    InstallationBeacon = 16

# ------------------------------------------------------------------------------------------------------- #

class Beacon(object):
    """
    Represents a type of beacon found in the Disney Parks.
    """

    def is_valid(self) -> bool:
        """
        Returns whether the beacon is valid.
        """

        raise NotImplementedError("%s does not implement is_valid()" % self.__class__.__name__)
  
    def _encode_to_payload(self) -> str:
        """
        Encodes the beacon as a hex string for use on physical BLE beacon devices.
        """

        raise NotImplementedError("%s does not implement _encode_to_payload()" % self.__class__.__name__)
    
    def _decode_from_payload(self, data: str) -> None:
        """
        Decodes the data from a BLE beacon into a Beacon object.
        """

        raise NotImplementedError("%s does not implement _decode_from_payload()" % self.__class__.__name__)
    
    def encode_beacon(self) -> str:
        """
        Encodes the beacon as a hex string for use on physical BLE beacon devices.
        """

        return self._encode_to_payload()

    @classmethod
    def decode_beacon(cls, data: str) -> object:
        """
        Decodes the data from a BLE beacon into a Beacon object.
        """

        beacon = cls()
        beacon._decode_from_payload(data)

        return beacon

# ------------------------------------------------------------------------------------------------------- #

class iBeacon(Beacon):
    """
    Represents an Apple iBeacon found in the Disney Parks.
    """

    def __init__(self, uuid: str = None, major: int = None, minor: int = None, power: int = None) -> None:
        """
        Initializes a new Beacon object.
        """

        self.uuid = uuid
        self.major = major
        self.minor = minor
        self.power = power

    def is_valid(self) -> bool:
        """
        Returns whether the beacon is valid.
        """

        return self.uuid is not None and self.major is not None and self.minor is not None and self.power is not None

    def get_name_if_known(self) -> str:
        """
        Returns the name of the beacon if it is known, otherwise returns 'Unknown'.
        """

        try:
            return BeaconIdentifiers(self.uuid).name
        except ValueError:
            return 'Unknown'

    def _encode_to_payload(self) -> str:
        """
        Encodes the beacon as a hex string for use on physical BLE beacon devices.
        """

        # Encode UUID as hex string
        uuid_hex = self.uuid.replace("-", "")
        
        # Encode major as big-endian 2-byte hex string
        major_hex = struct.pack(">H", self.major).hex()
        
        # Encode minor as big-endian 2-byte hex string
        minor_hex = struct.pack(">H", self.minor).hex()
        
        # Encode power as signed 1-byte hex string
        power_hex = struct.pack("b", self.power).hex()

        # Combine all hex strings and return
        return "0215" + uuid_hex + major_hex + minor_hex + power_hex

    def _decode_from_payload(self, data: str) -> None:
        """
        Decodes the data from a BLE beacon into a Beacon object.
        """

        # Shift data by 4 bytes
        data = data[4:]

        # Parse UUID (first 16 bytes)
        uuid_str = data[:32]
        formatted_uuid = "-".join([uuid_str[:8], uuid_str[8:12], uuid_str[12:16], uuid_str[16:20], uuid_str[20:]])

        # Parse major (bytes 20-21)
        major_bytes = bytes.fromhex(data[-10:-6])
        major = struct.unpack(">H", major_bytes)[0]

        # Parse minor (bytes 22-23)
        minor_bytes = bytes.fromhex(data[-6:-2])
        minor = struct.unpack(">H", minor_bytes)[0]

        # Parse power (byte 24, as a signed char)
        power_byte = bytes.fromhex(data[-2:])
        power = struct.unpack("b", power_byte)[0]

        self.uuid = formatted_uuid
        self.major = major
        self.minor = minor
        self.power = power

    def __str__(self) -> str:
        """
        Converts the Beacon object to a string.
        """

        return '(KnownName: %s UUID: %s, Major: %s, Minor: %s, Power: %s)' %  (
            self.get_name_if_known(), self.uuid, self.major, self.minor, self.power)

    def __repr__(self) -> str:
        """
        Converts the Beacon object into a printable representation of the object.
        """

        return self.__str__()

# ------------------------------------------------------------------------------------------------------- #

class dBeacon(Beacon):
    """
    Represents a Disney dBeacon found in the Disney Parks.
    """

    def __init__(self, device_type: int = 10, payload_length: int = 4, fields: list = []) -> object:
        """
        Initializes a new dBeacon object.
        """

        self.device_type = device_type
        self.payload_length = payload_length
        self.fields = fields

    def is_valid(self) -> bool:
        """
        Returns whether the beacon is valid.
        """

        return self.device_type is not None and self.payload_length is not None and self.fields is not None
    
    def get_beacon_header(self) -> str:
        """
        Returns the header used by a SWGE Beacon
        """

        return utils.int_to_hex(self.device_type) + utils.int_to_hex(self.payload_length)

    def _encode_to_payload(self) -> str:
        """
        Encodes the beacon as a hex string for use on physical BLE beacon devices.
        """

        beacon_payload = self.get_beacon_header()
        for field in self.fields:
            beacon_payload += utils.encode_field(field)

        return beacon_payload
    
    def _decode_from_payload(self, data: str) -> None:
        """
        Decodes the data from a BLE beacon into a Beacon object.
        """

        self.device_type = utils.hex_to_int(data[:2])
        self.payload_length = utils.hex_to_int(data[2:4])

        self.fields = []
        for i in range(0, self.payload_length):
            start = 4 + (i * 2)
            field = utils.hex_to_int(data[start:start +2])
            self.fields.append(field)
    
    def _get_fields_with_names(self) -> list:
        """
        Returns a list of fields with their names.
        """

        if self.device_type == BeaconDeviceTypes.DroidIdentificationBeacon.value:
            return { "DroidPaired": self.fields[0], "AfilliationId": self.fields[1], "PersonalityId": self.fields[2] }
        elif self.device_type == BeaconDeviceTypes.LocationBeacon.value:
            return { "LocationId": self.fields[0], "ReactionInterval": self.fields[1], "SignalStrength": self.fields[2], "DroidPaired": self.fields[3] }
        elif self.device_type == BeaconDeviceTypes.InstallationBeacon.value:
            return { "Unknown1": self.fields[0], "Nodes": self.fields[1], "WaypointId": self.fields[2], "NodeId": self.fields[3] }
        else:
            data = {}

            for i in range(0, self.payload_length):
                data["Field%s" % i] = self.fields[i]

            return data

    def __str__(self) -> str:
        """
        Converts the Beacon object to a string.
        """

        fields = self._get_fields_with_names()
        field_str = ""

        for field in fields:
            field_str += "%s: %s, " % (field, fields[field])

        device_type = BeaconDeviceTypes(self.device_type).name if self.device_type in BeaconDeviceTypes._value2member_map_ else "Unknown (%s)" % self.device_type
        return '(DeviceType: %s PayloadLength: %s Fields: (%s))' %  (device_type, self.payload_length, field_str)

    def __repr__(self) -> str:
        """
        Converts the Beacon object into a printable representation of the object.
        """

        return self.__str__()

# ------------------------------------------------------------------------------------------------------- #

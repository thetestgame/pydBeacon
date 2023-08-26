"""
Copyright (c) Jordan Maxwell, All Rights Reserved.
See LICENSE file in the project root for full license information.
"""

import struct
import logging
from enum import Enum
from dbeacon import utils

# ------------------------------------------------------------------------------------------------------- #

class DisneyBLEManufacturerId(object):
    """
    Constants representing the types of BLE beacons found in Disney parks.
    """

    DisneyiBeacon = 76
    DroidManufacturerId = 387

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
        Decodes the data from a BLE beacon.
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
        Decodes the data from a BLE beacon.
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

    def __init__(self, device_type: int, payload_length: int) -> object:
        """
        Initializes a new dBeacon object.
        """

        self._device_type = device_type
        self._payload_length = payload_length

    @property
    def device_type(self) -> int:
        """
        Getter for the device type.
        """

        return self._device_type
    
    @property
    def payload_length(self) -> int:
        """
        Getter for the payload length.
        """

        return self._payload_length

    def is_valid(self) -> bool:
        """
        Returns whether the beacon is valid.
        """

        return self.device_type is not None and self.payload_length is not None
    
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
    
    def _decode_beacon_type_payload(self, data: str) -> None:
        """
        Decodes the data from a specific type of BLE beacon.
        """

        raise NotImplementedError("%s does not implement _decode_beacon_type_payload()" % self.__class__.__name__)
    
    def _decode_from_payload(self, data: str) -> None:
        """
        Decodes the data from a BLE beacon.
        """

        self._device_type = utils.hex_to_int(data[:2])
        self._payload_length = utils.hex_to_int(data[2:4])
        self._decode_beacon_type_payload(data[4:])

    def _get_fields_with_names(self) -> list:
        """
        Returns a list of fields with their names.
        """

        raise NotImplementedError("%s does not implement _get_fields_with_names()" % self.__class__.__name__)

    def __str__(self) -> str:
        """
        Converts the Beacon object to a string.
        """

        fields = self._get_fields_with_names()
        field_str = ""

        for field in fields:
            field_str += "%s: %s, " % (field, fields[field])

        device_type = BeaconDeviceTypes(self.device_type).name if self.device_type in BeaconDeviceTypes._value2member_map_ else "Unknown (%s)" % self.device_type
        return '(DeviceType: %s | PayloadLength: %s | Fields: (%s))' %  (device_type, self.payload_length, field_str)

    def __repr__(self) -> str:
        """
        Converts the Beacon object into a printable representation of the object.
        """

        return self.__str__()

# ------------------------------------------------------------------------------------------------------- #

class DroidIdentificationBeacon(dBeacon):
    """
    Represents a Droid Identification Beacon found in the Disney Parks.
    """

    def __init__(self, payload_length: int = 4, droid_paired: bool = False, affiliation_id: int = 1, personality_id: int = 1) -> object:
        super().__init__(BeaconDeviceTypes.DroidIdentificationBeacon, payload_length)

        self._droid_paired = droid_paired
        self._affiliation_id = affiliation_id
        self._personality_id = personality_id

    @property
    def droid_paired(self) -> bool:
        """
        Getter for whether the droid is paired.
        """

        return self._droid_paired
    
    @property
    def affiliation_id(self) -> int:
        """
        Getter for the affiliation id.
        """

        return self._affiliation_id
    
    @property
    def personality_id(self) -> int:
        """
        Getter for the personality id.
        """

        return self._personality_id

    def _decode_beacon_type_payload(self, data: str) -> None:
        """
        Decodes the data from a specific type of BLE beacon.
        """ 

        self._droid_paired = utils.hex_to_int(data[:2]) == 1
        self._affiliation_id = utils.hex_to_int(data[2:4])
        self._personality_id = utils.hex_to_int(data[4:6])

    def _get_fields_with_names(self) -> list:
        """
        Returns a list of fields with their names.
        """

        return { 
            "DroidPaired": self.droid_paired,
            "AfilliationId": self.affiliation_id,
            "PersonalityId": self.personality_id
        }

# ------------------------------------------------------------------------------------------------------- #

class LocationBeacon(dBeacon):
    """
    Represents a Location Beacon found in the Disney Parks.
    """

    def __init__(self, payload_length: int = 4, location_id: int = 1, reaction_interval: int = 30, minimum_rssi: int = 30, droid_paired: bool = False) -> object:
        super().__init__(BeaconDeviceTypes.LocationBeacon, payload_length)

        self._location_id = location_id
        self._reaction_interval = reaction_interval
        self._minimum_rssi = minimum_rssi
        self._droid_paired = droid_paired

    @property
    def location_id(self) -> int:
        """
        Getter for the location id.
        """

        return self._location_id
    
    @property
    def reaction_interval(self) -> int:
        """
        Getter for the reaction interval.
        """

        return self._reaction_interval
    
    @property
    def minimum_rssi(self) -> int:
        """
        Getter for the minimum RSSI.
        """

        return self._minimum_rssi
    
    @property
    def droid_paired(self) -> bool:
        """
        Getter for whether the droid is paired.
        """

        return self._droid_paired

    def _decode_beacon_type_payload(self, data: str) -> None:
        """
        Decodes the data from a specific type of BLE beacon.
        """ 

        self._location_id = utils.hex_to_int(data[:2])
        self._reaction_interval = utils.hex_to_int(data[2:4])
        self._minimum_rssi = utils.hex_to_dbm(data[4:6])
        self._droid_paired = utils.hex_to_int(data[6:8]) == 1

    def _get_fields_with_names(self) -> list:
        """
        Returns a list of fields with their names.
        """

        return { 
            "LocationId": self.location_id,
            "ReactionInterval": self.reaction_interval,
            "MinimumRSSI": self.minimum_rssi,
            "DroidPaired": self.droid_paired
        }

# ------------------------------------------------------------------------------------------------------- #

class InstallationBeacon(dBeacon):
    """
    Represents an Installation Beacon found in the Disney Parks.
    """

    def __init__(self, payload_length: int = 4, unknown1: int = 1, unknown2: int = 1, waypoint_id: int = 1, minimmum_rssi: int = -95) -> object:
        super().__init__(BeaconDeviceTypes.InstallationBeacon, payload_length)

        self._unknown1 = unknown1
        self._unknown2 = unknown2
        self._waypoint_id = waypoint_id
        self._minimmum_rssi = minimmum_rssi

    @property
    def unknown1(self) -> int:
        """
        Getter for the first unknown field.
        """

        return self._unknown1
    
    @property
    def unknown2(self) -> int:
        """
        Getter for the second unknown field.
        """

        return self._unknown2
    
    @property
    def waypoint_id(self) -> int:
        """
        Getter for the waypoint id.
        """

        return self._waypoint_id
    
    @property
    def minimmum_rssi(self) -> int:
        """
        Getter for minimum RSSI
        """

        return self._minimmum_rssi
    
    def _decode_beacon_type_payload(self, data: str) -> None:
        """
        Decodes the data from a specific type of BLE beacon.
        """ 

        self._unknown1 = utils.hex_to_int(data[:2])
        self._unknown2 = utils.hex_to_int(data[2:4])
        self._waypoint_id = utils.hex_to_int(data[4:6])
        self._minimmum_rssi = utils.hex_to_dbm(data[6:8])

    def _get_fields_with_names(self) -> list:
        """
        Returns a list of fields with their names.
        """

        return { 
            "Unknown1": self.unknown1,
            "Unknown2": self.unknown2,
            "WaypointId": self.waypoint_id,
            "MinimumRSSI": self._minimmum_rssi
        }

# ------------------------------------------------------------------------------------------------------- #

class UnknownBeacon(dBeacon):
    """
    Represents an Unknown Beacon found in the Disney Parks.
    """

    def __init__(self, device_type: int = 1, payload_length: int = 4, fields: list = []) -> object:
        super().__init__(device_type, payload_length)

        self._fields = fields

    @property
    def fields(self) -> list:
        """
        Getter for the fields associated with the unknown beacon.
        """

        return self._fields
    
    def _decode_beacon_type_payload(self, data: str) -> None:
        """
        Decodes the data from a specific type of BLE beacon.
        """ 

        self._fields = []
        for field_id in range(0, self.payload_length):
            self._fields.append(utils.hex_to_int(data[field_id * 2:(field_id * 2) + 2]))

    def _get_fields_with_names(self) -> list:
        """
        Returns a list of fields with their names.
        """

        fields = {}
        for field_id in range(1, len(self.fields) + 1):
            fields["Unknown%s" % field_id] = self.fields[field_id - 1]

        return fields

# ------------------------------------------------------------------------------------------------------- #

def decode_dbeacon(data: str) -> object:
    """
    Decodes a dBeacon from the given data.
    """

    device_type = utils.hex_to_int(data[:2])
    if device_type == BeaconDeviceTypes.DroidIdentificationBeacon.value:
        return DroidIdentificationBeacon.decode_beacon(data)
    elif device_type == BeaconDeviceTypes.LocationBeacon.value:
        return LocationBeacon.decode_beacon(data)
    elif device_type == BeaconDeviceTypes.InstallationBeacon.value:
        return InstallationBeacon.decode_beacon(data)
    else:
        return UnknownBeacon.decode_beacon(data)

# ------------------------------------------------------------------------------------------------------- #
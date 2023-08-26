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
        """

        return self._device_type
    
    @property
    def payload_length(self) -> int:
        """
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
        """

        return self.droid_paired
    
    @property
    def affiliation_id(self) -> int:
        """
        """

        return self._affiliation_id
    
    @property
    def personality_id(self) -> int:
        """
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

    def __init__(self, payload_length: int = 4, location_id: int = 1, reaction_interval: int = 30, signal_strength: int = 30, droid_paired: bool = False) -> object:
        super().__init__(BeaconDeviceTypes.LocationBeacon, payload_length)

        self._location_id = location_id
        self._reaction_interval = reaction_interval
        self._signal_strength = signal_strength
        self._droid_paired = droid_paired

    @property
    def location_id(self) -> int:
        """
        """

        return self._location_id
    
    @property
    def reaction_interval(self) -> int:
        """
        """

        return self._reaction_interval
    
    @property
    def signal_strength(self) -> int:
        """
        """

        return self._signal_strength
    
    @property
    def droid_paired(self) -> bool:
        """
        """

        return self._droid_paired

    def _decode_beacon_type_payload(self, data: str) -> None:
        """
        Decodes the data from a specific type of BLE beacon.
        """ 

        self._location_id = utils.hex_to_int(data[:2])
        self._reaction_interval = utils.hex_to_int(data[2:4])
        self._signal_strength = utils.hex_to_dbm(data[4:6])
        self._droid_paired = utils.hex_to_int(data[6:8]) == 1

    def _get_fields_with_names(self) -> list:
        """
        Returns a list of fields with their names.
        """

        return { 
            "LocationId": self.location_id,
            "ReactionInterval": self.reaction_interval,
            "SignalStrength": self.signal_strength,
            "DroidPaired": self.droid_paired
        }

# ------------------------------------------------------------------------------------------------------- #

def decode_dbeacon(data: str) -> object:
    """
    """

    device_type = utils.hex_to_int(data[:2])
    if device_type == BeaconDeviceTypes.DroidIdentificationBeacon.value:
        return DroidIdentificationBeacon.decode_beacon(data)
    elif device_type == BeaconDeviceTypes.LocationBeacon.value:
        return LocationBeacon.decode_beacon(data)
    else:
        logging.warning("Unknown beacon type: %s" % device_type)

# ------------------------------------------------------------------------------------------------------- #
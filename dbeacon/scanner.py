"""
Copyright (c) Jordan Maxwell, All Rights Reserved.
See LICENSE file in the project root for full license information.
"""

from dbeacon import beacon

from bleak import BleakScanner
from threading import Thread
import logging
import asyncio

class DBeaconScanner(object):
    """
    A class for scanning and decoding Disney dBeacon broadcasts.
    """
    
    def __init__(self):
        """
        Initializes a new instance of the DBeaconScanner class.
        """

        self.__beacon_handlers = {}

        self.__scan_loop = asyncio.new_event_loop()
        self.__scan_thread = None

    def add_beacon_handler(self, beacon_type: beacon.BeaconDeviceTypes, handler: object) -> None:
        """
        Adds a handler for a specific beacon type
        """

        if isinstance(beacon_type, beacon.BeaconDeviceTypes):
            beacon_type = beacon_type.value

        if beacon_type not in self.__beacon_handlers:
            self.__beacon_handlers[beacon_type] = []

        self.__beacon_handlers[beacon_type].append(handler)

    def remove_beacon_handler(self, beacon_type: beacon.BeaconDeviceTypes, handler: object) -> None:
        """
        Removes a handler for a specific beacon type
        """

        if isinstance(beacon_type, beacon.BeaconDeviceTypes):
            beacon_type = beacon_type.value

        if beacon_type not in self.__beacon_handlers:
            return
        
        self.__beacon_handlers[beacon_type].remove(handler)

    async def __scan(self) -> None:
        """
        Scans for nearby Disney BLE dBeacons and decodes their data.
        """

        async with BleakScanner() as scanner:
            await scanner.start()

            while True:
                devices = scanner.discovered_devices_and_advertisement_data
                visible_beacons = {}
                
                for device_address in devices:
                    try:
                        # Check if the device is advertising with the expected manufacturer ID
                        device, data = devices[device_address]
                        if self.__is_dbeacon(data.manufacturer_data):
                            beacon_payload = data.manufacturer_data[beacon.DisneyBLEManufacturerId.DroidManufacturerId]
                            beacon_payload = beacon_payload.hex()

                            decoded_beacon = beacon.decode_dbeacon(beacon_payload)
                            if decoded_beacon is None:
                                continue

                            logging.debug('Found dBeacon: %s' % decoded_beacon)
                            if decoded_beacon.device_type not in visible_beacons:
                                visible_beacons[decoded_beacon.device_type] = []

                            visible_beacons[decoded_beacon.device_type].append((device_address, decoded_beacon))
                    except Exception as e:
                        logging.error('An unexpected error occured processing bluetooth device: %s' % device_address)
                        logging.error(e, exc_info=True) 

                for device_type in visible_beacons:
                    if device_type in self.__beacon_handlers:
                        for handler in self.__beacon_handlers[device_type]:
                            await handler(visible_beacons[device_type])

                scanner.discovered_devices_and_advertisement_data.clear()
                await asyncio.sleep(2)

    def __start_scan_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Starts the beacon scanning event loop
        """

        asyncio.set_event_loop(loop)
        loop.run_forever()

    def __is_dbeacon(self, data: dict) -> bool:
        """
        Checks if the given data contains dBeacon data
        """

        return beacon.DisneyBLEManufacturerId.DroidManufacturerId in data

    def start(self) -> None:
        """
        Starts the beacon scanner
        """

        if self.__scan_loop.is_running():
            return

        self.__scan_thread = Thread(target=self.__start_scan_loop, args=(self.__scan_loop,), daemon=True)
        self.__scan_thread.start()
        asyncio.run_coroutine_threadsafe(self.__scan(), self.__scan_loop)

    def stop(self) -> None:
        """
        Stops the beacon scanner
        """

        if self.__scan_loop.is_running():
            self.__scan_loop.stop()
            self.__scan_thread.join()
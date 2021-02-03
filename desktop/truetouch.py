import struct
from enum import IntEnum

from bleak import BleakScanner, BleakClient
from typing import List, Optional, Callable

from bleak.backends.client import BaseBleakClient


def _rx_callback(sender, data):
    """
    Private callback to handle receiving data
    """
    # TODO implement (???)
    print("Rx {0}: {1}".format(sender, data))


class TrueTouchCommands(IntEnum):
    SOLENOID_WRITE = 0x01
    SOLENOID_PULSE = 0x02
    ERM_SET = 0x03


class TrueTouchFinger(IntEnum):
    THUMB = 0x00,
    INDEX = 0x01,
    MIDDLE = 0x02,
    RING = 0x03,
    PINKY = 0x04,
    PALM = 0x05


class TrueTouchGpioOutputs(IntEnum):
    OUT_LOW = 0x00,
    OUT_HIGH = 0x01


class TrueTouch:
    NORDIC_UART_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
    NUS_RX_CHAR = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    NUS_TX_CHAR = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

    def __init__(self):
        # The bleak client instance
        self.client = None
        # The BLEDevice representing the remote device
        self.device = None

    @classmethod
    async def list_devices(cls):
        """
        Finds and prints available BLE devices
        """
        devices = await BleakScanner.discover()

        for device in devices:
            print(device)

    @classmethod
    async def new(cls, device_name: str = None):
        """
        Creates and initializes a BLE connection to a target device running the Nordic UART service.
        :param device_name: Name of the device to connect to.
        """
        self = TrueTouch()

        # Gather and look through devices for one that matches the target name
        devices = await BleakScanner.discover()

        # Scan through the devices to see if the desired device is available
        for device in devices:
            if device_name is not None:  # search by device name
                if device.name == device_name:
                    self.device = device
                    if self.NORDIC_UART_SERVICE not in self.device.metadata['uuids']:
                        raise RuntimeError("Device with given name does not have the Nordic UART service",
                                           self.device, self.NORDIC_UART_SERVICE)
                    break
            else:  # just grab the first one with the Nordic UART service
                if self.NORDIC_UART_SERVICE in device.metadata['uuids']:
                    self.device = device
                    break

        if self.device is None:
            raise RuntimeError("Could not find a device with the given name or with the Nordic UART service",
                               device_name)

        # Get the client and wait for a connection
        self.client = BleakClient(self.device)
        conn = await self.client.connect()
        if not conn:
            raise RuntimeError("Could not connect to device")

        # Start listening for notifications from NUS service
        await self.client.start_notify(self.NUS_TX_CHAR, _rx_callback)

        return self

    def get_mac(self) -> str:
        """
        Gets the MAC address of the connected BLE device
        :return: a string containing the device's MAC address
        """
        return str(self.device.address)

    def set_disconnect_callback(self, callback: Optional[Callable[[BaseBleakClient], None]]):
        """
        Sets the callback to be called when BLE device is disconnected
        :param callback:
        """
        self.client.set_disconnected_callback(callback)

    async def write_gpio(self, fingers: List[TrueTouchFinger], output: TrueTouchGpioOutputs):
        """
        Controls GPIO on the connected device. The byte format is:
            <command 1-byte> <finger bitset 4-bytes> <output 1-byte>
        :param fingers: fingers to configure
        :param output: what output level to set on the GPIO
        """
        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE byte
        byte_buffer = struct.pack("!BLB", TrueTouchCommands.SOLENOID_WRITE,
                                  TrueTouch.finger_list_to_bitmask(fingers), int(output))

        print("write_gpio sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    async def pulse_gpio(self, fingers: List[TrueTouchFinger], duration_ms: int):
        """
        Pulses GPIO on the connected device. The byte format is:
            <command 1-byte> <finger bitset 4-bytes> <duration 4-byte>
        :param fingers: fingers to pulse
        :param duration_ms: pulse duration in ms
        """
        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE 4 bytes
        byte_buffer = struct.pack("!BLL", TrueTouchCommands.SOLENOID_PULSE,
                                  TrueTouch.finger_list_to_bitmask(fingers), duration_ms)

        print("pulse_gpio sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    async def set_pwm(self, fingers: List[TrueTouchFinger], duty_cycle: int):
        """
        Sets PWM output on the connected device. The byte format is:
            <command 1-byte> <finger bitset 4-bytes> <intensity 1-byte>
        :param fingers: fingers to set ERM on
        :param duty_cycle: duty cycle of the PWM cycle (duty cycle is intensity / 255)
        """
        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE byte
        byte_buffer = struct.pack("!BLB", TrueTouchCommands.ERM_SET,
                                  TrueTouch.finger_list_to_bitmask(fingers), duty_cycle)

        print("set_pwm sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    @staticmethod
    def finger_list_to_bitmask(fingers: List[TrueTouchFinger]) -> int:
        """
        Converts a list of fingers into a bitmask usable by the TrueTouch device
        :param fingers: list of fingers to form into a bitmask
        :return: bitmask
        """
        bitmask = 0
        for finger in fingers:
            bitmask = bitmask | (1 << int(finger))

        return bitmask

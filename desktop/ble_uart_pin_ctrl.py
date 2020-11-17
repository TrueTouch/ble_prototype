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


class BleUartPinCtrlCommands(IntEnum):
    GPIO_CONFIGURE = 0x01
    GPIO_WRITE = 0x02
    GPIO_PULSE = 0x03
    GPIO_QUERY = 0x04
    PWM_SET = 0x05
    QUERY_STATE = 0x06


class BleUartPinCtrlGpioDirections(IntEnum):
    DIR_INPUT = 0x00,
    DIR_OUTPUT = 0x01


class BleUartPinCtrlGpioOutputs(IntEnum):
    OUT_LOW = 0x00,
    OUT_HIGH = 0x01


class BleUartPinCtrl:
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
        self = BleUartPinCtrl()

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

    async def configure_gpio(self, port: int, pins: List[int], direction: BleUartPinCtrlGpioDirections):
        """
        Configures GPIO on the connected device. The byte format is:
            <command 1-byte> <port 4-bytes> <pin mask 4-bytes> <0x00 = input, 0x01 = output>
        :param port: port number to configure
        :param pins: list of pins to configure
        :param direction: which directon to configure the pins as
        """
        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE 4 bytes, LE byte
        byte_buffer = struct.pack("!BLLB", BleUartPinCtrlCommands.GPIO_CONFIGURE,
                                  port, BleUartPinCtrl.pin_list_to_bitmask(pins), int(direction))

        print("configure_gpio sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    async def write_gpio(self, port: int, pins: List[int], output: BleUartPinCtrlGpioOutputs):
        """
        Controls GPIO on the connected device. The byte format is:
            <command 1-byte> <port 4-bytes> <pin mask 4-bytes>
        :param port: port number to configure
        :param pins: list of pins to configure
        :param output: what output level to set on the GPIO
        """
        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE 4 bytes, LE byte
        byte_buffer = struct.pack("!BLLB",
                                  BleUartPinCtrlCommands.GPIO_WRITE,
                                  port, BleUartPinCtrl.pin_list_to_bitmask(pins), int(output))

        print("write_gpio sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    async def pulse_gpio(self, port: int, pins: List[int], duration_ms: int):
        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE 4 bytes, LE byte
        byte_buffer = struct.pack("!BLLL",
                                  BleUartPinCtrlCommands.GPIO_PULSE,
                                  port, BleUartPinCtrl.pin_list_to_bitmask(pins), duration_ms)

        print("pulse_gpio sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    async def query_gpio(self, port: int, pins: List[int]):
        """
        TODO
        """
        raise NotImplementedError("TODO CMK(11/15/20): Implement query_gpio")

    async def set_pwm(self, port: int, pins: List[int], duty_cycle: int):
        """
        Sets PWM output on the connected device. The byte format is:
            <command 1-byte> <port 4-bytes> <pin mask 4-bytes> <intensity 1-byte>
        :param port: port number to configure
        :param pins: list of pins to configure
        :param duty_cycle: duty cycle of the PWM cycle (duty cycle is intensity / 255)
        """
        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE 4 bytes, LE byte
        byte_buffer = struct.pack("!BLLB", BleUartPinCtrlCommands.PWM_SET,
                                  port, BleUartPinCtrl.pin_list_to_bitmask(pins), duty_cycle)

        print("set_pwm sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    async def query_state(self, port: int, pins: List[int]):
        """
        TODO
        """
        raise NotImplementedError("TODO CMK(11/15/20): Implement query_state")

    @staticmethod
    def pin_list_to_bitmask(pins: List[int]) -> int:
        """
        Converts a string of pin numbers into a bitmask where each pin number is converted to a set bit of the
            corresponding position.
        :param pins: list of pin numbers to form into a bitmask
        :return: bitmask
        """
        pin_mask = 0
        for pin in pins:
            pin_mask = pin_mask | (1 << pin)
        return pin_mask

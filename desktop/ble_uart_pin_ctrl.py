import struct
import time
from enum import IntEnum

from bleak import BleakScanner, BleakClient
from typing import List, Tuple


def _rx_callback(sender, data):
    """
    Private callback to handle receiving data
    """
    # TODO implement (???)
    print("Rx {0}: {1}".format(sender, data))


class BleUartPinCtrlCommands(IntEnum):
    GPIO_CONFIGURE = 0x01
    GPIO_SET = 0x02
    GPIO_CLEAR = 0x03
    GPIO_QUERY = 0x04
    PWM_SET = 0x05
    QUERY_STATE = 0x06


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
            raise RuntimeError("Could not find a device with the given name", device_name)

        # Get the client and wait for a connection
        self.client = BleakClient(self.device)
        conn = await self.client.connect()
        if not conn:
            raise RuntimeError("Could not connect to device")

        # Start listening for notifications from NUS service
        await self.client.start_notify(self.NUS_TX_CHAR, _rx_callback)

        return self

    async def configure_gpio(self, port: int, pins: List[int], is_output: bool):
        """
        Configures GPIO on the connected device. The byte format is:
            <command 1-byte> <port 4-bytes> <pin mask 4-bytes> <0x00 = input, 0x01 = output>
        :param port: port number to configure
        :param pins: list of pins to configure
        :param is_output: whether to configure the pins as outputs (true) or inputs (false)
        """
        # Form the pin mask
        pin_mask = 0
        for pin in pins:
            pin_mask = pin_mask | (1 << pin)

        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE 4 bytes, LE byte
        byte_buffer = struct.pack("!BLLB", BleUartPinCtrlCommands.GPIO_CONFIGURE,
                                  port, pin_mask, 0x01 if is_output else 0x00)

        print("configure_gpio sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    async def write_gpio(self, port: int, pins: List[int], output_high: bool):
        """
        Controls GPIO on the connected device. The byte format is:
            <command 1-byte> <port 4-bytes> <pin mask 4-bytes>
        :param port: port number to configure
        :param pins: list of pins to configure
        :param output_high: whether to set the pins output high (true) or low (false)
        """
        # Form the pin mask
        pin_mask = 0
        for pin in pins:
            pin_mask = pin_mask | (1 << pin)

        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE 4 bytes, LE byte
        byte_buffer = struct.pack("!BLL",
                                  BleUartPinCtrlCommands.GPIO_SET if output_high else BleUartPinCtrlCommands.GPIO_CLEAR,
                                  port, pin_mask)

        print("write_gpio sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    async def query_gpio(self, port: int, pins: List[int]):
        """
        TODO
        """
        raise NotImplementedError("TODO CMK(11/15/20): Implement query_gpio")

    async def set_pwm(self, port: int, pins: List[int], intensity: int):
        """
        Sets PWM output on the connected device. The byte format is:
            <command 1-byte> <port 4-bytes> <pin mask 4-bytes> <intensity 1-byte>
        :param port: port number to configure
        :param pins: list of pins to configure
        :param intensity: duty cycle of the PWM cycle (duty cycle is intensity / 255)
        """
        # Form the pin mask
        pin_mask = 0
        for pin in pins:
            pin_mask = pin_mask | (1 << pin)

        # Pack it all into a byte buffer (LE byte, LE 4 bytes, LE 4 bytes, LE byte
        byte_buffer = struct.pack("!BLLB", BleUartPinCtrlCommands.PWM_SET, port, pin_mask, intensity)

        print("set_pwm sending: ", byte_buffer)

        # Transmit the byte buffer
        await self.client.write_gatt_char(self.NUS_RX_CHAR, bytearray(byte_buffer))

    async def query_state(self, port: int, pins: List[int]):
        """
        TODO
        """
        raise NotImplementedError("TODO CMK(11/15/20): Implement query_state")


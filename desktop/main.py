# -*- coding: utf-8 -*-
"""
Notifications
-------------
Example showing how to add notifications to a characteristic and handle the responses.
Updated on 2019-07-03 by hbldh <henrik.blidh@gmail.com>
Adapted for prototype on 2020-11-14 by Cameron Kluza <ckluza@umass.edu>
"""


import asyncio
import sys
import logging

import time

from bleak import BleakScanner, BleakClient
from bleak import _logger as logger

# TODO - don't hardcode this (maybe look for device name)
feather_address = "F7:02:CB:A8:52:F4"
nordic_uart_service = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
nus_rx_char = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
nus_tx_char = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


def uart_received_handler(sender, data):
    # TODO remove, debug
    print("Rx {0}: {1}".format(sender, data))


async def run():
    # TODO remove, debug logging
    l = logging.getLogger("asyncio")
    l.setLevel(logging.DEBUG)
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(logging.DEBUG)
    l.addHandler(h)
    logger.addHandler(h)

    devices = await BleakScanner.discover()

    # TODO remove, debug
    for dev in devices:
        print(dev)

    feather = await BleakScanner.find_device_by_address(feather_address)
    if not feather:
        print("Could not find feather")
        return

    print("Found feather: ", feather)
    async with BleakClient(feather) as feather_client:
        x = await feather_client.is_connected()
        logger.info("Connected: {0}".format(x))

        services = await feather_client.get_services()

        # TODO remove, debug
        print("Services:")
        for service in services:
            print(service)

        # Look for the UART service
        uart_service = services.get_service(nordic_uart_service)
        if not uart_service:
            print("Couldn't find Nordic UART service")
            return

        # Grab the rx and tx characteristics
        rx_char = uart_service.get_characteristic(nus_rx_char)
        tx_char = uart_service.get_characteristic(nus_tx_char)

        if not rx_char or not tx_char:
            print("Couldn't find UART characteristics")
            return

        print("Successfully found NUS service and characteristics")

        await feather_client.start_notify(nus_tx_char, uart_received_handler)

        print("Listening to TX notifications")

        # for now just send a sequence of hard-coded commands

        # Want to turn on LED_RED (Arduino pin 3) and PWM pin 12 - set these as outputs
        configure_outputs = bytearray()
        configure_outputs.extend(bytes.fromhex("01"))  # 1-byte GPIO configure command 0x01
        configure_outputs.extend(bytes.fromhex("00000000"))  # 4-bytes port (unused)
        configure_outputs.extend(bytes.fromhex("00001008"))  # 4-bytes pin mask (bits 3 and 12 set)
        configure_outputs.extend(bytes.fromhex("01"))  # 1-byte pinmode output

        # And then do a GPIO set command
        set_output = bytearray()
        set_output.extend(bytes.fromhex("02"))  # 1-byte GPIO set command 0x02
        set_output.extend(bytes.fromhex("00000000"))  # 4-bytes port (unused)
        set_output.extend(bytes.fromhex("00000008"))  # 4-bytes pin mask (bit 3 set)

        # And a PWM command
        set_pwm = bytearray()
        set_pwm.extend(bytes.fromhex("05"))  # 1-byte PWM set command 0x02
        set_pwm.extend(bytes.fromhex("00000000"))  # 4-bytes port (unused)
        set_pwm.extend(bytes.fromhex("00001000"))  # 4-bytes pin mask (bit 12 set)
        set_pwm.extend(bytes.fromhex("77"))  # 1-byte intensity

        # send the configure command
        print("Configuring outputs... ({})".format(configure_outputs))
        await feather_client.write_gatt_char(nus_rx_char, configure_outputs)
        print("Outputs configured!")

        time.sleep(5)

        # send the GPIO set command
        print("Setting GPIO...({})".format(set_output))
        await feather_client.write_gatt_char(nus_rx_char, set_output)
        print("GPIO set!")

        time.sleep(5)

        # send the PWM set command
        print("Setting PWM...({})".format(set_pwm))
        await feather_client.write_gatt_char(nus_rx_char, set_pwm)
        print("PWM set!")

        # Just stay connected forever
        while True:
            continue


loop = asyncio.get_event_loop()
loop.run_until_complete(run())

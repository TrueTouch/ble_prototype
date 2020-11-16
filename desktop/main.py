# -*- coding: utf-8 -*-
"""
Notifications
-------------
Example showing how to add notifications to a characteristic and handle the responses.
Updated on 2019-07-03 by hbldh <henrik.blidh@gmail.com>
"""

import asyncio

import time

from bleak import _logger as logger

from ble_uart_pin_ctrl import BleUartPinCtrl


async def run():
    # For debugging - print available BLE devices
    await BleUartPinCtrl.list_devices()

    pin_ctrl = await BleUartPinCtrl.new()

    print("Connected to feather!")

    time.sleep(5)

    print("Sending GPIO configure")
    await pin_ctrl.configure_gpio(port=0, pins=[3, 12], is_output=True)
    print("GPIO configure sent")

    time.sleep(5)

    print("Sending GPIO write")
    await pin_ctrl.write_gpio(port=0, pins=[3], output_high=True)
    print("GPIO write sent")

    time.sleep(5)

    print("Sending PWM set")
    await pin_ctrl.set_pwm(port=0, pins=[12], intensity=125)
    print("PWM set sent")

    while True:
        continue


loop = asyncio.get_event_loop()
loop.run_until_complete(run())

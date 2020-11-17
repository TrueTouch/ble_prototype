# -*- coding: utf-8 -*-

import asyncio
import time

from ble_uart_pin_ctrl import BleUartPinCtrl


async def run():
    # For debugging - print available BLE devices
    await BleUartPinCtrl.list_devices()

    pin_ctrl = await BleUartPinCtrl.new()

    print("Connected to feather!")

    time.sleep(5)

    print("Sending GPIO configure")
    await pin_ctrl.configure_gpio(port=0, pins=[12], is_output=True)
    print("GPIO configure sent")

    time.sleep(5)

    print("Sending GPIO write")
    await pin_ctrl.write_gpio(port=0, pins=[12], output_high=True)
    print("GPIO write sent")

    time.sleep(0.01)

    print("Sending PWM set")
    await pin_ctrl.write_gpio(port=0, pins=[12], output_high=False)
    print("PWM set sent")

    while True:
        continue


loop = asyncio.get_event_loop()
loop.run_until_complete(run())

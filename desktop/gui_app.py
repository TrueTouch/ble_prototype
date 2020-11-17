import asyncio
import threading
import time
from typing import List

import tkinter as tk
from tkinter import ttk


from ble_uart_pin_ctrl import BleUartPinCtrl, BleUartPinCtrlGpioOutputs, BleUartPinCtrlGpioDirections


class Solenoids:
    NUM_SOLENOIDS = 5
    DEFAULT_PINS = [9, 10, 11, 12, 13]
    ACTION_OPTIONS = ("Nothing", "High", "Low", "Pulse")

    def __init__(self, main_window: tk.Tk):
        """
        Initializes GUI components for solenoid control.

        The solenoid gui shall consist of a few parts:
            A row of 5 labels (one per solenoid) stating which solenoid it refers to
            A row of 5 small text boxes (one per solenoid), where a user can enter a pin number
            A row of 5 combo boxes (one per solenoid), where a user can select to do nothing, set a pin high, low,
                or pulse it
            A row of 5 buttons (one per solenoid), that a user can select or deselect to indicate if a solenoid should
                update
            A text input where a user can enter a solenoid actuation duration
                TODO: specifics of this

        :param main_window: a tkinter window instance to attach GUI widgets to
        """
        self.pin_labels = list()
        self.pin_inputs = list()
        self.pin_cboxes = list()
        self.pin_cbox_values = list()
        self.pulse_label = None
        self.pulse_dur_input = None

        # Pack a frame into main window, then pack everything into that frame
        window = tk.Frame(
            master=main_window
        )
        window.pack()

        # Add first row - title
        title_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=title_row, column=0, columnspan=self.NUM_SOLENOIDS)
        title = tk.Label(master=frame, text="Solenoids")
        title.config(font=('Helvetica', 20))
        title.pack(anchor=tk.CENTER)

        # Add the first row - solenoid labels
        labels_row = window.grid_size()[1]
        for i in range(self.NUM_SOLENOIDS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=labels_row, column=i)
            self.pin_labels.append(tk.Label(master=frame, text=f"Solenoid {i}"))
            self.pin_labels[i].pack(padx=5, pady=5)

        # Add the second row - pin number inputs
        inputs_row = window.grid_size()[1]
        for i in range(self.NUM_SOLENOIDS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=inputs_row, column=i)
            self.pin_inputs.append(tk.Entry(master=frame, width=5))
            self.pin_inputs[i].pack(padx=5, pady=5)
            # Set default pins
            self.pin_inputs[i].insert(0, str(self.DEFAULT_PINS[i]))

        # Add the third row - solenoid active buttons
        buttons_row = window.grid_size()[1]
        for i in range(self.NUM_SOLENOIDS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=buttons_row, column=i)
            self.pin_cbox_values.append(tk.StringVar(value="Nothing"))
            self.pin_cboxes.append(ttk.Combobox(master=frame, width=10, textvariable=self.pin_cbox_values[i]))
            self.pin_cboxes[i].pack(padx=5, pady=5)
            self.pin_cboxes[i]["values"] = self.ACTION_OPTIONS

        # Add fourth row - actuation duration label
        act_label_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=act_label_row, column=0, columnspan=self.NUM_SOLENOIDS - 2)
        self.pulse_label = tk.Label(master=frame, text="Pulse duration (ms):")
        self.pulse_label.config(font=('Helvetica', 16))
        self.pulse_label.pack()

        # Same row - input text box
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=act_label_row, column=self.NUM_SOLENOIDS - 2, columnspan=2)
        self.pulse_dur_input = tk.Entry(master=frame, width=10)
        self.pulse_dur_input.pack()

    def get_action_pins(self, pin_action: str) -> List[int]:
        """
        Creates a list of integers representing solenoid pins that will perform the given action
        :return: list of solenoid pins
        """
        solenoid_pins = list()
        for i, action in enumerate(self.pin_cbox_values):
            if action.get() == pin_action:
                pin = int(self.pin_inputs[i].get())
                if pin < 0 or pin > 31:
                    raise ValueError("Solenoid pin not in range [0, 31]")
                solenoid_pins.append(pin)

        return solenoid_pins

    def get_pulse_dur(self) -> int:
        """
        Converts the value in the duration input box to an integer and returns it
        :return: activation length as an integer in units of ms
        """
        pulse_dur_str = self.pulse_dur_input.get()
        if len(pulse_dur_str) == 0:  # user hasn't entered anything yet
            return 0
        pulse_dur = int(pulse_dur_str)
        if pulse_dur < 0:
            raise ValueError("Solenoid pules duration cannot be negative")
        return pulse_dur

    def get_all_pins(self) -> List[int]:
        """
        Creates a list of integers representing solenoid pins
        :return: list of solenoid pins
        """
        solenoid_pins = list()
        for pin_input in self.pin_inputs:
            pin = int(pin_input.get())
            if pin < 0 or pin > 31:
                raise ValueError("Solenoid pin not in range [0, 31]")
            solenoid_pins.append(pin)

        return solenoid_pins

    def get_action_str(self) -> str:
        """
        Returns a string of underlying BLE commands that will take place for solenoids given the current GUI
        configuration

        String format:
            Setting High: [pin list]
            Setting Low: [pin list]
            Pulsing: [pin list]
        """
        return "Setting High: {}\nSetting Low: {}\nPulsing for {} ms: {}\n".format(
            self.get_action_pins("High"),
            self.get_action_pins("Low"),
            self.get_pulse_dur(),
            self.get_action_pins("Pulse")
        )


class ERMMotors:
    NUM_MOTORS = 6
    DEFAULT_PINS = [14, 15, 16, 17, 18, 19]

    def __init__(self, main_window: tk.Tk):
        """
        Initializes GUI components for ERM control.

        The motor gui shall consist of a few parts:
            A row of 6 labels (one per motor) stating which motor it refers to
            A row of 6 small text boxes (one per motor), where a user can enter a pin number
            A row of 6 buttons (one per motor), that a user can select or deselect to indicate if a motor should
                update
            A text input where a user can enter a motor duty_cycle

        :param main_window: a tkinter window instance to attach GUI widgets to
        """
        self.pin_labels = list()
        self.pin_inputs = list()
        self.pin_buttons = list()
        self.pin_button_values = list()
        self.intensity_label = None
        self.intensity_input = None

        # Pack a frame into main window, then pack everything into that frame
        window = tk.Frame(
            master=main_window
        )
        window.pack()

        # Add first row - title
        title_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=title_row, column=0, columnspan=self.NUM_MOTORS)
        title = tk.Label(master=frame, text="Motors")
        title.config(font=('Helvetica', 20))
        title.pack(anchor=tk.CENTER)

        # Add the first row - solenoid labels
        labels_row = window.grid_size()[1]
        for i in range(self.NUM_MOTORS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=labels_row, column=i)
            self.pin_labels.append(tk.Label(master=frame, text=f"Solenoid {i}"))
            self.pin_labels[i].pack(padx=5, pady=5)

        # Add the second row - pin number inputs
        inputs_row = window.grid_size()[1]
        for i in range(self.NUM_MOTORS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=inputs_row, column=i)
            self.pin_inputs.append(tk.Entry(master=frame, width=5))
            self.pin_inputs[i].pack(padx=5, pady=5)
            # Set default pins
            self.pin_inputs[i].insert(0, str(self.DEFAULT_PINS[i]))

        # Add the third row - solenoid active buttons
        buttons_row = window.grid_size()[1]
        for i in range(self.NUM_MOTORS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=buttons_row, column=i)
            self.pin_button_values.append(tk.BooleanVar(value=0))
            self.pin_buttons.append(tk.Checkbutton(master=frame, width=5, variable=self.pin_button_values[i]))
            self.pin_buttons[i].pack(padx=5, pady=5)

        # Add fourth row - duty_cycle label
        intensity_label_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=intensity_label_row, column=0, columnspan=self.NUM_MOTORS - 2)
        self.intensity_label = tk.Label(master=frame, text="Intensity (0-255):")
        self.intensity_label.config(font=('Helvetica', 16))
        self.intensity_label.pack()

        # Same row - input text box
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=intensity_label_row, column=self.NUM_MOTORS - 2, columnspan=2)
        self.intensity_input = tk.Entry(master=frame, width=10)
        self.intensity_input.pack()

    def get_motors(self) -> List[int]:
        """
        Creates a list of integers representing motor pin values where the values are converted from the motor
        pin text boxes.
        :return: list of motor pins to control
        """
        active_motors = list()
        for i, is_enabled in enumerate(self.pin_button_values):
            if is_enabled.get():
                pin = int(self.pin_inputs[i].get())
                if pin < 0 or pin > 31:
                    raise ValueError("Motor pin not in range [0, 31]")
                active_motors.append(pin)

        return active_motors

    def get_intensity(self) -> int:
        """
        Converts the value in the duration input box to an integer and returns it
        :return: activation length as an integer in units of ms
        """
        intensity_str = self.intensity_input.get()
        if len(intensity_str) == 0:  # user hasn't entered anything yet
            return 0
        intensity = int(intensity_str)
        if intensity > 255 or intensity < 0:  # check for values too large
            raise ValueError("Motor duty_cycle not in range [0, 255]")
        return intensity

    def get_pins(self) -> List[int]:
        """
        Creates a list of integers representing motor pins
        :return: list of motor pins
        """
        motor_pins = list()
        for pin_input in self.pin_inputs:
            pin = int(pin_input.get())
            if pin < 0 or pin > 31:
                raise ValueError("Solenoid pin not in range [0, 31]")
            motor_pins.append(pin)

        return motor_pins

    def get_action_str(self) -> str:
        """
        Returns a string of underlying BLE commands that will take place for solenoids given the current GUI
        configuration

        String format:
            Setting Duty Cycle to <duty_cycle>/255: [pin list]
        """
        return "Setting Duty Cycle to {}/255: {}".format(self.get_intensity(), self.get_pins())


class BLEApp:
    def __init__(self, main_window: tk.Tk, solenoids: Solenoids, motors: ERMMotors):
        """
        Initializes GUI components and callbacks for the main app logic (connecting and sending commands over BLE).

        The BLE gui shall consist of a few parts:
            A button for connecting to the device
            A button for executing current command configuration
            A label that gives status updates

        :param main_window: a tkinter window instance to attach GUI widgets to
        :param solenoids: an instance of the solenoids GUI elements
        :param motors: an instance of the motors GUI elements
        """
        # tkinter GUI variables
        self.connect_button = None
        self.gpio_conf_button = None
        self.execute_button = None
        self.status_label_var = tk.StringVar(value="Ready")
        self.conn_state_var = tk.StringVar(value="Disconnected")

        # Other GUI elements
        self.solenoids = solenoids
        self.motors = motors

        # BLE UART pin control variables
        self.pin_ctrl = None

        # asyncio thread variables
        self.loop = None

        # Pack a frame into main window, then pack everything into that frame
        window = tk.Frame(
            master=main_window
        )
        window.pack()

        # Add first row - title
        title_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=title_row, column=0, columnspan=3)
        title = tk.Label(master=frame, text="BLE")
        title.config(font=('Helvetica', 20))
        title.pack(anchor=tk.CENTER)

        # Add second row first column - connect button
        buttons_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=buttons_row, column=0)
        self.connect_button = tk.Button(master=frame, text="Connect to Device", command=self.on_connect)
        self.connect_button.pack(padx=5, pady=5)

        # Add second row second column - configure GPIO button (start disabled until connected)
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=buttons_row, column=1)
        self.gpio_conf_button = tk.Button(master=frame, text="Configure GPIOs", command=self.on_gpio_conf)
        self.gpio_conf_button.pack(padx=5, pady=5)
        self.gpio_conf_button["state"] = "disabled"

        # Add second row third column - execute commands button
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=buttons_row, column=2)
        self.execute_button = tk.Button(master=frame, text="Execute Commands", command=self.on_execute)
        self.execute_button.pack(padx=5, pady=5)
        self.execute_button["state"] = "disabled"

        # Add third row - status info
        status_label_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=status_label_row, column=0, columnspan=3)
        status_label = tk.Label(master=frame, textvariable=self.status_label_var)
        status_label.pack(pady=5)
        status_label.config(font=('Helvetica', 14), wraplength=400, justify=tk.LEFT)

        # Add connection state to bottom right
        status_label = tk.Label(master=main_window, textvariable=self.conn_state_var)
        status_label.pack(anchor=tk.SE)
        status_label.config(font=('Helvetica', 10))

        # Setup asyncio
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def on_connect_async(self):
        try:
            self.pin_ctrl = await BleUartPinCtrl.new()
        except RuntimeError as err:  # Couldn't connect, update GUI state
            self.connect_button["state"] = "normal"
            self.status_label_var.set("Could not connect: {}".format(str(err)))
        else:  # Connected successfully, setup callbacks and update GUI state
            self.gpio_conf_button["state"] = "normal"
            self.execute_button["state"] = "normal"
            self.status_label_var.set("Connected!")
            self.pin_ctrl.set_disconnect_callback(self.on_disconnect)
            self.conn_state_var.set("Connected: {}".format(self.pin_ctrl.get_mac()))

    def on_connect(self):
        # Disable buttons no longer used
        self.connect_button["state"] = "disabled"
        self.status_label_var.set("Attempting to connect ...")
        # start a new thread to run coroutine while keeping other GUI elements interactive
        threading.Thread(target=lambda: self.loop.run_until_complete(self.on_connect_async())).start()

    async def on_gpio_conf_async(self, pins: List[int]):
        try:
            await self.pin_ctrl.configure_gpio(port=0, pins=pins, direction=BleUartPinCtrlGpioDirections.DIR_OUTPUT)
        except RuntimeError as err:  # Couldn't configure, update GUI state
            self.status_label_var.set("Could not configure GPIO: {}".format(str(err)))
        else:  # Connected successfully, setup callbacks and update GUI state
            self.status_label_var.set("Successfully configured GPIO as outputs!")
        self.gpio_conf_button["state"] = "normal"
        self.execute_button["state"] = "normal"

    def on_gpio_conf(self):
        # Get list of pins to configure
        pins = list()
        pins.extend(self.solenoids.get_all_pins())
        pins.extend(self.motors.get_pins())

        # Disable buttons no longer used
        self.gpio_conf_button["state"] = "disabled"
        self.execute_button["state"] = "disabled"
        self.status_label_var.set("Configuring as outputs: {} ...".format(pins))
        # start a new thread to run coroutine while keeping other GUI elements interactive
        threading.Thread(target=lambda: self.loop.run_until_complete(self.on_gpio_conf_async(pins))).start()

    async def on_execute_async(self, high_solenoids: List[int], low_solenoids: List[int], pulse_solenoids: List[int],
                               pulse_duration: int, erm_motors: List[int], erm_duty_cycle: int):
        try:
            # Are there solenoids to set high?
            if len(high_solenoids) > 0:  # Send a GPIO high command
                temp_str = self.status_label_var.get()
                temp_str += "\nSetting high: {}...".format(high_solenoids)
                self.status_label_var.set(temp_str)

                await self.pin_ctrl.write_gpio(port=0, pins=high_solenoids, output=BleUartPinCtrlGpioOutputs.OUT_HIGH)
                time.sleep(0.1)  # sleep for a little bit so things don't get flooded

            # Are there solenoids to set low?
            if len(low_solenoids) > 0:  # Send a GPIO high command
                temp_str = self.status_label_var.get()
                temp_str += "\nSetting low: {}...".format(low_solenoids)
                self.status_label_var.set(temp_str)

                await self.pin_ctrl.write_gpio(port=0, pins=low_solenoids, output=BleUartPinCtrlGpioOutputs.OUT_LOW)
                time.sleep(0.1)  # sleep for a little bit so things don't get flooded

            # Are there solenoids to pulse?
            if len(pulse_solenoids) > 0:  # Send a GPIO high command
                temp_str = self.status_label_var.get()
                temp_str += "\nPulsing for {} ms: {}...".format(pulse_duration, pulse_solenoids)
                self.status_label_var.set(temp_str)

                await self.pin_ctrl.pulse_gpio(port=0, pins=pulse_solenoids, duration_ms=pulse_duration)
                time.sleep(0.1)  # sleep for a little bit so things don't get flooded

            # Are there ERMs to PWM?
            if len(erm_motors) > 0:  # Send a GPIO high command
                temp_str = self.status_label_var.get()
                temp_str += "\nPWMing duty cycle {}/255: {}...".format(erm_duty_cycle, erm_motors)
                self.status_label_var.set(temp_str)

                await self.pin_ctrl.set_pwm(port=0, pins=erm_motors, duty_cycle=erm_duty_cycle)
                time.sleep(0.1)  # sleep for a little bit so things don't get flooded
        except RuntimeError as err:  # Couldn't execute, update GUI state
            self.execute_button["state"] = "normal"
            self.gpio_conf_button["state"] = "normal"
            self.status_label_var.set("Could not execute commands: {}".format(str(err)))
        else:
            self.execute_button["state"] = "normal"
            self.gpio_conf_button["state"] = "normal"
            temp_str = self.status_label_var.get()
            temp_str += "\nSuccess!"
            self.status_label_var.set(temp_str)

    def on_execute(self):
        # Disable necessary GUI elements
        self.execute_button["state"] = "disabled"
        self.gpio_conf_button["state"] = "disabled"
        # Format a string to describe what's happening
        try:
            action_str = self.solenoids.get_action_str()
            action_str += self.motors.get_action_str()
        except ValueError as err:
            self.execute_button["state"] = "normal"
            self.gpio_conf_button["state"] = "normal"
            self.status_label_var.set("Value error: {}".format(err))
        else:
            self.status_label_var.set("Executing Actions...")
            # start a new thread to run coroutine while keeping other GUI elements interactive
            threading.Thread(target=lambda: self.loop.run_until_complete(
                self.on_execute_async(
                    self.solenoids.get_action_pins("High"),
                    self.solenoids.get_action_pins("Low"),
                    self.solenoids.get_action_pins("Pulse"),
                    self.solenoids.get_pulse_dur(),
                    self.motors.get_motors(),
                    self.motors.get_intensity()
                )
            )).start()

    def on_disconnect(self, client):
        self.connect_button["state"] = "normal"
        self.execute_button["state"] = "disabled"
        self.gpio_conf_button["state"] = "disabled"
        self.status_label_var.set("Disconnected from {}".format(client.address))
        self.conn_state_var.set("Disconnected")


def main():
    # Create a main window object
    window = tk.Tk()

    # Initialize solenoid options
    solenoids = Solenoids(window)

    # Initialize motor options
    motors = ERMMotors(window)

    # Initialize the main app
    app = BLEApp(window, solenoids, motors)

    window.mainloop()


if __name__ == "__main__":
    main()

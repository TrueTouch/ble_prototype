import asyncio
import queue
import threading
import time
from typing import List, Tuple

import tkinter as tk
from tkinter import ttk


from truetouch import TrueTouch, TrueTouchFinger, TrueTouchGpioOutputs


class Solenoids:
    NUM_SOLENOIDS = 5
    FINGERS = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
    LABEL_TO_FINGER = {
        "Thumb": TrueTouchFinger.THUMB,
        "Index": TrueTouchFinger.INDEX,
        "Middle": TrueTouchFinger.MIDDLE,
        "Ring": TrueTouchFinger.RING,
        "Pinky": TrueTouchFinger.PINKY
    }
    ACTION_OPTIONS = ("Nothing", "High", "Low", "Pulse")

    def __init__(self, main_window: tk.Tk):
        """
        Initializes GUI components for solenoid control.

        The solenoid gui shall consist of a few parts:
            A row of 5 labels (one per solenoid) stating which finger it actuates
            A row of 5 combo boxes (one per solenoid), where a user can select to do nothing, set a pin high, low,
                or pulse it
            A text input where a user can enter a solenoid actuation duration

        :param main_window: a tkinter window instance to attach GUI widgets to
        """
        self.finger_labels = list()
        self.action_cboxes = list()
        self.action_cbox_values = list()
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

        # Add next row - solenoid labels
        labels_row = window.grid_size()[1]
        for i in range(self.NUM_SOLENOIDS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=labels_row, column=i)
            self.finger_labels.append(tk.Label(master=frame, text=self.FINGERS[i]))
            self.finger_labels[i].pack(padx=5, pady=5)

        # Add next row - solenoid action buttons
        buttons_row = window.grid_size()[1]
        for i in range(self.NUM_SOLENOIDS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=buttons_row, column=i)
            self.action_cbox_values.append(tk.StringVar(value="Nothing"))
            self.action_cboxes.append(ttk.Combobox(master=frame, width=10, textvariable=self.action_cbox_values[i]))
            self.action_cboxes[i].pack(padx=5, pady=5)
            self.action_cboxes[i]["values"] = self.ACTION_OPTIONS

        # Add next row - actuation duration label
        act_label_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=act_label_row, column=1, columnspan=self.NUM_SOLENOIDS - 2)
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

    def get_action_pins(self, pin_action: str) -> List[TrueTouchFinger]:
        """
        Creates a list of integers representing solenoid pins that will perform the given action
        :return: list of fingers performing the given action
        """
        pins = list()
        for i, action in enumerate(self.action_cbox_values):
            if action.get() == pin_action:
                finger = self.finger_labels[i]["text"]
                pins.append(self.LABEL_TO_FINGER[finger])

        return pins

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
    FINGERS = ["Thumb", "Index", "Middle", "Ring", "Pinky", "Palm"]
    LABEL_TO_FINGER = {
        "Thumb": TrueTouchFinger.THUMB,
        "Index": TrueTouchFinger.INDEX,
        "Middle": TrueTouchFinger.MIDDLE,
        "Ring": TrueTouchFinger.RING,
        "Pinky": TrueTouchFinger.PINKY,
        "Palm": TrueTouchFinger.PALM,
    }

    def __init__(self, main_window: tk.Tk):
        """
        Initializes GUI components for ERM control.

        The motor gui shall consist of a few parts:
            A row of 6 labels (one per motor) stating which finger it refers to
            A row of 6 buttons (one per motor), that a user can select or deselect to indicate if a motor should
                update
            A text input where a user can enter a motor duty_cycle

        :param main_window: a tkinter window instance to attach GUI widgets to
        """
        self.finger_labels = list()
        self.erm_selected_buttons = list()
        self.erm_selected_values = list()
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

        # Add next row - finger labels
        labels_row = window.grid_size()[1]
        for i in range(self.NUM_MOTORS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=labels_row, column=i)
            self.finger_labels.append(tk.Label(master=frame, text=self.FINGERS[i]))
            self.finger_labels[i].pack(padx=5, pady=5)

        # Add next row - ERM selected buttons
        buttons_row = window.grid_size()[1]
        for i in range(self.NUM_MOTORS):
            frame = tk.Frame(
                master=window
            )
            frame.grid(row=buttons_row, column=i)
            self.erm_selected_values.append(tk.BooleanVar(value=0))
            self.erm_selected_buttons.append(tk.Checkbutton(master=frame, width=5,
                                                            variable=self.erm_selected_values[i]))
            self.erm_selected_buttons[i].pack(padx=5, pady=5)

        # Add next - duty_cycle label
        intensity_label_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=intensity_label_row, column=1, columnspan=self.NUM_MOTORS - 2)
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

    def get_active_motors(self) -> List[TrueTouchFinger]:
        """
        Creates a list of ERM motors to be updated
        :return: list of ERM motors to update
        """
        active_motors = list()
        for i, is_enabled in enumerate(self.erm_selected_values):
            if is_enabled.get():
                finger = self.finger_labels[i]["text"]
                active_motors.append(self.LABEL_TO_FINGER[finger])

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

    def get_action_str(self) -> str:
        """
        Returns a string of underlying BLE commands that will take place for solenoids given the current GUI
        configuration

        String format:
            Setting Duty Cycle to <duty_cycle>/255: [pin list]
        """
        return "Setting Duty Cycle to {}/255: {}".format(self.get_intensity(), self.get_active_motors())


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
        self.execute_button = None
        self.worker_thread = None
        self.status_label_var = tk.StringVar(value="Ready")
        self.conn_state_var = tk.StringVar(value="Disconnected")

        # Other GUI elements
        self.solenoids = solenoids
        self.motors = motors

        # BLE UART pin control variables
        self.pin_ctrl = None

        # asyncio thread variables
        self.loop = None
        self.queue = None

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

        # Add next row first column - connect button
        buttons_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=buttons_row, column=0)
        self.connect_button = tk.Button(master=frame, text="Connect to Device", command=self.on_connect)
        self.connect_button.pack(padx=5, pady=5)

        # Add same row second column - execute commands button
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=buttons_row, column=1)
        self.execute_button = tk.Button(master=frame, text="Execute Commands", command=self.on_execute)
        self.execute_button.pack(padx=5, pady=5)
        self.execute_button["state"] = "disabled"

        # Add next row - status info
        status_label_row = window.grid_size()[1]
        frame = tk.Frame(
            master=window
        )
        frame.grid(row=status_label_row, column=0, columnspan=6)
        status_label = tk.Label(master=frame, textvariable=self.status_label_var)
        status_label.pack(pady=5)
        status_label.config(font=('Helvetica', 14), wraplength=400, justify=tk.LEFT)

        # Add connection state to bottom right
        status_label = tk.Label(master=main_window, textvariable=self.conn_state_var)
        status_label.pack(anchor=tk.SE)
        status_label.config(font=('Helvetica', 10))

        # Setup asyncio and handler thread
        self.loop = asyncio.new_event_loop()
        self.queue = queue.Queue()
        asyncio.set_event_loop(self.loop)
        self.worker_thread = threading.Thread(target=lambda: self.process_tasks())

    def process_tasks(self):
        while True:
            if self.queue.empty():
                pass
            else:
                coroutine = self.queue.get()
                coroutine()

    async def on_connect_async(self):
        try:
            self.pin_ctrl = await TrueTouch.new()
        except RuntimeError as err:  # Couldn't connect, update GUI state
            self.connect_button["state"] = "normal"
            self.status_label_var.set("Could not connect: {}".format(str(err)))
        else:  # Connected successfully, setup callbacks and update GUI state
            self.execute_button["state"] = "normal"
            self.status_label_var.set("Connected!")
            self.pin_ctrl.set_disconnect_callback(self.on_disconnect)
            self.conn_state_var.set("Connected: {}".format(self.pin_ctrl.get_mac()))

    def on_connect(self):
        # Disable buttons no longer used
        self.connect_button["state"] = "disabled"
        self.status_label_var.set("Attempting to connect ...")
        # Queue the update to be executed in the BLE send thread
        self.queue.put(lambda: self.loop.run_until_complete(self.on_connect_async()))

    async def on_execute_async(self, actuate_solenoids: List[TrueTouchFinger], release_solenoids: List[TrueTouchFinger],
                               pulse_solenoids: List[TrueTouchFinger], pulse_duration: int,
                               erm_motors: List[TrueTouchFinger], erm_duty_cycle: int):
        try:
            # Are there solenoids to set high?
            if len(actuate_solenoids) > 0:  # Send a GPIO high command
                temp_str = self.status_label_var.get()
                temp_str += "\nSetting high: {}...".format(actuate_solenoids)
                self.status_label_var.set(temp_str)

                await self.pin_ctrl.write_gpio(fingers=actuate_solenoids,
                                               output=TrueTouchGpioOutputs.OUT_HIGH)

                time.sleep(0.1)  # sleep for a little bit so things don't get flooded

            # Are there solenoids to set low?
            if len(release_solenoids) > 0:  # Send a GPIO high command
                temp_str = self.status_label_var.get()
                temp_str += "\nSetting low: {}...".format(release_solenoids)
                self.status_label_var.set(temp_str)

                await self.pin_ctrl.write_gpio(fingers=release_solenoids, output=TrueTouchGpioOutputs.OUT_LOW)

                time.sleep(0.1)  # sleep for a little bit so things don't get flooded

            # Are there solenoids to pulse?
            if len(pulse_solenoids) > 0:  # Send a GPIO high command
                temp_str = self.status_label_var.get()
                temp_str += "\nPulsing for {} ms: {}...".format(pulse_duration, pulse_solenoids)
                self.status_label_var.set(temp_str)

                await self.pin_ctrl.pulse_gpio(fingers=pulse_solenoids, duration_ms=pulse_duration)

                time.sleep(0.1)  # sleep for a little bit so things don't get flooded

            # Are there ERMs to PWM?
            if len(erm_motors) > 0:  # Send a GPIO high command
                temp_str = self.status_label_var.get()
                temp_str += "\nPWMing duty cycle {}/255: {}...".format(erm_duty_cycle, erm_motors)
                self.status_label_var.set(temp_str)

                await self.pin_ctrl.set_pwm(fingers=erm_motors, duty_cycle=erm_duty_cycle)

                time.sleep(0.1)  # sleep for a little bit so things don't get flooded
        except RuntimeError as err:  # Couldn't execute, update GUI state
            self.execute_button["state"] = "normal"
            self.status_label_var.set("Could not execute commands: {}".format(str(err)))
        else:
            self.execute_button["state"] = "normal"
            temp_str = self.status_label_var.get()
            temp_str += "\nSuccess!"
            self.status_label_var.set(temp_str)

    def on_execute(self):
        # Disable necessary GUI elements
        self.execute_button["state"] = "disabled"
        # Format a string to describe what's happening
        try:
            action_str = self.solenoids.get_action_str()
            action_str += self.motors.get_action_str()
        except ValueError as err:
            self.execute_button["state"] = "normal"
            self.status_label_var.set("Value error: {}".format(err))
        else:
            self.status_label_var.set("Executing Actions...")
            self.queue.put(lambda: self.loop.run_until_complete(
                self.on_execute_async(
                    self.solenoids.get_action_pins("High"),
                    self.solenoids.get_action_pins("Low"),
                    self.solenoids.get_action_pins("Pulse"),
                    self.solenoids.get_pulse_dur(),
                    self.motors.get_active_motors(),
                    self.motors.get_intensity()
                )
            ))

    def on_disconnect(self, client):
        self.connect_button["state"] = "normal"
        self.execute_button["state"] = "disabled"
        self.status_label_var.set("Disconnected from {}".format(client.address))
        self.conn_state_var.set("Disconnected")

    @staticmethod
    def separate_pins_by_port(pins: List[Tuple[int, int]]) -> Tuple[List[int], List[int]]:
        """
        Helper function to convert a list of pin tuples into two lists of pins numbers, one for each port.
        :param pins: list of tuples containing (port, pin)
        :return: two lists, the first containing pin numbers in port 0, the second having pin numbers in port 1
        """
        port_zero_pins = list()
        port_one_pins = list()

        for port_pin in pins:
            if port_pin[0] == 0:
                port_zero_pins.append(port_pin[1])
            else:
                port_one_pins.append(port_pin[1])

        return port_zero_pins, port_one_pins


def main():
    # Create a main window object
    window = tk.Tk()

    # Initialize solenoid options
    solenoids = Solenoids(window)

    # Initialize motor options
    motors = ERMMotors(window)

    # Initialize the main app
    app = BLEApp(window, solenoids, motors)
    app.worker_thread.start()

    window.mainloop()

    app.worker_thread.join()


if __name__ == "__main__":
    main()

"""
Arduino instrument ITL.
"""

import socket
import time

import azcam
import azcam.exceptions


class ArduinoQB(object):
    """
    The arduino instrument subclass for the ITL quantum bench.
    """

    def __init__(self):

        self.arduino_host = "10.0.2.50"
        self.arduino_address = (self.arduino_host, 80)
        self.client_socket = 0

    # ***************************************************************************
    # Arduino for LEDs and Fe55 control
    # ***************************************************************************

    def initialize(self):
        """
        Initialze arduino for LED and shutter control.
        """

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.arduino_address)

        # set Arduino pins for shutter mode at start
        self.send_command("S")

        return

    def close(self):
        self.client_socket.close()
        return

    def get_comps(self):
        """
        Return list of the active comp names.
        """

        complist = []

        return complist

    def set_comps(self, comp_names=["shutter"]):
        if type(comp_names) == list:
            lamps = " ".join(comp_names)
        else:
            lamps = comp_names.lower()

        if lamps == "shutter":
            self.send_command("S")
        elif lamps == "fe55":
            self.send_command("F")
        else:
            self.send_command("S")

        return

    def comps_on(self):
        """
        Turn active comparisons on.
        """

        self.set_shutter_state(1)

        return

    def comps_off(self):
        """
        Turn active comparisons off.
        """

        self.set_shutter_state(0)

        return

    def set_fe55(self, state=0):
        """
        Activate Fe55 (state=1) or deactivate (state=0).
        """

        return

    def send_command(self, cmd: str):
        """
        Send a command to the Arduino.
        """

        # client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # client_socket.connect(self.arduino_address)
        self.client_socket.send(cmd.encode())
        # client_socket.close()

    def set_shutter_state(self, state):
        """
        Open or close Oriel shutter.
        """

        state = int(state)

        if state:
            self.send_command("O")
        else:
            self.send_command("C")

        return

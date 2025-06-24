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

        self.arduino_host = "10.0.0.50"
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
        self.arduino_state = "shutter"

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

        if "shutter" in comp_names:
            self.send_command("S")
            self.arduino_state = "shutter"
        elif "fe55" in comp_names:
            self.send_command("F")
            self.arduino_state = "fe55"
        else:
            azcam.exceptions.warning(
                f"arduino_qb: Unknown comparison '{comp_names}' specified. "
                "Valid comparisons are 'shutter' and 'fe55'."
            )

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
        This is also called for Fe55 control from comps_on() and comps_off().
        
        For shutter control:
            state: 1 to open shutter, 0 to close shutter.
        For Fe55 control:
            state: 1 "opens" Fe55 (deactivates), 0 to "close" or deploy Fe55.
        """

        state = int(state)

        if state:
            self.send_command("O")
        else:
            if self.arduino_state == "shutter":
                self.send_command("S")
            elif self.arduino_state == "fe55":
                self.send_command("C")
            else:
                azcam.exceptions.warning(
                    f"arduino_qb: Unknown arduino state '{self.arduino_state}'. "
                    "Valid states are 'shutter' and 'fe55'."
                )

        return

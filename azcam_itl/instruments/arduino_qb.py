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

    # ***************************************************************************
    # Arduino for LEDs and Fe55 control
    # ***************************************************************************

    def initialize(self):
        """
        Initialze arduino for LED and shutter control.
        """

        # set Arduino pins for shutter mode at start
        self.send_command("S")

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

        return

    def comps_off(self):
        """
        Turn active comparisons off.
        """

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

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(self.arduino_address)
        client_socket.send(cmd.encode())
        client_socket.close()

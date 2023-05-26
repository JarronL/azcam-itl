import time
import datetime

from azcam.exceptions import AzcamError
import serial
import threading

import azcam
from azcam_server.tools.instrument import Instrument
from azcam_itl.instruments import pressure_vgc501
from azcam_itl.instruments import pressure_mks900
from azcam_itl.instruments import pressure_pkr361
from azcam_itl.instruments import webpower

"""
Power Outlets:
1 - TEC
2 - Vacuum
3 - NC
4 - Archon power
5 - 940 nm LED
6 - 640 nm LED
7 - 560 nm LED
8 - 405 nm LED
"""


class InstrumentEB(Instrument):
    """
    The Instrument interface to the ITL Electron Bench test system.
    """

    def __init__(self, tool_id="instrument", description="EB instrument"):
        super().__init__(tool_id, description)

        self.shutter_strobe = 1

        self.autofill_port = 2
        self.autofill_looptime = 3600 * 6
        self.autofill_filltime = 60

        # Web power switch instance
        self.power = webpower.WebPowerClass()
        self.power.service_name = "powerswitcheb"
        self.power.username = "lab"
        self.power.hostname = "powerswitcheb"

        # Aux.Web power switch instance
        self.poweraux = webpower.WebPowerClass()
        self.poweraux.service_name = "powerswitcheb2"
        self.poweraux.username = "lab"
        self.poweraux.hostname = "10.0.0.15"

        # Aux.Web power switch instance
        self.powerqb = webpower.WebPowerClass()
        self.powerqb.service_name = "powerswitchqb"
        self.powerqb.username = "lab"
        self.powerqb.hostname = "10.0.0.18"

        self.pressure_ids = [0, 1]  # [0, 1, 2, 4]
        self.pressure0 = pressure_mks900.PressureController("COM3")  # EB MKS controller
        self.pressure1 = pressure_vgc501.PressureController("COM4")  # EB ethernet mapped Pfeiffer
        self.pressure2 = pressure_vgc501.PressureController("COM11")  # EB ethernet mapped Agilent

        # create header
        self.define_keywords()

    def get_pressure(self, pressure_id=0):
        """
        Read an instrument pressure.
        Args:
            pressure_id: 0 is MKS, 1 is Pfeiffer
        Returns:
            pressure: -999 for bad pressure
        """

        try:
            if pressure_id == 0:
                reply = self.pressure0.read_pressure(1)  # temp 2 is for MKS CC

            elif pressure_id == 1:
                self.pressure1.read_pressure()
                reply = self.pressure1.read_pressure()

            elif pressure_id == 2:
                self.pressure2.read_pressure()
                reply = self.pressure2.read_pressure()

            else:
                reply = -999

        except Exception:
            reply = -1

        return reply

    def auto_fill(self):
        """
        Auto LN2 fill for a specific time.  Sleep before first fill.
        """

        now = datetime.datetime.now().strftime("%H:%M:%S")

        print(f"Turning LN2 fill on for {self.autofill_filltime} seconds at {now}")
        self.powerqb.turn_on(self.autofill_port)

        time.sleep(self.autofill_filltime)

        print("Turning LN2 fill off")
        self.powerqb.turn_off(self.autofill_port)

        return

    def set_autofill_state(self, state=0):
        """
        Sets autofill state: 1 or 0.
        """

        state = int(state)

        if state == 0:
            self.power.turn_off(self.autofill_port)
            azcam.log("stopping autofill loop")
            self.autofillstate = 0

        elif state == 1:
            azcam.log("starting autofill loop")
            self.autofillstate = 1
            self.autofillthread = threading.Thread(target=self.autofill_loop, args=[])
            self.autofillthread.start()

        return

    def autofill_loop(self):
        """
        Loop routine to run autofill, usually started in a thread from autofill() method.
        Delay before first fill.
        """

        while self.autofillstate:
            time.sleep(self.autofill_looptime)

            self.auto_fill()

        return

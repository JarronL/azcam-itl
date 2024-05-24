import serial

import azcam
from azcam.tools.instrument import Instrument

from azcam_itl.instruments import pressure_vgc401
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

"""
Defines the WebPower interface.

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


class InstrumentGort(Instrument):
    """
    The Instrument interface to the ITL GORT test system.
    """

    def __init__(self, tool_id, description="GORT instrument"):
        super().__init__(tool_id, description)

        self.shutter_strobe = 1

        # Web power switch instance
        self.power = webpower.WebPowerClass()
        self.power.service_name = "powerswitchgort"
        self.power.username = "lab"
        self.power.hostname = "powerswitchgort"

        # pressure controller instance
        self.pressure = pressure_vgc401.PressureController("COM22")

        # create header
        self.define_keywords()

    def get_pressure(self, PressureID=0):
        """
        Read an instrument pressure.
        """

        reply = self.pressure.read_pressure()

        return reply

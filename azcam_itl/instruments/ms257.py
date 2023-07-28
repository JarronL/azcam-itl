"""
MS257 77781 monochromator
"""

import pyvisa


class MS257(object):
    """
    Class for Newport MS257 monochromator.
    """

    def __init__(self, port="COM12"):
        self.MonoShutterState = -1
        self.CurrentWavelength = -1
        self.Filter1 = -1  # order block FW
        self.Filter2 = -1  # nd FW
        self.port = port

        try:
            self.rm = pyvisa.ResourceManager()
        except ValueError:
            azcam.log("PyVisa may not be installed")

    def initialize(self, reset=1):
        """
        Initialize monochromator.
        Newport ORIEL MS257 monochromator
        """

        self.mono = self.rm.open_resource(self.port)

        self.mono.timeout = 20000
        self.mono.write_termination = "\r"
        self.mono.read_termination = ">"

        # init monochromator
        cmd = "=SHTRTYPE M"
        self.mono.query(cmd).strip()
        cmd = "!PORTIN 0"
        self.mono.query(cmd).strip()
        cmd = "=CHNGPI D:395:A"
        self.mono.query(cmd).strip()
        if reset:
            cmd = "!GW  400"
            self.mono.query(cmd).strip()
            cmd = "!FILT1 0"  # auto filter
            self.mono.query(cmd).strip()
            cmd = "!FILT2 0"  # auto filter
            self.mono.query(cmd).strip()

        return

    def read_mono(self):
        """
        Read all monochromater values.
        """

        reply = self.mono.query("?PW").strip()
        wavelength = float(reply)
        wavelength = f"{wavelength:0.03f}"
        reply = self.mono.query("?FILT1").strip()
        filter1 = reply[-1]
        reply = self.mono.query("?FILT2").strip()
        filter2 = reply[-1]

        return [wavelength, filter1, filter2]

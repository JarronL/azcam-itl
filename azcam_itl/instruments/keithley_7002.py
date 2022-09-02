import azcam

from azcam_itl.instruments.visa_comm import VisaComm


class Switcher(VisaComm):
    """
    Class for Keithley switcher communications.
    """

    def __init__(self, Address):
        """ """

        self.Address = Address

        self.instr = VisaComm.__init__(self, self.Address)

    def initialize(self):
        """
        Initialize hardware.
        """

        reply = self.open_comm()

        reply = self.instr.query("*IDN?")
        reply = reply.strip()
        azcam.log("ISDN response: %s" % reply)

        self.initialized = 1

        return

    def open_all(self):
        """
        Open all switches.
        """

        self.send("OPEN ALL;")

        return

    def close_switch(self, Switch):
        """
        Close one switch.
        Switch format like '1!1,1!2'.
        """

        self.send(":CLOS (@%s)" % Switch)

        return

import azcam

from azcam_itl.instruments.visa_comm import VisaComm


class VoltageSource(VisaComm):
    """
    Class for Keithley voltage source communications.
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

        # setup for reading current
        s = "B1V5.0000I0W0.003X"
        reply = self.command(s)
        s = "R0P0F1T4X"
        reply = self.command(s)

        self.initialized = 1

        return

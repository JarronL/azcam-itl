import azcam

from azcam_itl.instruments.visa_comm import VisaComm


class Multimeter(VisaComm):
    """
    Class for Keithley multimeter communications.
    """

    def __init__(self, Address):
        """ """

        self.Address = Address

        self.instr = VisaComm.__init__(self, self.Address)

    def initialize(self):
        """
        Initialize hardware for current reading.
        """

        reply = self.open_comm()

        reply = self.instr.query("*IDN?")
        reply = reply.strip()
        azcam.log("ISDN response: %s" % reply)

        # setup for reading current
        s = '*RST;:FORM:ELEM READ;:INIT:CONT OFF;:FUNC "CURR:DC";:CURR:DC:RANG:AUTO ON'
        reply = self.send(s)

        self.is_initialized = 1

        return

    def get_current(self):
        """
        Read current.
        """

        current = -1

        reply = self.command(":READ?")
        reply = reply.strip()
        current = float(reply)

        return current

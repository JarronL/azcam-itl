from .visa_comm import VisaComm


class EGProber(VisaComm):
    """
    Class for EG 4090u+ prober communications.
    """

    def __init__(self, Address):
        """ """

        self.Address = Address

        self.instr = VisaComm.__init__(self, self.Address)

    def initialize(self):
        """
        Initialize hardware.
        """

        self.open_comm()

        # don't ISDN? because of bad char in return string (mu)

        self.initialized = 1

        return

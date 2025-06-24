"""
MS257 77781 monochromator
"""

import time
import pyvisa

import azcam
import azcam.exceptions

class MS257(object):
    """
    Class for Newport MS257 monochromator.
    """

    """
    Grating 1: 77743 -  600 lpm, 225 blaze, 200 - 400 nm
    Grating 2: 77744 - 600 lpm, 370 nm blaze, 270 - 1000 nm
    """

    def __init__(self, port="COM12"):
        self.MonoShutterState = -1
        self.CurrentWavelength = -1
        self.Filter1 = -1  # order block FW
        self.Filter2 = -1  # nd FW
        self.port = port

        self.mono = None
        self.rm = pyvisa.ResourceManager()

    def query(self, cmd):
        """
        Send a command to the monochromator and return the response.
        """

        if self.mono is None:
            raise azcam.exceptions.AzcamError("Monochromator not initialized. Run initialize() first.")

        reply = self.mono.query(cmd).strip()
        # if reply == ">":
        #     reply = ""
        return reply


    def initialize(self, reset : int = 1):
        """
        Initialize monochromator.
        Newport ORIEL MS257 monochromator

        :param reset: 1 to reset monochromator, 0 to not reset
        :type reset: int
        :return: None
        """

        self.mono = self.rm.open_resource(self.port)

        self.mono.timeout = 20000
        self.mono.write_termination = "\r"
        self.mono.read_termination = ">"

        # init monochromator
        # self.query("=SHTRTYPE M")  # Set shutter type to manual
        self.query("=SHTRTYPE F")  # Set shutter type to fast
        self.query("!PORTIN 0")    # Set to 0 for Auto Port selection BNC AUX OUT level
        self.query("=CHNGPI D:395:A") # Wavelength transition point between D and A (although, there is no D???)
        if reset:
            # Command value 0 on each filter wheel for position auto selection
            self._set_filter(0, filter_id=1)
            self._set_filter(0, filter_id=2)
             # Set wavelength to 400 nm
            self.set_wavelength(400)

        # Populate parameters
        self.set_shutter(1)  # Set shutter to open (1)
        _ = self.get_wavelength()
        _ = self.get_loaded_filters()

        return
    
    # def get_shutter(self):
    #     """
    #     Get current shutter state.
    #     0 is closed, 1 is open.
    #     """

    #     reply = self.mono.query("?SHUTTER").strip()
    #     if reply == "0":
    #         self.MonoShutterState = 0
    #     elif reply == "1":
    #         self.MonoShutterState = 1
    #     else:
    #         raise azcam.exceptions.AzcamError(f"Unknown shutter state: {reply}")

    #     return self.MonoShutterState

    def set_shutter(self, state):
        """
        Open (1) or close (0) shutter.
        """

        self.mono.query(f"!SHUTTER {state}").strip()
        self.MonoShutterState = state

    def read_mono(self):
        """
        Read all monochromater values.
        """

        wavelength = self.get_wavelength()
        wavelength = f"{wavelength:0.03f}"
        filter1 = self.query("?FILT1")[-1]
        filter2 = self.query("?FILT2")[-1]

        return [wavelength, filter1, filter2]

    def set_wavelength(self, wavelength):#, wavelength_id=0):
        """
        Set monochromator wavelength (nm).
        """

        dw = abs(self.CurrentWavelength - float(wavelength))
        if dw < 0.001:
            azcam.log(f"MS257: wavelength {wavelength} already set, no change", level=2)
            return

        self.mono.query(f"!GW {wavelength}").strip()
        time.sleep(1)
        _ = self.get_wavelength()  # update current wavelength

        return

    def get_wavelength(self):#, wavelength_id=0):
        """
        Get monochromator wavelength (nm).
        """

        reply = self.mono.query("?PW").strip()
        self.CurrentWavelength = round(float(reply), 3)

        return reply
    
    def get_filter(self, filter_id=0):
        """
        Get filter wheel position.
        """

        filt = self.mono.query(f"?FILT{filter_id}").strip()

        return filt
    
    def get_loaded_filters(self):#, filter_id=0):
        """
        Get the current filter positions.
        filter_id is 1 for FilterWheel 1 (ND) and 2 for FilterWheel 2 (Order Blocking).
        Return is like A:3 or M:2 for auto or manual mode.
        """

        reply = self.get_filter(1)
        tokens = reply.split(":")
        self.Filter1 = int(tokens[1])

        reply = self.get_filter(2)
        tokens = reply.split(":")
        self.Filter2 = int(tokens[1])

        return [self.Filter1, self.Filter2]
    
    def _set_filter(self, position, filter_id=0):
        """
        Set filter wheel position.
        """

        self.query(f"!FILT{filter_id} {position}")

        return
    
    def set_filter(self, position, filter_id=1):
        """
        Set the current filter position.
        filter_id is 1 for FilterWheel 1 (ND) and 2 for FilterWheel 2 (Order Blocking).
        """

        fid = int(filter_id)
        pint = int(position)

        if fid == 1:
            self._set_filter(pint, 1)
        elif fid == 2:
            self._set_filter(pint, 2)
        else:
            raise azcam.exceptions.AzcamError(f"bad filter_id {filter_id} in set_filter")

        time.sleep(2)
        _ = self.get_loaded_filters()  # update current filter positions

        return
import time

import azcam
import azcam.exceptions
import azcam.sockets
from azcam.tools.instrument import Instrument
from azcam_itl.instruments.ms257 import MS257
from azcam_itl.instruments.newport_1936_R import NewPort_1936r
from azcam_itl.instruments.arduino_qb import ArduinoQB
from azcam_itl.instruments import webpower

from azcam_itl.instruments import pressure_mks900


class InstrumentQB(Instrument):
    """
    The Instrument interface to the ITL Detector Characterization Quantum system.
    """

    def __init__(self, tool_id="instrument", description="QB instrument"):
        super().__init__(tool_id, description)

        self.shutter_strobe = 1

        # comps
        self.active_comps = ["shutter"]

        # define header keywords
        self.define_keywords()

        return

    def initialize(self):
        """
        Initialize hardware.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.exceptions.warning(f"{self.description} is not enabled")
            return

        try:
            self.n1936 = NewPort_1936r()
            self.n1936.initialize()
        except Exception as e:
            azcam.log(f"Could not initialize power meter - {e}")

        try:
            self.mono = MS257()
            self.mono.initialize()
        except Exception as e:
            azcam.log(f"could not initialize monochromator {e}")

        try:
            self.arduino = ArduinoQB()
            self.arduino.initialize()
        except Exception as e:
            azcam.log(f"Could not initialize arduino - {e}")

        try:
            self.pressure = pressure_mks900.PressureController("COM9")  # COM9 on QB
        except Exception as e:
            azcam.log(f"Could not initialize pressure - {e}")

        # QB web power switch instance
        self.power = webpower.WebPowerClass()
        self.power.service_name = "powerswitchqb"
        self.power.username = "lab"
        self.power.hostname = "10.131.0.5"

        self.initialized = 1

        return

    # header

    def define_keywords(self):
        """
        Defines and resets instrument keywords.
        """

        self.set_keyword("WAVLNGTH", 0.0, "Wavelength of monochromator", "float")
        self.set_keyword("WAVEUNIT", "nm", "Wavelength units", "str")

        return

    def get_keyword(self, keyword):
        """
        Read an instrument keyword value.
        This command will read hardware to obtain the keyword value.
        """

        if keyword == "WAVEUNIT":
            reply = "nm"
        elif keyword == "WAVLNGTH":
            reply = self.get_wavelength()
        elif keyword == "FILTER1":
            reply = self.get_filter(1)
        elif keyword == "FILTER2":
            reply = self.get_filter(2)
        else:
            try:
                reply = self.header.values[keyword]
            except Exception:
                return []

        # store value in Header
        self.set_keyword(keyword, reply)

        reply, t = self.header.convert_type(reply, self.header.typestrings[keyword])

        return [reply, self.header.comments[keyword], t]

    # shutter

    def set_shutter(self, state, shutter_id: int = 0):
        """
        Open or close shutter.
        0 is mono shutter, 1 is arduino shutter command
        """

<<<<<<< HEAD
=======
        shutter_id = int(shutter_id)

>>>>>>> dev
        if shutter_id == 0:
            self.mono.mono.query(f"!SHUTTER {state}").strip()
            self.MonoShutterState = int(state)
        elif shutter_id == 1:
            self.arduino.set_shutter_state(state)

        return

    # Monochrometer

    def set_wavelength(self, wavelength, wavelength_id=0):
        """
        Set monochomator wavelength (nm).
        """

        self.mono.mono.query(f"!GW {wavelength}").strip()
        time.sleep(2)
        self.CurrentWavelength = float(wavelength)

        return

    def get_wavelength(self, wavelength_id=0):
        """
        Get monochomator wavelength (nm).
        """

        reply = self.mono.mono.query("?PW").strip()
        w = int(float(reply) * 1000) / 1000.0
        wave = float(w)
        self.CurrentWavelength = w

        return wave

    def get_filter(self, filter_id=0):
        """
        Get filter wheel position.
        """

        filt = self.mono.mono.query(f"?FILT{filter_id}").strip()

        return filt

    def get_filters(self, filter_id=0):
        """
        Return a list of all available/loaded filters.
        filter_id is the filter mechanism ID.
        """

        filters = [1, 2, 3, 4, 5, 6]

        return filters

    def get_loaded_filters(self, filter_id=0):
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

    def set_filter(self, filter, filter_id=1):
        """
        Set the current filter position.
        filter_id is 1 for FilterWheel 1 (ND) and 2 for FilterWheel 2 (Order Blocking).
        """

        fid = int(filter_id)

        if fid == 1:
            f1 = filter
            self._set_filter1({str(f1)}, 1)
            self.Filter1 = f1

        elif fid == 2:
            f2 = filter
            self._set_filter1({str(f2)}, 2)
            self.Filter2 = f2
        else:
            raise azcam.exceptions.AzcamError("bad filter_id in set_filter")

        time.sleep(2)

    def _set_filter1(self, position, filter_id=0):
        """
        Set filter wheel position.
        """

        self.mono.mono.query(f"!FILT{filter_id} {position}")

        return

        return

    # Newport power meter

    def init_powermeter(self):
        """
        Initialize Newport power meter.
        Newport optical power meter 1936-R - USB
        """

        self.n1936.initialize()

        self.n1936.select_units("watts/cm2")

        return

    def get_power1(self, wavelength):
        """
        Returns mean power [W/cm2] @ wavelength.
        """

        # wave, power = self.n1936.read_instant_power(int(wavelength))
        wave, meanpower, stdpower = self.n1936.read_buffer(int(wavelength), 100, 1)

        return meanpower

    def get_power(self, wavelength, power_id=0) -> float:
        """
        Get power reading at specified wavelength.
        Be sure to set instrument wavelength first.
        Args:
            wavelength: wavelength for power meter
            power_id: power ID flag
        Returns:
            mean_power: mean power in Watts/cm2
        """

        wavelength = int(wavelength)

        reply = self.get_power1(wavelength)

        power = float(reply)

        return power

    def get_pressure(self, pressure_id=0):
        """
        Read an instrument pressure.
        """

        return self.pressure.read_pressure(pressure_id)

    def set_comps(self, comp_names=["shutter"]):
        """
        Set arduino state.
        """

        self.arduino.set_comps(comp_names)

        return

    def get_all_comps(self):
        """
        Return all valid comparison names.
        Useful for clients to determine which type of comparison exposures are supported.
        """

        comps = ["Fe55"]

        return comps

    def comps_on(self):
        """
        Turn active comparisons on.
        """

        self.arduino.comps_on()

        return

    def comps_off(self):
        """
        Turn active comparisons off.
        """

        self.arduino.comps_off()

        return

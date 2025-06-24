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

        # NOTE: Turn off later strobe if no BNC cable is connected
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

        if self.is_initialized:
            return

        if not self.is_enabled:
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

            # use arduino shutter by default
            self.use_mono_shutter(0)  
        except Exception as e:
            azcam.log(f"Could not initialize arduino - {e}")

            # use mono shutter if arduino fails
            azcam.log(f"Attempting to use mono shutter instead of arduino.")
            self.use_mono_shutter(1)

        try:
            self.pressure = pressure_mks900.PressureController("COM9")  # COM9 on QB
        except Exception as e:
            azcam.log(f"Could not initialize pressure - {e}")

        # QB web power switch instance
        self.power = webpower.WebPowerClass()
        self.power.service_name = "powerswitchqb"
        self.power.username = "lab"
        self.power.hostname = "10.131.0.5"

        self.is_initialized = 1

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


    # Monochomator properties

    @property
    def MonoShutterState(self):
        """
        Current state of the monochromator shutter.
        0 is closed, 1 is open.
        """
        return self.mono.MonoShutterState
    @MonoShutterState.setter
    def MonoShutterState(self, value):
        raise RuntimeError('MonoShutterState not directly settable. Use set_shutter_mono() instead.')
    @property
    def CurrentWavelength(self):
        """
        Current wavelength of the monochromator.
        """
        return self.mono.CurrentWavelength
    @CurrentWavelength.setter
    def CurrentWavelength(self, value):
        raise RuntimeError('CurrentWavelength not directly settable. Use set_wavelength() instead.')
    @property
    def Filter1(self):
        """
        Current position of filter wheel 1 (ND).
        """
        return self.mono.Filter1
    @Filter1.setter
    def Filter1(self, value):
        raise RuntimeError('Filter1 not directly settable. Use set_filter() instead.')
    @property
    def Filter2(self):
        """
        Current position of filter wheel 2 (Order Blocking).
        """
        return self.mono.Filter2
    @Filter2.setter
    def Filter2(self, value):
        raise RuntimeError('Filter2 not directly settable. Use set_filter() instead.')

    # shutter

    def use_mono_shutter(self, value: int = 1):
        """
        Set whether to use the monochromator shutter.
        If value=1 (True), the monochromator shutter will be used.
        If value=0 (False), the arduino shutter will be used.
        """

        value = int(value)

        if value==1:
            # Close the monochromator shutter
            self.set_shutter_mono(0)
            self._use_mono_shutter = True
            # Open the arduino shutter
            self.set_shutter_arduino(1)
            self._use_arduino_shutter = False
        elif value==0:
            # Close the arduino shutter
            self.set_shutter_arduino(0)
            self._use_arduino_shutter = True
            # Open the monochromator shutter
            self.set_shutter_mono(1)
            self._use_mono_shutter = False
        else:
            azcam.exceptions.warning("use_mono_shutter value must be 0 or 1")

        return

    def set_shutter(self, state, shutter_id: int = 0):
        """
        Open (1) or close (0) shutter.
        0 is mono shutter, 1 is arduino shutter command
        """

        shutter_id = int(shutter_id)

        if shutter_id == 0:
            try:
                self.mono.set_shutter(state)
            except Exception as e:
                azcam.log(f"Error setting monochromator shutter state: {e}")

        elif shutter_id == 1:
            try:
                self.arduino.set_shutter_state(state)
            except Exception as e:
                azcam.log(f"Error setting arduino shutter state: {e}")

        return
    
    def set_shutter_arduino(self, state):
        """
        Set the arduino shutter state.
        0 is closed, 1 is open.
        """
        self.set_shutter(state, 1)
        return
    
    def set_shutter_mono(self, state):
        """
        Set the monochrometer shutter state.
        0 is closed, 1 is open.
        """
        self.set_shutter(state, 0)
        return

    # Monochrometer

    def set_wavelength(self, wavelength, *args, **kwargs):#, wavelength_id=0):
        """
        Set monochromator wavelength (nm).
        """

        self.mono.set_wavelength(float(wavelength))

        return

    def get_wavelength(self, *args, **kwargs):#, wavelength_id=0):
        """
        Get monochromator wavelength (nm).
        """

        return self.mono.get_wavelength()

    def get_filter(self, filter_id=0):
        """
        Get filter wheel position.
        """

        return self.mono.get_filter(filter_id)

    def get_filters(self, *args, **kwargs): #filter_id=0):
        """
        Return a list of all available/loaded filters.
        filter_id is the filter mechanism ID.
        """

        filters = [1, 2, 3, 4, 5, 6]

        return filters

    def get_loaded_filters(self, *args, **kwargs):#, filter_id=0):
        """
        Get the current filter positions.
        filter_id is 1 for FilterWheel 1 (ND) and 2 for FilterWheel 2 (Order Blocking).
        Return is like A:3 or M:2 for auto or manual mode.
        """

        return self.mono.get_loaded_filters()

    def set_filter(self, filter, filter_id=1):
        """
        Set the current filter position.
        filter_id is 1 for FilterWheel 1 (ND) and 2 for FilterWheel 2 (Order Blocking).
        """

        fid = int(filter_id)
        position = int(filter)

        return self.mono.set_filter(position, filter_id=fid)


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
        if isinstance(comp_names, str):
            comp_names = [comp_names]
            
        comp_names = [c.lower() for c in comp_names]
        if ("shutter" in comp_names) and (not self._use_arduino_shutter):
            pass
        else:
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

        if self.arduino.arduino_state=='fe55':
            self.arduino.comps_on()
        elif self.arduino.arduino_state=='shutter':
            # Only open required shutters
            if self._use_arduino_shutter:
                self.set_shutter_arduino(1)
            if self._use_mono_shutter:
                self.set_shutter_mono(1)
                self.set_shutter_arduino(1)

        return

    def comps_off(self):
        """
        Turn active comparisons off.
        """

        if self.arduino.arduino_state=='fe55':
            self.arduino.comps_off()
        elif self.arduino.arduino_state=='shutter':
            # Only close required shutters
            # Arduino shutter state
            if self._use_arduino_shutter:
                self.set_shutter_arduino(0)
            # Mono shutter state
            if self._use_mono_shutter:
                self.set_shutter_mono(0)
                self.set_shutter_arduino(1)

        return

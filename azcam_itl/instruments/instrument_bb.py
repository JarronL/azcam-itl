"""
Instrument control for ITL BosonBench.
"""

import time

from pydantic import validate_arguments

import azcam
from azcam import exceptions
from azcam.server.tools.instrument import Instrument

from azcam_itl.instruments import keithley_6482

# import pressure_pkr361
from azcam_itl.instruments import filters_bb
from azcam_itl.instruments import newport_1936_R
from azcam_itl.instruments import shutter_control
from azcam_itl.instruments import webpower

"""
Power Outlets:
1 -
2 - dewar valve
3 - shutter control box
4 - Uniblitz shutter
5 - Filter wheels
6 - lamp power supply
7 - pressure gauge
8 - outlet strip
"""


class InstrumentBB(Instrument):
    """
    The Instrument class to the ITL BosonBench system.
    """

    def __init__(self, tool_id="instrument", description="BB instrument"):
        super().__init__(tool_id, description)

        self.shutter_strobe = 1

        # web power switch
        self.power = webpower.WebPowerClass()
        self.power.service_name = "powerswitchbb"
        self.power.username = "lab"
        self.power.hostname = "powerswitchbb"

        # shutter controller
        self.shutter = shutter_control.ShutterControllerClass("COM20")

        # pressure controller
        # self.pressure = pressure_vgc401.PressureController("COM23")

        # newport power meter
        self.newport_pm = newport_1936_R.NewPort_1936r()

        # electrometer
        self.current_ids = [0, 1]
        self.diodes = keithley_6482.DiodeControllerClass()

        # filters
        self.filters = filters_bb.FilterControllerBB(["COM12", "COM13", "COM14"])
        self.filters.filter_wavelengths = {
            "clear": [1, 1],
            "330": [2, 1],
            "350": [3, 1],
            "370": [4, 1],
            "400": [5, 1],
            "500": [6, 1],
            "600": [1, 2],
            "700": [1, 3],
            "800": [1, 4],
            "900": [1, 5],
            "1000": [1, 6],
        }
        # ND filters3: NDA~0.2, NDB~0.08, NDC~0.01 very approximately
        f1 = [0, 330, 350, 370, 400, 500]
        f2 = [0, 600, 700, 800, 900, 1000]
        f3 = [0, "NDA", "NDB", "NDC", 0, 0]
        self.filters.loaded_filters = [f1, f2, f3]  # not used

        # comps
        self.active_comps = ["shutter"]

        # create header
        self.define_keywords()

    def initialize(self):
        """
        Initialize hardware.
        """

        if self.initialized:
            return

        if not self.enabled:
            exceptions.warning(f"{self.description} is not enabled")
            return

        try:
            self.power.initialize()
        except Exception:
            pass

        try:
            self.diodes.initialize()
        except Exception:
            pass

        self.shutter.initialize()
        self.set_comps()  # set default to shutter

        # self.pressure.initialize()
        # self.pressure1.initialize()

        try:
            self.newport_pm.initialize()
        except Exception:
            pass

        self.filters.initialize()
        self.set_wavelength(400)  # start at known wavelength
        self.set_filter(1, 2)  # start with open neutral density

        self.initialized = 1

        return

    # ***************************************************************************
    # header
    # ***************************************************************************
    def define_keywords(self):
        """
        Defines and resets instrument keywords.
        """

        self.set_keyword("WAVLNGTH", 0.0, "Wavelength of illumination", "float")
        self.set_keyword("WAVEUNIT", "nm", "Wavelength units")
        # self.set_keyword("DEWPRES", 0.0, "Dewar pressure", "float")
        # self.set_keyword("UNITPRES", "Torr", "Pressure units")
        self.set_keyword("DIODECUR", 0.0, "reference diode current", "float")

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
        elif keyword == "DEWPRES":
            reply = self.get_pressure()
        else:
            reply = self.header.values[keyword]

        # store value in Header
        self.set_keyword(keyword, reply)

        reply, t = self.header.convert_type(reply, self.header.typestrings[keyword])

        return [reply, self.header.comments[keyword], t]

    # ***************************************************************************
    # comparisons
    # ***************************************************************************
    def get_all_comps(self):
        """
        Return all valid comparison names.
        Useful for clients to determine which type of comparison exposures are supported.
        """

        comps = ["LED", "Fe55", "shutter"]

        return comps

    def set_comps(self, comp_names=[""]):
        """
        Set comparisons which are to be turned on and off with comps_on() and comps_off().
        comp_names is a single string or a list of strings to be set as active.
        """

        if type(comp_names) == list:
            lamp = comp_names[0].strip("'\"")  # strip quotes
        else:
            lamp = comp_names.strip("'\"")

        if lamp.lower() == "fe-55" or lamp.lower() == "fe55":
            self.active_comps[0] = "fe55"
            function = "F"
        elif lamp.lower() == "led":
            self.active_comps[0] = "led"
            function = "L"
        elif lamp.lower() == "growth":
            self.active_comps[0] = "growth"
            function = "G"
        else:
            self.active_comps[0] = "shutter"
            function = "S"

        reply = self.shutter.set_state(function)

        return reply

    def comps_on(self):
        """
        Turn on active comparisons.
        During an exposure don't call this as the shutter controls the comparisons.
        """

        reply = self.shutter.set_state("O")

        return reply

    def comps_off(self):
        """
        Turn off active comparisons.
        During an exposure don't call this as the shutter controls the comparisons.
        """

        reply = self.shutter.set_state("C")

        return reply

    # ***************************************************************************
    # shutter
    # ***************************************************************************
    def set_shutter(self, state, shutter_id=0):
        """
        Open or close the instrument shutter.
        state is 1 for open and 0 for close.
        shutter_id is the shutter mechanism ID.
        """

        state = int(state)

        self.shutter.set_state("S")
        if state:
            self.shutter.set_state("O")
        else:
            self.shutter.set_state("C")

        return

    # ************************************************************
    # Electrometer
    # ************************************************************
    def get_current(self, shutter_state: int = 1, current_id: int = 0) -> float:
        """
        Read Electrometer diode current in Amps.
        Args:
            ShutterState is 0, 1 to close/open shutter during read or 2 unchanged.
            current_id = 0 is the sphere (Reference) diode.
            current_id = 1 is the calibrated diode or DUT.
        Returns:
            current: measured current in amps
        """

        current_id = int(current_id)
        shutter_state = int(shutter_state)

        # open shutter and wait for stable reading
        if shutter_state == 1:
            self.set_shutter(1)
            time.sleep(1)
        elif shutter_state == 0:
            self.set_shutter(0)

        reply = self.diodes.read_diodes()  # reads both diodes together
        if shutter_state == 1:
            self.set_shutter(0)

        if current_id == 0:
            return reply[0]
        elif current_id == 1:
            return reply[1]
        else:
            raise exceptions.AzcamError("bad current_id value")

    # ***************************************************************************
    # pressure
    # ***************************************************************************
    def get_pressure(self, pressure_id=0):
        """
        Read an instrument pressure.
        """

        return self.pressure.read_pressure(pressure_id)

    # ***************************************************************************
    # filters
    # ***************************************************************************
    @validate_arguments
    def get_filters(self, filter_id: int = 0) -> list:
        """
        Return a list of all available/loaded filters.
        """

        return self.filters.get_filters(filter_id)

    def get_filter(self, filter_id=0):
        """
        Return the current/loaded filter, typically the filter in the beam.
        filter_id is the filter mechanism ID.
        """

        return self.filters.get_filter(filter_id)

    def set_filter(self, filter_name, filter_id=0):
        """
        Set the current/loaded filter, typically the filter in the beam.
        filter_name is the filter name to set.
        filter_id is the filter mechanism ID.
        """

        return self.filters.set_filter(filter_name, filter_id)

        return

    # ***************************************************************************
    # wavelengths
    # ***************************************************************************
    def get_wavelengths(self, wavelength_id=0):
        """
        Returns a list of valid wavelengths.
        Used for filter and LED based systems.
        wavelength_id is the wavelength mechanism ID.
        """

        return self.filters.get_wavelengths(wavelength_id)

    def get_wavelength(self, wavelength_id=0):
        """
        Returns the current wavelength.
        wavelength_id is the wavelength mechanism ID.
        """

        return self.filters.get_wavelength(wavelength_id)

    def set_wavelength(self, wavelength, wavelength_id=0):
        """
        Set the current wavelength, typically for a filter or grating.
        wavelength is the wavelength value.
        wavelength_id is the wavelength mechanism ID.
        """

        return self.filters.set_wavelength(wavelength, wavelength_id)

    # ***************************************************************************
    # power meter
    # ***************************************************************************
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

        if self.newport_pm.status == "Connected":
            # print("Serial number is " + str(self.newport_pm.serial_number))
            # print("Model name is " + str(self.newport_pm.model_number))
            # print(nd.query('ERRors?'))
            # Print the IDN of the newport detector.
            # print("Connected to " + self.newport_pm.query("*IDN?"))

            # 100 reading of the newport detector at 500 nm wavelength and plot them
            [actualwavelength, mean_power, std_power] = self.newport_pm.read_buffer(
                wavelength=wavelength, buff_size=10, interval_ms=1
            )

            # Close the device
            # self.newport_pm.close_device()

            return mean_power

        elif self.newport_pm.status != "Connected":
            raise exceptions.AzcamError("Cannot connect to Newport power meter")

    def get_focus(self, focus_id=0):
        return 123

    def set_focus(self, value, focus_id=0, focus_type="step"):
        return

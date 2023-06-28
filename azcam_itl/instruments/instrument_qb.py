import time

import pyvisa

import azcam
import azcam.sockets
from azcam_server.tools.instrument import Instrument
from azcam_itl.instruments.keithley_6512 import EM6512
from azcam_itl.instruments.newport_1936_R import NewPort_1936r
from azcam_itl.instruments import pressure_mks900
from azcam_itl.instruments import shutter_control
from azcam_itl.instruments import webpower


class InstrumentQB(Instrument):
    """
    The Instrument interface to the ITL Detector Characterization Quantum system.
    """

    def __init__(self, tool_id="instrument", description="QB instrument"):
        super().__init__(tool_id, description)

        self.MonoShutterState = -1
        self.CurrentWavelength = -1
        self.shutter_strobe = 1
        self.Filter1 = -1  # order block FW
        self.Filter2 = -1  # nd FW

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
            azcam.AzcamWarning(f"{self.description} is not enabled")
            return

        try:
            self.rm = pyvisa.ResourceManager()
        except ValueError:
            azcam.log("PyVisa may not be installed")

        try:
            self.n1936 = NewPort_1936r()
        except Exception as e:
            azcam.log(f"Newport 1936 error - {e}")

        try:
            self.mono = self.rm.open_resource("COM10")
        except Exception as e:
            azcam.log(f"Monochromator error - {e}")

        try:
            self.shutter = shutter_control.ShutterControllerClass("COM8")
        except Exception as e:
            azcam.log(f"Shutter controller error - {e}")

        # try:
        #     self.k6512 = EM6512("GPIB0::22::INSTR")
        # except Exception as e:
        #     azcam.log(f"Keithley 6512 error - {e}")

        # try:
        #     self.k6514 = self.rm.open_resource("COM9")
        # except Exception as e:
        #     azcam.log(f"Keithley 6514 error - {e}")

        # try:
        #     self.pressure = pressure_mks900.PressureController("COM7")
        # except Exception as e:
        #     azcam.log(f"Pressure PDR900 error - {e}")

        # try:
        #     self.init_powermeter()
        # except Exception as e:
        #     azcam.log(f"could not initialize powermeter: {e}")

        try:
            self.init_mono()
            self.set_wavelength(450)
            self.set_filter(0, 1)  # auto filters
            self.set_filter(0, 2)
        except Exception as e:
            azcam.log(f"could not initialize monochromator {e}")

        try:
            self.shutter.initialize()
            self.set_comps()  # set default to shutter
        except Exception as e:
            azcam.log(f"could not initialize shutter {e}")

        if 0:
            try:
                self.init_dut_meter()
            except Exception as e:
                azcam.log(f"could not initialize DUT meter {e}")

        if 0:
            try:
                self.init_refdiode_meter()
            except Exception as e:
                azcam.log(f"could not initialize ref diode meter {e}")

        # QB web power switch instance
        self.power = webpower.WebPowerClass()
        self.power.service_name = "powerswitchqb"
        self.power.username = "lab"
        self.power.hostname = "10.131.0.5"

        self.initialized = 1

        return

    def server_command(self, command: str, timeout: int = -1, terminator: str = "\n"):
        """
        Wrapper for command to instrument server.
        """

        try:
            reply = self.iserver.command(command)
        except Exception as e:
            azcam.log(f"instrument communication error: {e}")
            reply = None

        return reply

    # ***************************************************************************
    # header
    # ***************************************************************************

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
        elif keyword == "DIODECUR":
            reply = self.get_current()
        else:
            try:
                reply = self.header.values[keyword]
            except Exception:
                return []

        # store value in Header
        self.set_keyword(keyword, reply)

        reply, t = self.header.convert_type(reply, self.header.typestrings[keyword])

        return [reply, self.header.comments[keyword], t]

    # ***************************************************************************
    # comparisons - shutter controller
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

    # ************************************************************
    # Monochrometer
    # ************************************************************
    def init_mono(self, reset=0):
        """
        Initialize monochromator.
        Newport ORIEL MS257 monochromator
        """

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
            cmd = "!FILT1 0"
            self.mono.query(cmd).strip()
            cmd = "!FILT2 0"
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

    def set_filter1(self, position, filter_id=0):
        """
        Set filter wheel position.
        """

        self.mono.query(f"!FILT{filter_id} {position}")

        return

    def get_filter(self, filter_id=0):
        """
        Get filter wheel position.
        """

        filt = self.mono.query(f"?FILT{filter_id}").strip()

        return filt

    def set_wavelength(self, wavelength, wavelength_id=0):
        """
        Set monochomator wavelength (nm).
        """

        self.mono.query(f"!GW {wavelength}").strip()
        time.sleep(2)
        self.CurrentWavelength = float(wavelength)

        return

    def get_wavelength(self, wavelength_id=0):
        """
        Get monochomator wavelength (nm).
        """

        reply = self.mono.query("?PW").strip()
        w = int(float(reply) * 1000) / 1000.0
        wave = float(w)
        self.CurrentWavelength = w

        return wave

    def set_shutter(self, state):
        """
        Open (1) or close (0) monochomator shutter.
        """

        self.mono.query(f"!SHUTTER {state}").strip()
        self.MonoShutterState = int(state)

        return

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
            self.set_filter1({str(f1)}, 1)
            self.Filter1 = f1

        elif fid == 2:
            f2 = filter
            self.set_filter1({str(f2)}, 2)
            self.Filter2 = f2
        else:
            raise azcam.AzcamError("bad filter_id in set_filter")

        time.sleep(2)

        return

    # ***************************************************************************
    # pressure
    # ***************************************************************************
    def get_pressure(self, pressure_id=0):
        """
        Read an instrument pressure.
        """

        return self.pressure.read_pressure(pressure_id)

    # ************************************************************
    # Electrometer
    # ************************************************************
    def get_current(
        self,
        shutter_state: int = 1,
        current_id: int = 0,
    ) -> float:
        """
        Read Electrometer diode current in Amps.
        current_id = 0 is the sphere (Reference) diode.
        current_id = 1 is the calibrated diode or DUT.
        shutter_state is 1 to open shutter during read.
        """

        shutter_state = int(shutter_state)

        self.set_comps("S")
        time.sleep(0.5)
        if shutter_state:
            azcam.db.tools["controller"].set_shutter(1)
            self.comps_on()
            time.sleep(2)
        else:
            self.set_shutter(0)

        current_id = int(current_id)
        if current_id == 0:
            cmd = "instrument.get_refdiode_current"
        elif current_id == 1:
            cmd = "instrument.get_dut_current"
        else:
            raise azcam.AzcamError("bad current_id value")
        reply = self.server_command(cmd)
        reply = float(reply[1])

        if shutter_state:
            azcam.db.tools["controller"].set_shutter(0)
            self.comps_off()

        return reply

    # ******************************************************************************
    # Newport power meter
    # ******************************************************************************
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

    # ******************************************************************************
    # sensor current - Keithley 6512 meter
    # ******************************************************************************
    def init_dut_meter(self):
        """
        Initialize sensor current meter.
        Keithley 6512 electrometer - DUT - USB GPIB
        """

        # init 6512
        self.k6512.defaults()

        return

    def get_dut_current(
        self,
    ):
        """
        Get Device Under Test current in Amps.
        """

        reply = self.k6512.get_val("current")
        current = float(reply)

        return current

    # ******************************************************************************
    # reference diode current - Keithley 6514 meter
    # ******************************************************************************
    def init_refdiode_meter(self):
        """
        Initialize reference diode current meter.
        Keithley 6514 electrometer - integrating sphere reference diode
        """

        self.k6514.read_termination = "\r"
        self.k6514.timeout = 5000

        # init 6514
        # print(self.k6514.query("*IDN?"))
        s = "*RST"
        self.k6514.write(s)
        s = "SENS:FUNC 'CURR'"
        self.k6514.write(s)
        s = "SENS:CURR:RANG:AUTO ON"
        self.k6514.write(s)
        s = "SENS:ZCCH OFF"
        self.k6514.write(s)

        return

    def get_refdiode_current(self):
        """
        Get reference diode current in Amps.
        """

        for _ in range(3):
            current = []
            try:
                reply = self.k6514.query("READ?")
                current.append(float(reply.split(",")[0]))
            except Exception as e:
                azcam.log(f"ERROR reading refdiode electrometer - {e}")
            time.sleep(0.1)
        current = sum(current) / len(current)

        return current

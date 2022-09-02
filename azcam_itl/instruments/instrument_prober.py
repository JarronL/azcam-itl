import azcam
from azcam.tools.instrument import Instrument

from azcam_itl.instruments.electroglas_4090 import EGProber
from azcam_itl.instruments.keithley_230 import VoltageSource
from azcam_itl.instruments.keithley_2000 import Multimeter
from azcam_itl.instruments.keithley_7002 import Switcher
from azcam_itl.instruments.shutter_control_usb import ShutterControllerClassUSB


class InstrumentProber(Instrument):
    """
    The Instrument interface to the ITL Prober system (2016).
    """

    def __init__(self, tool_id="instrument", description="prober instrument"):

        super().__init__(tool_id, description)

        # shutter controller, USB relay on "prober" PC
        # self.shutter = ShutterControllerClassUSB("COM4")

        # VISA communication to prober
        self.prober = EGProber("GPIB0::1::INSTR")

        # VISA communication to voltage source
        # self.voltage = VoltageSource("GPIB0::13::INSTR")

        # VISA communication to multimeter
        # self.multimeter = Multimeter("GPIB0::16::INSTR")

        # VISA communication to switcher
        # self.switcher = Switcher("GPIB0::7::INSTR")

        self.define_keywords()

    def initialize(self):
        """
        Initialize hardware.
        """

        self.initialized = 0

        if not self.enabled:
            azcam.AzcamWarning(f"{self.description} is not enabled")
            return

        # azcam.log("Initializing multimeter communications")
        # self.multimeter.initialize()

        # azcam.log("Initializing voltage source communications")
        # self.voltage.initialize()

        # azcam.log("Initializing switcher communications")
        # self.switcher.initialize()

        azcam.log("Initializing prober communications")
        self.prober.initialize()

        self.active_comps=["shutter"]

        self.initialized = 1

        return

    # ***************************************************************************
    # Comparisons - shutter controller
    # ***************************************************************************
    def get_all_comps(self):

        comps = ["LED", "Fe55"]

        return comps

    def get_comps(self):

        comps = list(self.active_comps)

        return comps

    def set_comps(self, comp_names=[""]):
        if type(comp_names) == list:
            lamp = comp_names[0].strip("'\"")  # strip quotes
        else:
            lamp = comp_names.strip("'\"")

        if lamp.lower() == "fe-55" or lamp.lower() == "fe55":
            self.active_comps[0] = "fe55"
            function = "F"
        elif lamp.lower() == "projector":
            self.active_comps[0] = "shutter"
            function = "S"
        elif lamp.lower() == "led":
            self.active_comps[0] = "led"
            function = "L"
        else:
            self.active_comps[0] = "shutter"
            function = "S"

        #self.shutter.set_state(function)

        return

    def comps_on(self):
        """
        Turn Comps on.
        During an exposure don't call this as the shutter controls the Comps.
        Issues the 'Activate' command to the insturment server.
        """

        return

    def comps_off(self):
        """
        Turn Comps off.
        During an exposure don't call this as the shutter controls the Comps.
        Issues the 'Deactivate' command to the insturment server.
        """

        return

    def set_shutter(self, state):
        """
        Opens the instrument shutter.
        """

        self.shutter.set_state("S")
        if state:
            self.shutter.open_shutter()
        else:
            self.shutter.close_shutter()

        return

    def set_fe55(self, state):
        """
        Moves Fe-55 source in our out.
        """

        self.shutter.set_state("F")
        if state:
            self.shutter.open_shutter()
        else:
            self.shutter.close_shutter()

        return

    # ************************************************************
    # Prober
    # ************************************************************
    def get_temperature(self):
        """
        Read prober chuck temperature.
        """

        temp = 999.99

        reply = self.prober.command("?A0")

        if reply.startswith("AT"):
            temp = float(reply[2:])

        return temp

    # ************************************************************
    # Electrometer
    # ************************************************************
    def get_current(self, current_id=0):
        """
        Read Electrometer diode current in Amps.
        """

        reply = self.multimeter.get_current()

        return reply

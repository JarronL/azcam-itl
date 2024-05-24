import time
import socket

import pyvisa

import azcam
import azcam.exceptions
from azcam.tools.instrument import Instrument
from azcam_itl.instruments import pressure_vgc501
from azcam_itl.instruments import pressure_mks900
from azcam_itl.instruments import webpower
from azcam_itl.instruments.pollux import PolluxCtrl

"""
COM3 is Arduino serial port
"""


class InstrumentEB(Instrument):
    """
    The instrument class for the ITL Electronbench bench.
    """

    def __init__(self, tool_id="instrument", description="Electronbench instrument"):
        super().__init__(tool_id, description)

        self.shutter_strobe = 1

        self.define_keywords()

        self.wavelength = ""  # wavelengths are LED strings like "green"
        self.valid_wavelengths = ["violet", "green", "orange", "red", "IR", "UV"]
        self.wavelengthLeds = {
            "violet": 2,
            "green": 3,
            "orange": 4,
            "red": 5,
            "ir": 6,
            "uv": 7,
        }

        # current state
        self.led_state = "FFFFFFFF"  # start with all Arduino pins off

        self.led_codes = {
            "shutter": "FFFFFFFF",
            "fe55": "NFFFFFFF",
            "violet": "FFNFFFFF",
            "green": "FFFNFFFF",
            "orange": "FFFFNFFF",
            "red": "FFFFFNFF",
            "ir": "FFFFFFNF",
            "uv": "FFFFFFFN",
        }

        self.led_pins = {
            0: "fe55",
            1: "input",
            2: "violet",
            3: "green",
            4: "orange",
            5: "red",
            6: "ir",
            7: "uv",
        }

        self.led_color_places = {
            "fe55": 0,
            "input": 1,
            "violet": 2,
            "green": 3,
            "orange": 4,
            "red": 5,
            "ir": 6,
            "uv": 7,
        }

        # focus stage control
        self.pollux = PolluxCtrl()

        # filter wheel
        self.filters = FilterWheelEB()

        # self.pressure = pressure_mks900.PressureController("COM4")

        # initialization - may fail if turned off
        self.initialized = False

    def initialize(self):
        """
        Initialize the instrument interface.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.exceptions.warning(f"{self.description} is not enabled")
            return

        # init arduino for LEDs and shutter control
        self.initialize_arduino()

        # init focus stages
        self.pollux.initialize()

        # init filter wheel
        self.filters.initialize()

        self.initialized = True

        azcam.log("Instrument initialized")

        self.initialized = 1

        return

    # ***************************************************************************
    # Header/Keywords
    # ***************************************************************************
    def define_keywords(self):
        """
        Defines and resets instrument keywords.
        """

        self.set_keyword("WAVLNGTH", "", "Wavelength of LEDs", "str")
        self.set_keyword("FOCUSVAL", 0, "Focus position", "float")
        self.set_keyword("FILTER", "", "Filter position", "str")

        return

    def get_keyword(self, keyword):
        """
        Read an instrument keyword value.
        This command will read hardware to obtain the keyword value.
        """

        if keyword == "WAVLNGTH":
            reply = self.get_wavelength()
        elif keyword == "FOCUSVAL":
            reply = self.get_focus()
        elif keyword == "FILTER":
            reply = self.get_filter()
        else:
            raise azcam.exceptions.AzcamError("invalid keyword")

        # store value in Header
        self.set_keyword(keyword, reply)

        reply, t = self.header.convert_type(reply, self.header.typestrings[keyword])

        return [reply, self.header.comments[keyword], t]

    # ***************************************************************************
    # Arduino for LEDs and Fe55 control
    # ***************************************************************************

    def initialize_arduino(self):
        """
        Initialze arduino for LED and shutter control.
        """

        # set Arduino pins OFF for LED and Fe55 control
        self.set_leds("FFFFFFFF")

        return

    def get_all_comps(self):
        """
        Return list of valid LED names.
        """

        complist = list(self.led_codes.keys())

        return complist

    def get_comps(self):
        """
        Return list of the active comp names.
        """

        complist = []
        # ledlist = list(self.led_state)
        for i in range(8):
            if self.led_state[i] == "N":
                complist.append(self.led_pins[i])

        return complist

    def set_comps(self, comp_names=["shutter"]):
        if type(comp_names) == list:
            lamps = " ".join(comp_names)
        else:
            lamps = comp_names

        if lamps == "shutter":
            ledstring = "FFFFFFFF"
        else:
            ledstring = self.make_ledstring(lamps)

        self.set_pin_state(ledstring, "S")
        self.led_state = ledstring

        return

    def comps_on(self):
        """
        Turn active comparisons on.
        """

        self.set_pin_state(self.led_state, "C")

        return

    def comps_off(self):
        """
        Turn active comparisons off.
        """

        self.set_pin_state("FFFFFFFF", "C")

        return

    def set_led(self, color_code, state):
        """
        Turn one LEDs on or off immediately.
        LEDs color_codes are:
          fe55
          not used (shutter input)
          violet
          green
          orange
          red
          IR
          UV
        """

        if state == 1:
            state1 = "N"
        elif state == 0:
            state1 = "F"

        ledstring = []
        for i in range(8):
            if color_code == self.led_pins[i]:
                ledstring.append(state1)
            else:
                ledstring.append(self.led_state[i])
        ledstring = "".join(ledstring)

        self.set_pin_state(ledstring, "C")
        self.led_state = ledstring

        return

    def set_leds(self, ledstring):
        """
        Turn on or off multiple LEDs using the ledstring code like "FFNNFFFF".
        Use 'N" for ON and 'F' for OFF.
        Sends command in Control mode.

        """

        self.set_pin_state(ledstring, "C")
        self.led_state = ledstring

        return

    def set_pin_state(self, state="FFFFFFFF", mode="C"):
        """
        Set state of all pins using the ledstring code like "FFNNFFFF".
        Use 'N" for ON and 'F' for OFF.
        mode is 'C' for Control or 'S' for Shutter.
        """

        output = mode + state

        # set up socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Declare Arduino address and port
        arduino_address = ("10.131.0.9", 80)

        # send string over socket
        client_socket.connect(arduino_address)
        client_socket.send(output.encode())
        client_socket.close()

        return

    def get_leds(self):
        """
        Return current LED state.
        """

        ledlist = []

        for i in range(2, 8):
            if self.led_state[i] == "N":
                ledlist.append(self.led_pins[i])

        return ledlist

    def set_fe55(self, state=0):
        """
        Activate Fe55 (state=1) or deactivate (state=0).
        """

        if state:
            newstate = "N"
        else:
            newstate = "F"

        for i in range(1, 8):
            newstate += self.led_state[i]

        self.led_state = newstate
        cmd = newstate

        self.set_pin_state(cmd, "C")

        return

    def make_ledstring(self, code):
        """
        Make ledstring from a string or list of colors.
        code example: ['red', IR'] or 'red IR'.
        """

        if type(code) == str:
            codes = code.split(" ")
        else:
            codes = code

        ledstring = 8 * ["F"]
        for code1 in codes:
            index = self.led_color_places[code1]
            ledstring[index] = "N"
        ledstring = "".join(ledstring)

        return ledstring

    def get_wavelengths(self, wavelength_id=0):
        """
        Returns a list of valid led colors.
        """

        return list(self.led_codes.keys())[1:]

    def get_wavelength(self, wavelength_id=0):
        """
        Return current LED wavelength.
        """

        leds = self.get_leds()

        if len(leds) == 0:
            return "dark"

        return leds[0]

    def set_wavelength(self, wavelength, wavelength_id=0):
        """
        Set current LED wavelength.
        """

        self.set_leds(self.led_codes[wavelength])

        return

    def set_shutter_mode(self, code):
        """
        Set states for shutter mode.
        This state is activated when shutter signal goes high,
        code is like "green" or "fe55" or "shutter" or "green red".
        """

        ledstring = self.make_ledstring(code)

        self.set_pin_state(ledstring, "S")
        self.led_state = ledstring

        return

    # ***************************************************************************
    # focus control with Pollux stages (EB at ARB)
    # Axes are (1,2,3) not (0,1,2)
    # Axis 1 is z-axis focus, positive toward camera
    # Axis 2 is right-left, positive toward left
    # Axis 3 is up-down, positive down
    # ***************************************************************************

    def initialize_focus(self):
        """
        Initialize focus stage communications.
        """

        self.pollux.initialize()

        return

    def home_focus(self, AxisID):
        """
        Home an axis to its absolute home reference.
        """

        if AxisID not in self.pollux.valid_axes:
            raise azcam.exceptions.AzcamError(f"focus axis {AxisID} not supported")

        self.pollux.go_home(AxisID)

        return

    def get_focus(self, AxisID=1, wait=1):
        if AxisID not in self.pollux.valid_axes:
            raise azcam.exceptions.AzcamError(f"focus axis {AxisID} not supported")

        reply = self.pollux.get_pos(AxisID, wait)

        position = reply[1]
        position = float(position)

        return position

    def set_focus(self, FocusPosition, AxisID=1, focus_type="absolute"):
        if AxisID not in self.pollux.valid_axes:
            raise azcam.exceptions.AzcamError(f"focus axis {AxisID} not supported")

        FocusPosition = float(FocusPosition)
        focus_id = int(AxisID)

        if focus_type == "absolute":
            self._set_focus(FocusPosition, focus_id)
        elif focus_type == "step":
            self._step_focus(FocusPosition, focus_id)
        else:
            raise azcam.exceptions.AzcamError("invalid focus_type")

        return

    def _set_focus(self, Position, AxisID=1):
        if AxisID not in self.pollux.valid_axes:
            raise azcam.exceptions.AzcamError(f"focus axis {AxisID} not supported")

        Position = float(Position)
        self.pollux.move_absolute(AxisID, Position)

        return

    def _step_focus(self, PositionChange, AxisID=1):
        if AxisID not in self.pollux.valid_axes:
            raise azcam.exceptions.AzcamError(f"focus axis {AxisID} not supported")

        PositionChange = float(PositionChange)
        self.pollux.move_relative(AxisID, PositionChange)

        return

    def calibrate_focus(self, AxisID=1):
        """
        Run calibration sequence for axis.
        """

        print("Moving to end of travel")
        self.pollux.calibrate(AxisID)
        self.pollux.get_motion(AxisID, 1)  # wait for motion to stop

        print("Measuring range of travel")
        self.pollux.range_measure(AxisID)
        self.pollux.get_motion(AxisID, 1)  # wait for motion to stop

        reply = self.pollux.get_limits(AxisID)
        print(reply)
        limits = [float(x) for x in reply[1].split()]
        print(f"Limits: {limits[0]} - {limits[1]}")
        midrange = (limits[1] - limits[0]) / 2.0
        self.set_focus(midrange, AxisID)

        self.pollux.set_home(AxisID)
        reply = self.get_focus(AxisID)
        print("Homed position in center:", reply)

        return

    def focus_command(self, Command, GetReply=0):
        """
        Send a command to focus device.
        """

        reply = self.pollux.send_cmd(Command, GetReply)

        return reply

    # ***************************************************************************
    # filters
    # ***************************************************************************
    """
    RST -> FILT
    NEXT
    PREV
    FILT?
    FILTx moves wheel
    USB2 works to control, but pyvisa might be best
    """

    def initialize_filters(self):
        """
        Initialize filters.
        """

        reply = self.filters.initialize()

        return reply

    def get_filters(self, filter_id=0):
        """
        Return list of valid filter names.
        """

        reply = self.filters.get_filters()

        return reply

    def get_filter(self, filter_id=0):
        """
        Return the filter in the beam.
        filter_id is the filter mechanism ID.
        """

        reply = self.filters.get_filter()

        return reply

    def set_filter(self, filter_name, filter_id=0):
        """
        Set the filter in the beam.
        filter_name is a string containing the filter name to set.
        filter_id is the filter mechanism ID.
        """

        self.filters.set_filter(filter_name)

        return

    # ***************************************************************************
    # pressure
    # ***************************************************************************
    def get_pressure(self, pressure_id=0):
        """
        Read an instrument pressure.
        """

        return self.pressure.read_pressure(pressure_id)


class FilterWheelEB(object):
    """
    Server for instrument control on ITL detchar ElectronBench.

    # filter control with Newport USB filter wheel
    RST -> FILT
    NEXT
    PREV
    FILT?
    FILTx moves wheel
    USB2 works to control, but pyvisa might be best
    """

    def __init__(self):
        self.mock = 0
        self.verbose = 0

        self.filter_wavelengths = {
            "art1": 1,  # clear with opaque artwork
            "art2": 2,  # opaque with clear artwork
            "clear1": 3,
            "clear2": 4,
            "clear3": 5,
            "dark": 6,
        }

        self.filter_names = {
            "FILT1": "art1",
            "FILT2": "art2",
            "FILT3": "clear1",
            "FILT4": "clear2",
            "FILT5": "clear3",
            "FILT6": "dark",
        }

        # filter wheel
        if not self.mock:
            self.rm = pyvisa.ResourceManager()

        # initialization - may fail if turned off
        self.initialized = False

    def initialize(self):
        """
        Initialize hardware.
        """

        # filter wheel
        if not self.mock:
            self.fw = self.rm.open_resource("USB0")  # renamed filter wheel from NI Max
            # self.fw = self.rm.open_resource("COM3")

        reply = self.fw.query("RST")

        self.initialized = True

        azcam.log("Filter wheel initialized")

        return

    def get_filter(self, filter_id=0):
        """
        Return the filter in the beam.
        FilterID is the filter mechanism ID.
        """

        filt = self.fw.query("FILT?")  # like FILT4
        filter_name = self.filter_names[filt]

        return filter_name

    def set_filter(self, filter_name, filter_id=0):
        """
        Set the filter in the beam.
        FilterID is the filter mechanism ID.
        """

        pos = self.filter_wavelengths[filter_name]
        self.fw.query(f"FILT{pos}")
        for _ in range(5):  # wait for motion
            current = self.fw.query(f"FILT?")
            if current == filter_name:
                break
            time.sleep(0.5)

        return

    def get_filters(self, filter_id=0):
        """
        Return list of valid filter names.
        """

        return list(self.filter_wavelengths.keys())


class InstrumentEBXXX(Instrument):
    """
    The Instrument interface to the ITL Electron Bench test system.
    """

    def __init__(self, tool_id="instrument", description="EB instrument"):
        super().__init__(tool_id, description)

        self.shutter_strobe = 1

        # EB web power switch instance
        self.power = webpower.WebPowerClass()
        self.power.service_name = "powerswitcheb"
        self.power.username = "lab"
        self.power.hostname = "10.131.0.6"

        # EB2 web power switch instance
        self.power2 = webpower.WebPowerClass()
        self.power2.service_name = "powerswitcheb2"
        self.power2.username = "lab"
        self.power2.hostname = "10.131.0.19"

        self.pressure_ids = [0, 1]  # [0, 1, 2, 4]
        self.pressure0 = pressure_mks900.PressureController("COM3")  # EB MKS controller
        self.pressure1 = pressure_vgc501.PressureController(
            "COM4"
        )  # EB ethernet mapped Pfeiffer
        self.pressure2 = pressure_vgc501.PressureController(
            "COM11"
        )  # EB ethernet mapped Agilent
        self.wavelength = ""  # wavelengths are LED strings like "green"
        self.valid_wavelengths = ["UV", "violet", "green", "orange", "red", "IR"]
        self.wavelengthLeds = {
            "UV": 7,
            "violet": 2,
            "green": 3,
            "orange": 4,
            "red": 5,
            "IR": 6,
        }

        # current state
        self.led_state = "FFFFFFFF"  # start with all Arduino pins off

        self.led_codes = {
            "shutter": "FFFFFFFF",
            "fe55": "NFFFFFFF",
            "violet": "FFNFFFFF",
            "green": "FFFNFFFF",
            "orange": "FFFFNFFF",
            "red": "FFFFFNFF",
            "IR": "FFFFFFNF",
            "UV": "FFFFFFFN",
        }

        self.led_pins = {
            0: "fe55",
            1: "input",
            2: "violet",
            3: "green",
            4: "orange",
            5: "red",
            6: "IR",
            7: "UV",
        }

        self.led_color_places = {
            "fe55": 0,
            "input": 1,
            "violet": 2,
            "green": 3,
            "orange": 4,
            "red": 5,
            "IR": 6,
            "UV": 7,
        }

        # create header
        self.define_keywords()

    def get_pressure(self, pressure_id=0):
        """
        Read an instrument pressure.
        Args:
            pressure_id: 0 is MKS, 1 is Pfeiffer
        Returns:
            pressure: -999 for bad pressure
        """

        try:
            if pressure_id == 0:
                reply = self.pressure0.read_pressure(1)  # temp 2 is for MKS CC

            elif pressure_id == 1:
                self.pressure1.read_pressure()
                reply = self.pressure1.read_pressure()

            elif pressure_id == 2:
                self.pressure2.read_pressure()
                reply = self.pressure2.read_pressure()

            else:
                reply = -999

        except Exception:
            reply = -1

        return reply


# start
if __name__ == "__main__":
    ebserver = InstrumentEB()

    # debug here
    if 1:
        ebserver.pollux.calibrate(3)  # sets axis to zero at end limit

        # ebserver.set_focus(50,1)
        # ebserver.set_focus(50,2)
        # ebserver.set_focus(50,3)

        # ebserver.set_led("red",1)
        # ebserver.set_fe55(0)
        # ebserver.set_leds('FFNNNNNN')
        # ebserver.set_leds('FFFFFFFF')

        # reply = ebserver.get_filters()
        # print(reply)
        # reply = ebserver.get_filter()
        # print(reply)
        # ebserver.set_filter('dark')
        # reply = ebserver.get_filter()
        # print(reply)

        pass

    # fun loop
    if 0:
        print("running random LEDs test")
        import random

        while 1:
            for i in range(2, 8):
                state = random.randint(0, 1)
                ebserver.set_led(ebserver.led_pins[i], state)
                time.sleep(random.random() * 0.1)


# ***************************************************************************
# filter control with Newport USB filter wheel
# ***************************************************************************
"""
RST -> FILT
NEXT
PREV
FILT?
FILTx moves wheel
USB2 works to control, but pyvisa might be best
"""

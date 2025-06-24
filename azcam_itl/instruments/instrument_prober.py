import time
import socket

import pyvisa

import azcam
import azcam.exceptions
from azcam.tools.instrument import Instrument
from azcam_itl.instruments import webpower


class InstrumentProber(Instrument):
    """
    The instrument class for the ITL Electroglas 4090 prober.
    """

    def __init__(self, tool_id="instrument", description="prober instrument"):
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

        # initialization - may fail if turned off
        self.is_initialized = False

    def initialize(self):
        """
        Initialize the instrument interface.
        """

        if self.is_initialized:
            return

        if not self.is_enabled:
            azcam.exceptions.warning(f"{self.description} is not enabled")
            return

        # init arduino for LEDs and shutter control
        # self.initialize_arduino()

        self.is_initialized = True

        azcam.log("Instrument initialized")

        self.is_initialized = 1

        return

    # ***************************************************************************
    # Header/Keywords
    # ***************************************************************************
    def define_keywords(self):
        """
        Defines and resets instrument keywords.
        """

        self.set_keyword("WAVLNGTH", "", "Wavelength of LEDs", "str")
        self.set_keyword("FILTER", "", "Filter position", "str")

        return

    def get_keyword(self, keyword):
        """
        Read an instrument keyword value.
        This command will read hardware to obtain the keyword value.
        """

        if keyword == "WAVLNGTH":
            reply = self.get_wavelength()
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
        # arduino_address = ("10.131.0.9", 80)
        arduino_address = ("", 80)

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

    def get_wavelengths(self, *args, **kwargs):#, wavelength_id=0):
        """
        Returns a list of valid led colors.
        """

        return list(self.led_codes.keys())[1:]

    def get_wavelength(self, *args, **kwargs):#, wavelength_id=0):
        """
        Return current LED wavelength.
        """

        leds = self.get_leds()

        if len(leds) == 0:
            return "dark"

        return leds[0]

    def set_wavelength(self, wavelength, *args, **kwargs):#, wavelength_id=0):
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

    def get_filters(self, *args, **kwargs):#, filter_id=0):
        """
        Return list of valid filter names.
        """

        reply = self.filters.get_filters()

        return reply

    def get_filter(self, *args, **kwargs):#, filter_id=0):
        """
        Return the filter in the beam.
        filter_id is the filter mechanism ID.
        """

        reply = self.filters.get_filter()

        return reply

    def set_filter(self, filter_name, *args, **kwargs):#, filter_id=0):
        """
        Set the filter in the beam.
        filter_name is a string containing the filter name to set.
        filter_id is the filter mechanism ID.
        """

        self.filters.set_filter(filter_name)

        return


class FilterWheelProber(object):
    """
    Example for a filter wheel like on ITL detchar ElectronBench.

    # filter control with Newport USB filter wheel
    RST -> FILT
    NEXT
    PREV
    FILT?
    FILTx moves wheel
    USB2 works to control, but pyvisa might be best
    """

    def __init__(self):
        self.mock = 1
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
        self.is_initialized = False

    def initialize(self):
        """
        Initialize hardware.
        """

        # filter wheel
        if not self.mock:
            self.fw = self.rm.open_resource("USB0")  # renamed filter wheel from NI Max
            # self.fw = self.rm.open_resource("COM3")

        reply = self.fw.query("RST")

        self.is_initialized = True

        azcam.log("Filter wheel initialized")

        return

    def get_filter(self):#, filter_id=0):
        """
        Return the filter in the beam.
        FilterID is the filter mechanism ID.
        """

        filt = self.fw.query("FILT?")  # like FILT4
        filter_name = self.filter_names[filt]

        return filter_name

    def set_filter(self, filter_name):#, filter_id=0):
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

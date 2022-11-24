"""
Instrument EBInstrumentServer for ITL Flex bench.

Authors: Alanna Zubler & Michael Lesser
"""

import shlex
import socket
import time

import pyvisa  # for filter wheel

import azcam
from azcam.tools.instrument import Instrument
from azcam_itl.instruments import pressure_mks900
from azcam_itl.instruments.pollux import PolluxCtrl  # SMC-Pollux stages


class InstrumentFlex(Instrument):
    """
    The instrument class for the ITL flex bench.
    """

    def __init__(self, tool_id="instrument", description="Flex instrument"):

        super().__init__(tool_id, description)

        self.shutter_strobe = 1

        self.define_keywords()

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

        # focus stage control
        self.pollux = PolluxCtrl()

        # filters server running on conserver5
        self.filters = azcam.sockets.SocketInterface("conserver5", 2406)
        # self.filters = azcam.sockets.SocketInterface("localhost", 2406)
        self.filters.timeout = 10.0

        self.pressure = pressure_mks900.PressureController("COM4")

        # initialization - may fail if turned off
        self.initialized = False

    def initialize(self):
        """
        Initialize the instrument interface.
        """

        if self.initialized:
            return

        if not self.enabled:
            azcam.AzcamWarning(f"{self.description} is not enabled")
            return

        self.initialize_filters()

        self.initialize_arduino()

        # init focus stages
        self.pollux.initialize()

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
        self.set_keyword("FOCUSVAL", "", "Focus position", "float")
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
            raise azcam.AzcamError("invalid keyword")

        # store value in Header
        self.set_keyword(keyword, reply)

        reply, t = self.header.convert_type(reply, self.header.typestrings[keyword])

        return [reply, self.header.comments[keyword], t]

    def command_parser(self, command_string):
        """
        Custom command parser for socket server.
        Executes command_string and returns data component of response (only) to cmdserver.
        Command and arguments are space delimited.
        """

        # self instance is cmdserver not ebserver
        ebserver = azcam.db.ebserver

        command_string = command_string.strip()
        tokens = shlex.split(command_string)
        command = tokens[0]
        args = tokens[1:]

        VERBOSE = 1

        if VERBOSE:
            print(f"Rec: {command_string}")

        # parse incoming string commands
        if command == "initialize":
            reply = ebserver.initialize()
        elif command == "help":
            replylist = [
                "Supported commands are:",
                "initialize",
                "get_all_comps",
                "set_comps",
                "set_led",
                "set_leds",
                "set_shutter_mode",
                "set_fe55",
                "set_wavelength",
                "get_wavelength",
                "home_focus",
                "get_focus",
                "set_focus",
                "step_focus",
                "get_filters",
                "set_filter",
                "",
            ]
            reply = "\r\n".join(replylist)

        elif command == "get_all_comps":
            replylist = ebserver.get_all_comps()
            reply = " ".join(replylist)
        elif command == "get_comps":
            replylist = ebserver.get_comps()
            reply = " ".join(replylist)
        elif command == "set_comps":
            if len(args) > 1:
                comps = " ".join(args)
            else:
                comps = args[0]
            reply = ebserver.set_comps(comps)
        elif command == "comps_on":
            reply = ebserver.comps_on()
        elif command == "comps_off":
            reply = ebserver.comps_off()

        elif command == "set_led":
            reply = ebserver.set_led(int(args[0]), int(args[1]))
        elif command == "set_leds":
            reply = ebserver.set_led(args[0])
        elif command == "set_shutter_mode":
            reply = ebserver.set_shutter_mode(args[0])
        elif command == "set_fe55":
            reply = ebserver.set_fe55(int(args[0]))
        elif command == "set_wavelength":
            reply = ebserver.set_wavelength(args[0])
        elif command == "get_wavelength":
            reply = ebserver.get_wavelength()

        elif command == "home_focus":
            reply = ebserver.home_focus(int(args[0]))
        elif command == "get_focus":
            reply = ebserver.get_focus(int(args[0]), int(args[1]))
            reply = str(reply)
        elif command == "set_focus":
            reply = ebserver.set_focus(float(args[0]), int(args[1]))
        elif command == "step_focus":
            reply = ebserver.step_focus(float(args[0]), int(args[1]))

        elif command == "get_filters":
            replylist = ebserver.get_filters()
            reply = " ".join(replylist)
        elif command == "get_filter":
            reply = ebserver.get_filter()
        elif command == "set_filter":
            reply = ebserver.set_filter(args[0])

        else:
            reply = "Command not yet supported remotely"

        if VERBOSE:
            if reply is None:
                print(f"===> None")
                reply = "OK"
            else:
                print(f"===> {reply}")

        return reply

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
        arduino_address = ("10.0.0.37", 80)

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
    # Focus
    # ***************************************************************************

    # ***************************************************************************
    # focus control with Pollux stages
    # Axes are (1,2,3) not (0,1,2)
    # Axis 1 is z-axis focus, negative away from dewar
    # ***************************************************************************

    def home_focus(self, Axis):
        """
        Home an axis.
        """

        self.pollux.home(Axis)

        return

    def get_focus(self, AxisID=1, wait=1):

        reply = self.pollux.get_pos(AxisID, wait)

        position = reply[1]
        position = float(position)

        return position

    def set_focus(self, FocusPosition, focus_id=1, focus_type="absolute"):

        FocusPosition = float(FocusPosition)
        focus_id = int(focus_id)

        if focus_type == "absolute":
            self._set_focus(FocusPosition, focus_id)
        elif focus_type == "step":
            self._step_focus(FocusPosition, focus_id)
        else:
            raise azcam.AzcamError("invalid focus_type")

        return

    def _set_focus(self, Position, AxisID=1):

        Position = float(Position)
        self.pollux.MoveAbsolute(AxisID, Position)

        return

    def _step_focus(self, PositionChange, AxisID=1):

        PositionChange = float(PositionChange)
        self.pollux.move_relative(AxisID, PositionChange)

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

        reply = self.filters.command("filters.initialize")

        return reply

    def get_filters(self, filter_id=0):
        """
        Return list of valid filter names.
        """

        reply = self.filters.command("filters.get_filters")

        return reply[1:]

    def get_filter(self, filter_id=0):
        """
        Return the filter in the beam.
        filter_id is the filter mechanism ID.
        """

        reply = self.filters.command(f"filters.get_filter {filter_id}")

        return reply

    def set_filter(self, filter_name, filter_id=0):
        """
        Set the filter in the beam.
        filter_name is a string containing the filter name to set.
        filter_id is the filter mechanism ID.
        """

        self.filters.command(f"filters.set_filter {filter_name} {filter_id}")

        return

    # ***************************************************************************
    # pressure
    # ***************************************************************************
    def get_pressure(self, pressure_id=0):
        """
        Read an instrument pressure.
        """

        return self.pressure.read_pressure(pressure_id)


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

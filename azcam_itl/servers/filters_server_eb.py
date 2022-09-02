"""
Filter wheel server application for ITL ElectronBench.
"""

import sys
import time

import azcam
import azcam.server
import pyvisa
from azcam.tools.cmdserver import CommandServer


class ElectronBenchFiltersServer(object):
    """
    Server for ITL Electronbench filter wheel.
    """

    def __init__(self, port):

        # logging
        azcam.db.logger.start_logging(logtype="1")
        azcam.log(f"Configuring filters for ITL Electronbench")

        # create filters object and tool
        filters = FilterWheelEB()
        azcam.db.tools["filters"] = filters

        # command server
        cmdserver = CommandServer()
        cmdserver.port = port
        cmdserver.logcommands = 1
        azcam.log(f"Starting cmdserver - listening on port {cmdserver.port}")
        cmdserver.start()


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
        self.verbose = 1

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

        reply = self.fw.query("RST")
        print(reply)

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


# start server
try:
    i = sys.argv.index("-port")
    port = int(sys.argv[i + 1])
except ValueError:
    port = 2406

ElectronBenchFiltersServer(port)

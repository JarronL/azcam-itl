"""
Setup method for ITL azcamserver.

Usage example:
  python -i -m azcam_itl.server -- -system LVM -instrument QB -tempcon EB
    or -- -configure /data/LVM/config_LVM.py
    or -- -datafolder path_to_datafolder
"""

import importlib
import os
import sys
from runpy import run_path

import azcam
import azcam.utils
from azcam.logger import check_for_remote_logger
from azcam.scripts.scripts import loadscripts

import azcam.server
import azcam.shortcuts
from azcam.cmdserver import CommandServer
from azcam.tools.tempcon_cryocon24 import TempConCryoCon24
from azcam.tools.tempcon import TempCon
from azcam.tools.ds9display import Ds9Display

from azcam.webtools.webserver import WebServer
from azcam.webtools.status.status import Status
from azcam.webtools.exptool.exptool import Exptool

from azcam.tools.instrument import Instrument
from azcam_itl.instruments.instrument_qb import InstrumentQB
from azcam_itl.instruments.instrument_eb import InstrumentEB
from azcam_itl.instruments.instrument_arduino import InstrumentArduino

from azcam_itl.local_web import LocalWebServer

from azcam.tools.ascom.tempcon_ascom import TempConASCOM
import azcam_itl.shortcuts_itl


def setup():

    # parse command line arguments
    try:
        i = sys.argv.index("-system")
        systemname = sys.argv[i + 1]
    except ValueError:
        systemname = "menu"
    try:
        i = sys.argv.index("-datafolder")
        datafolder = sys.argv[i + 1]
    except ValueError:
        datafolder = None
    try:
        i = sys.argv.index("-configure")
        configuration = sys.argv[i + 1]
    except ValueError:
        configuration = None
    try:
        i = sys.argv.index("-cmdport")
        cmdport = int(sys.argv[i + 1])
    except ValueError:
        cmdport = 2402
    try:
        i = sys.argv.index("-instrument")
        instflag = sys.argv[i + 1]
    except ValueError:
        instflag = None
    try:
        i = sys.argv.index("-tempcon")
        tempflag = sys.argv[i + 1]
    except ValueError:
        tempflag = None

    # optional config script
    if configuration is not None:
        run_path(configuration)
        systemname = azcam.db.systemname  # may overwrite systemname

    # optionally select system with menu
    menu_options = {
        "DESI": "DESI",
        "QHY174 CMOS camera": "QHY174",
        # "LVM": "LVM",
        "ZWO ASI6200MM CMOS camera": "ASI6200MM",
        "ZWO ASI294MM CMOS camera": "ASI294MM",
        "Moravian IMX411 CMOS camera": "IMX411",
        # "OSU4k": "OSU4k",
        # "ITL6k": "ITL6k",
        "90prime4k": "90prime4k",
        # "Magellan Guider": "magguider",
        # "SO Guider": "soguider",
        "None": "NoSystem",
    }

    if systemname == "menu":
        systemname = azcam.utils.show_menu(menu_options)
    else:
        systemname = systemname
    azcam.db.systemname = systemname
    azcam.db.systemfolder = os.path.dirname(__file__)
    azcam.db.systemfolder = azcam.utils.fix_path(azcam.db.systemfolder)
    azcam.db.datafolder = azcam.utils.get_datafolder(datafolder)

    azcam.db.servermode = azcam.db.systemname
    azcam.db.verbosity = 2

    # logging
    logfile = os.path.join(azcam.db.datafolder, "logs", "server.log")
    if check_for_remote_logger():
        azcam.db.logger.start_logging(logtype="23", logfile=logfile)
    else:
        azcam.db.logger.start_logging(logtype="13", logfile=logfile)

    azcam.log(f"Configuring {azcam.db.systemname}")

    # define command server
    cmdserver = CommandServer()
    cmdserver.port = cmdport
    cmdserver.logcommands = 0

    # instrument
    if instflag is None:
        instrument = Instrument()
    elif instflag == "EB":
        instrument = InstrumentEB()
        instrument.pressure_ids = [0, 1]
        azcam.log(f"Instrument is Electron Bench")
    elif instflag == "QB":
        instrument = InstrumentQB()
        azcam.log(f"Instrument is Quantum Bench")
    elif instflag == "ASCOM":
        instrument = InstrumentArduino()

    # temperature controller
    if tempflag is None:
        tempflag = instflag
    if tempflag == "EB":
        tempcon = TempConCryoCon24()
        tempcon.host = "cryoconeb"  # EB
        tempcon.control_temperature = -100.0
        tempcon.init_commands = [
            "input A:units C",
            "input B:units C",
            "loop 1:type pid",
            "input A:isenix 2",
            "input B:isenix 2",
            "loop 1:range mid",
            "loop 1:maxpwr 100",
        ]
    elif tempflag == "QB":
        tempcon = TempConCryoCon24()
        tempcon.host = "cryoconqb"  # QB
        tempcon.control_temperature = -100.0
        tempcon.init_commands = [
            "input A:units C",
            "input B:units C",
            "loop 1:type pid",
            "input A:isenix 2",
            "input B:isenix 2",
            "loop 1:range mid",
            "loop 1:maxpwr 100",
        ]
    elif tempflag == "ASCOM":
        tempcon = TempConASCOM()
        tempcon.control_temperature = 0.0
    else:
        tempcon = TempCon()  # may be overwritten

    # load system-specific code
    if azcam.db.systemname != "NoSystem":
        importlib.import_module(f"azcam_itl.configs.config_server_{systemname}")

    # display
    display = Ds9Display()
    display.initialize()

    # scripts
    azcam.log("Loading azcam_itl.scripts.server")
    loadscripts(["azcam_itl.scripts.server"])

    # web server
    if 0:
        webserver = WebServer()
        webserver.port = 2403
        webserver.logcommands = 1
        webserver.logstatus = 0
        webserver.index = os.path.join(azcam.db.systemfolder, "index_ITL.html")
        webserver.message = f"for host {azcam.db.hostname}"
        webserver.start()

        webstatus = Status(webserver)
        webstatus.initialize()

        exptool = Exptool(webserver)
        exptool.initialize()

    # plotly web server
    else:
        webserver = LocalWebServer()
        webserver.port = 2403
        webserver.logcommands = 1
        webserver.logstatus = 0
        webserver.start()

    # azcammonitor
    azcam.db.monitor.register()

    # parameter file
    parfile = os.path.join(
        azcam.db.datafolder,
        "parameters",
        f"parameters_server_{azcam.db.systemname}.ini",
    )
    azcam.db.parameters.read_parfile(parfile)
    azcam.db.parameters.update_pars()

    # start command server
    azcam.log(f"Starting cmdserver - listening on port {cmdserver.port}")
    azcam.db.tools["api"].initialize_api()
    cmdserver.start()


# start
setup()
from azcam.cli import *

"""
Setup method for ITL azcamconsole.

Usage example:
ipython.exe ipython --ipython-dir=/data/ipython --profile azcamconsole -i -m azcam_itl.console -- -system DESI
"""

import os
import sys
from runpy import run_path

import azcam
import azcam.utils
from azcam.tools.ds9display import Ds9Display
from azcam.scripts.scripts import loadscripts

import azcam_console.console
from azcam_console.tools.console_tools import create_console_tools
import azcam_console.shortcuts
import azcam_console.scripts
from azcam_console.tools.focus import FocusConsole
from azcam_console.testers.testers import load_testers
from azcam_console.observe.observe_cli.observe_cli import ObserveCli

from azcam_itl import itlutils
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
        configuration = sys.argv[i + 1]  # may overwrite systemname
    except ValueError:
        configuration = None
    try:
        i = sys.argv.index("-cmdport")
        cmdport = int(sys.argv[i + 1])
    except ValueError:
        cmdport = 2402

    azcam.db.systemname = systemname

    # menu to select system
    menu_options = {
        "DESI": "DESI",
        # "LVM": "LVM",
        "ZWO ASI6200MM CMOS camera": "ASI6200MM",
        "ZWO ASI294 CMOS camera": "ASI294",
        "ZWO ASI183 CMOS camera": "ASI183",
        "QHY174 CMOS camera": "QHY174",
        # "ITL4k": "ITL4k",
        "90prime4k": "90prime4k",
        "None": "NoSystem",
    }

    # configuration
    if configuration is not None:
        run_path(configuration)

    if azcam.db.systemname == "menu":
        azcam.db.systemname = azcam.utils.show_menu(menu_options)

    azcam.db.systemfolder = azcam.utils.fix_path(os.path.dirname(__file__))
    azcam.db.datafolder = azcam.utils.get_datafolder(datafolder)

    # logging
    logfile = os.path.join(azcam.db.datafolder, "logs", "console.log")
    azcam.db.logger.start_logging(logfile=logfile)
    azcam.log(f"Configuring console for {azcam.db.systemname}")

    # display
    display = Ds9Display()
    display.initialize()
    # dthread = threading.Thread(target=display.initialize, args=[])
    # dthread.start()  # thread just for speed

    # console tools
    create_console_tools()
    focus = FocusConsole()
    load_testers()
    observe = ObserveCli()

    # scripts
    azcam.log("Loading scripts: azcam_itl.scripts, azcam_console.scripts")
    loadscripts(["azcam_itl.scripts", "azcam_console.scripts"])

    # try to connect to azcamserver
    connected = azcam.db.server.connect(port=cmdport)  # default host and port
    if connected:
        azcam.log("Connected to azcamserver")
    else:
        azcam.log("Not connected to azcamserver")

    # system-specific
    if azcam.db.systemname == "DESI":
        from azcam_itl.detchars.detchar_DESI import detchar

    elif azcam.db.systemname == "LVM":
        if 0:  # azcam.db.LVM_itl4k:
            from azcam_itl.detchars.detchar_ITL4k import detchar

        else:
            from azcam_itl.detchars.detchar_LVM import detchar

    elif azcam.db.systemname == "90prime4k":
        from azcam_itl.detchars.detchar_90prime4k import detchar

    elif azcam.db.systemname == "ASI183":
        from azcam_itl.detchars.detchar_ASI183 import detchar

    elif azcam.db.systemname == "ASI294":
        from azcam_itl.detchars.detchar_ASI294 import detchar

    elif azcam.db.systemname == "ASI6200MM":
        from azcam_itl.detchars.detchar_ASI6200MM import detchar

    elif azcam.db.systemname == "IMX411":
        from azcam_itl.detchars.detchar_IMX411 import detchar

    # elif azcam.db.systemname == "OSU4k":
    #     from azcam_itl.detchars.detchar_OSU4k import detchar

    # elif azcam.db.systemname == "ITL4k":
    #     from azcam_itl.detchars.detchar_ITL4k import detchar

    if azcam.db.wd is None:
        azcam.db.wd = azcam.db.datafolder

    # par file
    parfile = os.path.join(
        azcam.db.datafolder,
        "parameters",
        f"parameters_console_{azcam.db.systemname}.ini",
    )
    azcam.db.parameters.read_parfile(parfile)
    azcam.db.parameters.update_pars()


# start
setup()
from azcam_console.cli import *

del setup

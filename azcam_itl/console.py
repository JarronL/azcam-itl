"""
azcam console script for ITL detchar systems

Command line options:
  -system LVM
  -configure /data/LVM/config_LVM.py
  -datafolder path_to_datafolder
"""

import os
import sys
import ctypes
import threading
from runpy import run_path

import azcam
import azcam_console.console
import azcam_console.shortcuts
import azcam_console.tools.console_tools
import azcam_console.tools.testers
import azcam_console.scripts
from azcam_console.tools.ds9display import Ds9Display
from azcam_console.tools.focus import FocusConsole


from azcam_itl import itlutils
from azcam.scripts import loadscripts
import azcam_itl.shortcuts_itl

from azcam_observe.observe_cli.observe_cli import ObserveCli

# parse command line arguments
try:
    i = sys.argv.index("-system")
    azcam.db.systemname = sys.argv[i + 1]
except ValueError:
    azcam.db.systemname = "menu"
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

# menu to select system
menu_options = {
    "DESI": "DESI",
    # "LVM": "LVM",
    # "ZWO ASI2600MM CMOS camera": "ASI2600MM",
    "QHY174 CMOS camera": "QHY174",
    # "OSU4k": "OSU4k",
    # "ITL4k": "ITL4k",
    "None": "NoSystem",
}

# configuration
if configuration is not None:
    run_path(configuration)

if azcam.db.systemname == "menu":
    azcam.db.systemname = azcam.utils.show_menu(menu_options)

azcam.db.systemfolder = azcam.utils.fix_path(os.path.dirname(__file__))

if datafolder is None:
    droot = os.environ.get("AZCAM_DATAROOT")
    if droot is None:
        if os.name == "posix":
            droot = os.environ.get("HOME")
        else:
            droot = "/"
        azcam.db.datafolder = os.path.join(os.path.realpath(droot), "data", azcam.db.systemname)
    else:
        azcam.db.datafolder = os.path.join(os.path.realpath(droot), azcam.db.systemname)
else:
    azcam.db.datafolder = os.path.realpath(datafolder)

parfile = os.path.join(
    azcam.db.datafolder, "parameters", f"parameters_console_{azcam.db.systemname}.ini"
)

# logging
logfile = os.path.join(azcam.db.datafolder, "logs", "console.log")
azcam.db.logger.start_logging(logfile=logfile)
azcam.log(f"Configuring console for {azcam.db.systemname}")

# display
display = Ds9Display()
# dthread = threading.Thread(target=display.initialize, args=[])
# dthread.start()  # thread just for speed

# console tools
from azcam_console.tools import create_console_tools

create_console_tools()
focus = FocusConsole()

# ****************************************************************
# testers
# ****************************************************************
azcam_console.tools.testers.load()

# ****************************************************************
# ObserveCli
# ****************************************************************
observe = ObserveCli()

# ****************************************************************
# scripts
# ****************************************************************
azcam.log("Loading scripts")
loadscripts(["azcam_itl.scripts"])

# try to connect to azcamserver
connected = azcam.db.tools["server"].connect(port=cmdport)  # default host and port
if connected:
    azcam.log("Connected to azcamserver")
else:
    azcam.log("Not connected to azcamserver")

# system-specific
if azcam.db.systemname == "DESI":
    from azcam_itl.detchars.detchar_DESI import detchar
    import azcam_console.tools.console_arc

    if azcam.db.wd is None:
        azcam.db.wd = "/data/DESI"

elif azcam.db.systemname == "LVM":
    if 0:  # azcam.db.LVM_itl4k:
        from azcam_itl.detchars.detchar_ITL4k import detchar

        azcam.db.wd = "/data/ITL4k"
    else:
        from azcam_itl.detchars.detchar_LVM import detchar
    import azcam_console.tools.console_archon

    if azcam.db.wd is None:
        azcam.db.wd = "/data/LVM"

elif azcam.db.systemname == "90prime4k":
    from azcam_itl.detchars.detchar_90prime4k import detchar
    import azcam_console.tools.console_archon

    if azcam.db.wd is None:
        azcam.db.wd = "/data/90prime4k"

elif azcam.db.systemname == "ASI294":
    from azcam_itl.detchars.detchar_ASI294 import detchar

    if azcam.db.wd is None:
        azcam.db.wd = "/data/ZWO/ASI294"

elif azcam.db.systemname == "ASI2600MM":
    from azcam_itl.detchars.detchar_ASI2600MM import detchar

    if azcam.db.wd is None:
        azcam.db.wd = "/data/ASI2600MM"

elif azcam.db.systemname == "OSU4k":
    from azcam_itl.detchars.detchar_OSU4k import detchar
    import azcam_console.tools.console_archon

    if azcam.db.wd is None:
        azcam.db.wd = "/data/OSU4k"

elif azcam.db.systemname == "ITL4k":
    from azcam_itl.detchars.detchar_ITL4k import detchar
    import azcam_console.tools.console_archon

    if azcam.db.wd is None:
        azcam.db.wd = "/data/ITL4k"

if azcam.db.wd is None:
    azcam.db.wd = azcam.db.datafolder

# par file
azcam.db.parameters.read_parfile(parfile)
azcam.db.parameters.update_pars("azcamconsole")

# cli commands
from azcam.cli import *

# try to change window title
try:
    ctypes.windll.kernel32.SetConsoleTitleW("azcamconsole")
except Exception:
    pass

"""
azcam server script for ITL systems.

Command line options:
  -system LVM
  -configure /data/LVM/config_LVM.py
  -datafolder path_to_datafolder
"""

import importlib
import os
import sys
import ctypes
from runpy import run_path

import azcam
import azcam_server.server
import azcam_server.shortcuts
from azcam_server.cmdserver import CommandServer
from azcam.logger import check_for_remote_logger
from azcam.tools.webserver.fastapi_server import WebServer
from azcam_server.tools.webtools.exptool.exptool import Exptool
from azcam_server.tools.webtools.status.status import Status
import azcam_server.scripts

# from azcam_monitor.monitorinterface import AzCamMonitorInterface

import azcam_itl.shortcuts_itl

# ****************************************************************
# parse command line arguments
# ****************************************************************
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

# ****************************************************************
# configuration
# ****************************************************************

# optional config script
if configuration is not None:
    run_path(configuration)
    systemname = azcam.db.systemname  # may overwrite systemname

# optionally select system with menu
menu_options = {
    "DESI": "DESI",
    # "Magellan Guider": "magguider",
    # "SO Guider": "soguider",
    "QHY174 CMOS camera": "QHY174",
    # "LVM": "LVM",
    # "ZWO ASI2600MM CMOS camera": "ASI2600MM",
    # "OSU4k": "OSU4k",
    # "ITL6k": "ITL6k",
    # "90prime4k": "90prime4k",
    "QB": "QB",
    "EB": "EB",
    "None": "NoSystem",
}

if systemname == "menu":
    systemname = azcam.utils.show_menu(menu_options)
else:
    systemname = systemname
azcam.db.systemname = systemname
azcam.db.systemfolder = os.path.dirname(__file__)
azcam.db.systemfolder = azcam.utils.fix_path(azcam.db.systemfolder)

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

azcam.db.servermode = azcam.db.systemname
azcam.db.verbosity = 2

# ****************************************************************
# logging
# ****************************************************************
logfile = os.path.join(azcam.db.datafolder, "logs", "server.log")
if check_for_remote_logger():
    azcam.db.logger.start_logging(logtype="23", logfile=logfile)
else:
    azcam.db.logger.start_logging(logtype="1", logfile=logfile)
    # azcam.db.logger.start_logging(logtype="123", logfile=logfile)

# message
azcam.log(f"Configuring {azcam.db.systemname}")

# define command server
cmdserver = CommandServer()
cmdserver.port = cmdport
cmdserver.logcommands = 0

# ****************************************************************
# load system-specific code
# ****************************************************************
if azcam.db.systemname != "NoSystem":
    importlib.import_module(f"azcam_itl.configs.config_server_{systemname}")

# ****************************************************************
# scripts
# ****************************************************************
azcam.log("Loading scripts")
azcam_server.scripts.load()

# ****************************************************************
# web server
# ****************************************************************
if 1:
    webserver = WebServer()
    webserver.port = 2403
    webserver.logcommands = 0
    webserver.return_json = 0
    webserver.index = os.path.join(azcam.db.systemfolder, "index_ITL.html")
    webserver.message = f"for host {azcam.db.hostname}"
    webserver.datafolder = azcam.db.datafolder
    webserver.start()

    webstatus = Status()
    webstatus.message = "Status for ITL systems"
    webstatus.initialize()

    exptool = Exptool()
    exptool.initialize()

    azcam.log("Started webserver applications")

# ****************************************************************
# parameter file
# ****************************************************************
parfile = os.path.join(
    azcam.db.datafolder, "parameters", f"parameters_server_{azcam.db.systemname}.ini"
)
azcam.db.parameters.read_parfile(parfile)
azcam.db.parameters.update_pars(0, "azcamserver")

# ****************************************************************
# start command server
# ****************************************************************
azcam.log(f"Starting cmdserver - listening on port {cmdserver.port}")
cmdserver.start()

# cli commands
from azcam_server.cli import *

# try to change window title
try:
    ctypes.windll.kernel32.SetConsoleTitleW("azcamserver")
except Exception:
    pass

"""
azcam server script for ITL systems.

Command line options:
  -configure /data/LVM/config_LVM.py
  -system LVM
"""

import importlib
import os
import sys
from runpy import run_path

import azcam
import azcam.server
import azcam.shortcuts
from azcam.tools.cmdserver import CommandServer
from azcam.logger import check_for_remote_logger

from azcam_monitor.monitorinterface import AzCamMonitorInterface
from azcam_fastapi.fastapi_server import WebServer
from azcam_webtools.exptool.exptool import Exptool
from azcam_webtools.status.status import Status

import azcam_itl.shortcuts

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
    "LVM": "LVM",
    "ZWO ASI2600MM CMOS camera": "ASI2600MM",
    # "OSU4k": "OSU4k",
    "ITL6k": "ITL6k",
    "90prime4k": "90prime4k",
    "QB": "QB",
    "EB": "EB",
}

if systemname == "menu":
    azcam.db.systemname = azcam.utils.show_menu(menu_options)
else:
    azcam.db.systemname = systemname

azcam.db.systemfolder = os.path.dirname(__file__)
azcam.db.systemfolder = azcam.utils.fix_path(azcam.db.systemfolder)

if datafolder is None:
    droot = os.environ.get("AZCAM_DATAROOT")
    if droot is None:
        droot = os.environ.get("HOMEPATH")
        if droot is None:
            droot = os.environ.get("HOME")
            if droot is None:
                droot = "/data"
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
cmdserver.port = 2402
cmdserver.logcommands = 0

# ****************************************************************
# load system-specific code
# ****************************************************************
importlib.import_module(f"azcam_itl.configs.config_server_{azcam.db.systemname}")

# ****************************************************************
# web server
# ****************************************************************
if 0:
    webserver = WebServer()
    webserver.port = 2403
    webserver.logcommands = 0
    webserver.return_json = 0
    webserver.index = os.path.join(azcam.db.datafolder, "index_ITL.html")
    webserver.message = f"for host {azcam.db.hostname}"
    webserver.datafolder = azcam.db.datafolder
    webserver.start()

    webstatus = Status()
    webstatus.message = "for ITL systems"
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
azcam.db.tools["parameters"].read_parfile(parfile)
azcam.db.tools["parameters"].update_pars(0, "azcamserver")

# ****************************************************************
# start command server
# ****************************************************************
azcam.log(f"Starting cmdserver - listening on port {cmdserver.port}")
cmdserver.start()

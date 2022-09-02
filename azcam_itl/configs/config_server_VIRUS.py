import os

import azcam
from azcam.tools.system import System
from azcam_arc.controller_arc import ControllerArc
from azcam_arc.exposure_arc import ExposureArc
from azcam_cryocon.tempcon_cryocon24 import TempConCryoCon24
from azcam_monitor.monitorinterface import AzCamMonitorInterface
from azcam_ds9.ds9display import Ds9Display
from azcam_focus.focus import Focus
from azcam_observe.observe import Observe
from azcam_fastapi.fastapi_server import WebServer

from azcam_itl.instruments.instrument_bb import InstrumentBB
from azcam_itl.instruments.instrument_qb import InstrumentQB
from azcam_itl.detectors import detector_sta3600_VIRUS2, detector_sta3600

VIRUS2 = 1
COLD = 1

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArc()
controller.timing_board = "arc22"
controller.clock_boards = ["arc32"]
controller.video_boards = ["arc45", "arc45"]
controller.utility_board = None
controller.set_boards()
controller.utility_file = ""
if COLD:
    controller.video_gain = 5
else:
    controller.video_gain = 1
controller.video_speed = 1
# controller.camserver.set_server("conserver2")  # BB
controller.camserver.set_server("conserver1")  # QB
controller.pci_file = os.path.join(azcam.db.datafolder, "dspcode", "dsppci3", "pci3.lod")

if VIRUS2:
    if COLD:
        controller.timing_file = os.path.join(
            azcam.db.datafolder, "dspcode", "dsptiming_virus2", "VIRUS_config2.lod"
        )
    else:
        controller.timing_file = os.path.join(
            azcam.db.datafolder, "dspcode", "dsptiming_virus2_warm", "VIRUS_config2.lod"
        )
else:
    controller.timing_file = os.path.join(
        azcam.db.datafolder, "dspcode", "dsptiming", "VIRUS_config0.lod"
    )

# ****************************************************************
# instrument
# ****************************************************************
# instrument = InstrumentBB()
instrument = InstrumentQB()

# ****************************************************************
# tempcon
# ****************************************************************
tempcon = TempConCryoCon24()
# tempcon.host = "10.0.0.48"  # BB
tempcon.host = "10.0.0.44"  # QB
tempcon.control_temperature = -110.0
tempcon.init_commands = [
    "input A:units C",
    "input B:units C",
    "input A:isenix 2",
    "input B:isenix 2",
    "loop 1:type pid",
    "loop 1:range mid",
    "loop 1:maxpwr 100",
]

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureArc()
if VIRUS2:
    filetype = "FITS"
else:
    filetype = "MEF"
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
if VIRUS2:
    exposure.set_detpars(detector_sta3600_VIRUS2)
else:
    exposure.set_detpars(detector_sta3600)

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_VIRUS.txt")
system = System("VIRUS", template)
system.set_keyword("DEWAR", "ITL5", "Dewar name")

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

# ****************************************************************
# focus
# ****************************************************************
focus = Focus()
focus.focus_component = "instrument"
focus.focus_type = "absolute"

# ****************************************************************
# observe
# ****************************************************************
observe = Observe()

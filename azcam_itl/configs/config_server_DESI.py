import os

import azcam
from azcam.header import System
from azcam_server.tools.arc.controller_arc import ControllerArc
from azcam_server.tools.arc.exposure_arc import ExposureArc
from azcam_server.tools.tempcon_cryocon24 import TempConCryoCon24
from azcam_server.tools.ds9display import Ds9Display
from azcam_server.tools.focus import Focus

from azcam_itl.instruments.instrument_bb import InstrumentBB
from azcam_itl.detectors import detector_sta4150_4amp, detector_sta4150_2amp_left

FOURAMPS = 1

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArc()
controller.timing_board = "arc22"
controller.clock_boards = ["arc32"]
controller.video_boards = ["arc45", "arc45"]
controller.set_boards()
controller.utility_board = None
controller.pci_file = os.path.join(azcam.db.datafolder, "dspcode", "dsppci3", "pci3.lod")
controller.video_gain = 2
controller.video_speed = 1
controller.camserver.set_server("conserver2")

# controller timing file
if FOURAMPS:
    controller.timing_file = os.path.join(
        azcam.db.datafolder, "dspcode", "dsptiming", "DESI_config0.lod"
    )
else:
    controller.timing_file = os.path.join(
        azcam.db.datafolder, "dspcode", "dsptiming_fast_2amp", "DESI_config0.lod"
    )

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentBB()

# ****************************************************************
# tempcon
# ****************************************************************
tempcon = TempConCryoCon24(description="cryoconbb")
tempcon.host = "10.0.0.48"
tempcon.control_temperature = -100.0
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
filetype = "MEF"
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_DESI.txt")
system = System("DESI", template)
system.set_keyword("DEWAR", "ITL6", "Dewar name")

# ****************************************************************
# detector
# ****************************************************************
if FOURAMPS:
    exposure.set_detpars(detector_sta4150_4amp)
else:
    exposure.set_detpars(detector_sta4150_2amp_left)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

# ****************************************************************
# focus
# ****************************************************************
focus = Focus()

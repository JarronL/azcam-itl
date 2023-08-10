import os

import azcam
from azcam.header import System
from azcam_server.tools.archon.controller_archon import ControllerArchon
from azcam_server.tools.arc.exposure_arc import ExposureArc
from azcam_server.tools.tempcon_cryocon24 import TempConCryoCon24
from azcam_server.tools.ds9display import Ds9Display
from azcam_server.tools.focus import Focus

from azcam_itl.instruments.instrument_eb import InstrumentEB
from azcam_itl.instruments.instrument_qb import InstrumentQB
from azcam_itl.detectors import detector_sta4150_4amp, detector_sta4150_2amp_left

FOURAMPS = 1

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArchon()
controller.camserver.port = 4242
controller.camserver.host = "10.0.2.12"  # ITL3

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentQB()

# ****************************************************************
# tempcon
# ****************************************************************
tempcon = TempConCryoCon24(description="cryoconqb")
tempcon.host = "10.131.0.10"
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

import os

import azcam
from azcam.header import System
from azcam.server.tools.ds9display import Ds9Display
from azcam.server.tools.archon.controller_archon import ControllerArchon
from azcam.server.tools.archon.exposure_archon import ExposureArchon

from azcam_itl.detectors import (
    detector_sta4850,
    detector_sta4850_2amps_side,
    detector_sta4850_2amps_top,
)

# optional configuration options
LVM_2amps = 0
LVM_science = 0
LVM_webserver = 0

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArchon()
controller.camserver.port = 4242
if LVM_science:
    controller.camserver.host = "10.0.0.2"  # LVM cryostat
else:
    controller.camserver.host = "10.0.2.11"  # ITL2 for characterization

# ****************************************************************
# temperature controller
# ****************************************************************
azcam.db.tools["tempcon"].control_temperature = -110.0

# ****************************************************************
# exposure
# ****************************************************************
filetype = "MEF"
exposure = ExposureArchon()
if LVM_2amps:
    exposure.fileconverter.set_detector_config(detector_sta4850_2amps_side)
    exposure.fileconverter.set_detector_config(detector_sta4850_2amps_top)
else:
    exposure.fileconverter.set_detector_config(detector_sta4850)
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.add_extensions = 1

exposure.image.focalplane.gains = [
    1.0,
    1.0,
    1.0,
    1.0,
]
exposure.image.focalplane.rdnoises = [
    5.0,
    5.0,
    5.0,
    5.0,
]

# ****************************************************************
# detector
# ****************************************************************
if LVM_2amps:
    # exposure.set_detpars(detector_sta4850_2amps_side)
    exposure.set_detpars(detector_sta4850_2amps_top)
else:
    exposure.set_detpars(detector_sta4850)

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_ITL4k.txt")
system = System("ITL4k", template)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

# ****************************************************************
# special
# ****************************************************************
# arduino = InstrumentArduino()
# azcam.db.tools["arduino"] = arduino

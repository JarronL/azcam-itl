import os

import azcam
from azcam.header import System
from azcam.tools.archon.controller_archon import ControllerArchon
from azcam.tools.archon.exposure_archon import ExposureArchon

from azcam_itl.detectors import (
    detector_sta4850,
    detector_sta4850_2amps_side,
    detector_sta4850_2amps_top,
)

# optional configuration options
LVM_2amps = azcam.db.get("LVM_2amps")
if LVM_2amps is None:
    LVM_2amps = 0
LVM_science = azcam.db.get("LVM_science")
if LVM_science is None:
    LVM_science = 0
LVM_webserver = azcam.db.get("LVM_webserver")
if LVM_webserver is None:
    LVM_webserver = 1

# ARB test
LVM_science = 1

# ****************************************************************
# instrument
# ****************************************************************
if LVM_science:
    azcam.db.tools["instrument"].pressure_ids = [0, 1]

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArchon()
controller.camserver.port = 4242
if LVM_science:
    # controller.camserver.host = "10.0.0.2"  # LVM cryostat
    controller.camserver.host = "10.7.45.36"  # LVM cryostat
else:
    controller.camserver.host = "10.0.2.11"  # ITL2 for characterization

# ****************************************************************
# temperature controller
# ****************************************************************
azcam.db.tools["tempcon"].control_temperature = -110.0
if LVM_science:
    controller.heater_board_installed = 1

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
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_LVM.txt")
system = System("LVM", template)

# ****************************************************************
# header data
# ****************************************************************
exposure.image.focalplane.gains = [
    2.0,
    2.0,
    2.0,
    2.0,
]
exposure.image.focalplane.rdnoises = [0.0, 0.0, 0.0, 0.0]

# ****************************************************************
# special
# ****************************************************************
# arduino = InstrumentArduino()
# azcam.db.tools["arduino"] = arduino

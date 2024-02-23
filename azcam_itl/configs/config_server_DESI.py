import os

import azcam
from azcam.header import System
from azcam_server.tools.archon.controller_archon import ControllerArchon
from azcam_server.tools.archon.exposure_archon import ExposureArchon
from azcam_server.tools.ds9display import Ds9Display
from azcam_server.tools.focus import Focus

from azcam_itl.detectors import detector_sta4150_4amp, detector_sta4150_2amp_left

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArchon()
controller.camserver.port = 4242
controller.camserver.host = "10.0.2.11"  # ITL2

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureArchon()
exposure.fileconverter.set_detector_config(detector_sta4150_4amp)
filetype = "MEF"
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.add_extensions = 0
exposure.image.focalplane.gains = [
    2.0,
    2.0,
    2.0,
    2.0,
]
exposure.image.focalplane.rdnoises = [0.0, 0.0, 0.0, 0.0]

tempcon = azcam.db.tools["tempcon"]
tempcon.control_temperature = -110.0
tempcon.temperature_ids = [3, 1]  # camtemp, dewtemp for ITL2

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_DESI.txt")
system = System("DESI", template)
system.set_keyword("DEWAR", "ITL6", "Dewar name")

# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_sta4150_4amp)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

# ****************************************************************
# focus
# ****************************************************************
focus = Focus()

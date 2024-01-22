import os

import azcam
from azcam.header import System
from azcam_server.tools.ds9display import Ds9Display
from azcam_server.tools.archon.controller_archon import ControllerArchon
from azcam_server.tools.archon.exposure_archon import ExposureArchon

from azcam_itl.detectors import detector_sta4850, detector_sta4850_2amps_top

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArchon()
controller.camserver.port = 4242
controller.camserver.host = "10.0.2.12"  # ITL3

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = azcam.db.tools["tempcon"]
tempcon.control_temperature = -100.0
if tempcon.host == "cryoconqb":
    tempcon.temperature_ids = [2, 0]

# ****************************************************************
# exposure
# ****************************************************************
filetype = "MEF"
exposure = ExposureArchon()
exposure.fileconverter.set_detector_config(detector_sta4850_2amps_top)
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.add_extensions = 0
exposure.image.focalplane.gains = [
    6.0,
    6.0,
    6.0,
    6.0,
]
exposure.image.focalplane.rdnoises = [0.0, 0.0, 0.0, 0.0]


# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_sta4850_2amps_top)

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_90prime4k.txt")
system = System("ITL3", template)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

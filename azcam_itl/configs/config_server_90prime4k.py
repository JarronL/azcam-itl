import os

import azcam
from azcam.header import System
from azcam.tools.archon.controller_archon import ControllerArchon
from azcam.tools.archon.exposure_archon import ExposureArchon

from azcam_itl.detectors import detector_sta4850, detector_sta4850_2amps_top

# controller
controller = ControllerArchon()
controller.camserver.port = 4242
controller.camserver.host = "10.0.0.12"  # ITL3

# temperature controller
azcam.db.tools["tempcon"].temperature_ids = [2, 0]  # ITL3

# exposure
filetype = "MEF"
exposure = ExposureArchon()
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.add_extensions = 0
if 1:
    exposure.set_detpars(detector_sta4850_2amps_top)
    exposure.fileconverter.set_detector_config(detector_sta4850_2amps_top)
    exposure.image.focalplane.gains = 2 * [3.0]
    exposure.image.focalplane.rdnoises = 2 * [0.0]
else:
    exposure.set_detpars(detector_sta4850)
    exposure.fileconverter.set_detector_config(detector_sta4850)
    exposure.image.focalplane.gains = 4 * [3.0]
    exposure.image.focalplane.rdnoises = 4 * [0.0]

# system header
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_90prime4k.txt")
system = System("ITL3", template)

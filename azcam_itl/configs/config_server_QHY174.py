import os
import sys

import azcam
from azcam.header import System
from azcam.tools.ascom.controller_ascom import ControllerASCOM
from azcam.tools.ascom.exposure_ascom import ExposureASCOM
from azcam.tools.ascom.tempcon_ascom import TempConASCOM

from azcam_itl.detectors import detector_qhy174

# ****************************************************************
# controller
# ****************************************************************
try:
    controller = ControllerASCOM()
    controller.driver = "ASCOM.QHYCCD.Camera"

    # init now due to threading issue
    controller.initialize()

    controller.nx = 8288
    controller.ny = 5644
    controller.camera.Gain = 0
    controller.camera.Offset = 10
except Exception:
    pass

"""
# QHY174 data
self.camera.Gain = 0    # 0.49 e/DN, 5.7 e noise
self.camera.Gain = 1    # 0.46 e/DN, 5.5 e noise
self.camera.Gain = 10   # 0.42 e/DN, 5.3 e noise
self.camera.Gain = 30   # 0.32 e/DN, 4.8 e noise
self.camera.Gain = 100  # 0.17 e/DN, 4.7 e noise
self.camera.Gain = 144  # 0.12 e/DN, 3.8 e noise
self.camera.Gain = 480  # 0.02 e/DN, 3.8 e noise  # not well behaved for high gain
 """

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = TempConASCOM()
tempcon.control_temperature = -20
tempcon.initialize()

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureASCOM()
filetype = "FITS"
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.image.filename = os.path.join(azcam.db.datafolder, "image.fits")

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_QHY174.txt")
system = System("QHY174", template)

# ****************************************************************
# detector
# ****************************************************************
try:
    exposure.set_detpars(detector_qhy174)
except Exception:
    pass

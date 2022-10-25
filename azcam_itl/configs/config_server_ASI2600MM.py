import os
import sys

from azcam_itl.detectors import detector_asi2600MM
from azcam_ascom.controller_ascom import ControllerASCOM
from azcam_ascom.exposure_ascom import ExposureASCOM
from azcam_ascom.tempcon_ascom import TempConASCOM

import azcam
from azcam.tools.system import System

# from azcam.tools.instrument import Instrument
from azcam_itl.instruments.instrument_qb import InstrumentQB
from azcam.tools.tempcon import TempCon
from azcam_ds9.ds9display import Ds9Display
from azcam_imageserver.sendimage import SendImage

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerASCOM()
controller.driver = "ASCOM.ASICamera2.Camera"
# init now due to threading issue
try:
    controller.initialize()
    controller.nx = 6248
    controller.ny = 4176
    # controller.camera.Gain = 120
    # controller.camera.Offset = 10
except Exception as e:
    print(e)
    print("could not initialize camera")
"""
ZWO ASI294 data
start at 1.0 e/DN
self.camera.Gain = 150  # 0.68 e/DN, 3.4 e noise
self.camera.Gain = 120  # 0.88 e/DN, 3.5 e noise
self.camera.Gain = 115  # 1.10 e/DN, 12.4 e noise
self.camera.Gain = 90   # 1.46 e/DN, 12.6 e noise
self.camera.Gain = 60   # 2.85 e/DN, 12.0 e noise
self.camera.Offset = 10
 """

# ****************************************************************
# instrument
# ****************************************************************
# instrument = Instrument()
instrument = InstrumentQB()

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = TempConASCOM()
tempcon.control_temperature = -20
try:
    tempcon.initialize()
except Exception:
    pass

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureASCOM()
filetype = "FITS"  # BIN FITS
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.image.filename = "/data/ASI2600MM/image.fits"  # .bin .fits

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_ASI2600MM.txt")
system = System("ASI2600MM", template)

# ****************************************************************
# detector
# ****************************************************************
try:
    exposure.set_detpars(detector_asi2600MM)
except Exception:
    pass

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

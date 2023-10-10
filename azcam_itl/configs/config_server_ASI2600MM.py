import os

import azcam
from azcam_server.tools.ascom.controller_ascom import ControllerASCOM
from azcam_server.tools.ascom.exposure_ascom import ExposureASCOM
from azcam_server.tools.ascom.tempcon_ascom import TempConASCOM
from azcam.header import System
from azcam_server.tools.ds9display import Ds9Display

from azcam_itl.detectors import detectors_asi2600MM
from azcam_itl.instruments.instrument_qb import InstrumentQB

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerASCOM()
controller.driver = "ASCOM.ASICamera2.Camera"
# init now due to threading issue
try:
    controller.nx = 6248
    controller.ny = 4176
    controller.initialize()
    controller.camera.Gain = 100
    controller.camera.Offset = 1
except Exception as e:
    print(e)
    print("could not initialize camera")
    # print("Gain:", controller.camera.Gain)
    # print("Offset:", controller.camera.Offset)
    # controller.nx = 6248
    # controller.ny = 4176
    # controller.camera.Gain = 120
    # controller.camera.Offset = 10

"""
ZWO ASI2600MM data
self.camera.Offset = 10
self.camera.Gain = 120  # 0.20 e/DN, 1.4 e noise
self.camera.Gain = 100  # 0.25 e/DN, 1.6 e noise
self.camera.Gain = 80   # 0.32 e/DN, 3.6 e noise
self.camera.Gain = 60   # 0.40 e/DN, 3.5 e noise
self.camera.Gain = 20   # 0.60 e/DN, 3.5 e noise
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
    exposure.set_detpars(detectors_asi2600MM)
except Exception:
    pass

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

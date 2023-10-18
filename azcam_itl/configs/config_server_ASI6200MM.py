import os

import azcam
from azcam_server.tools.ascom.controller_ascom import ControllerASCOM
from azcam_server.tools.ascom.exposure_ascom import ExposureASCOM
from azcam_server.tools.ascom.tempcon_ascom import TempConASCOM
from azcam.header import System
from azcam_server.tools.ds9display import Ds9Display

from azcam_itl.detectors import detector_asi6200MM
from azcam_itl.instruments.instrument_qb import InstrumentQB
from azcam_itl.instruments.instrument_eb import InstrumentEB

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
    controller.camera.Gain = 50
    controller.camera.Offset = 10
except Exception as e:
    print(e)
    print("could not initialize camera")

# ASCOM GainMax is 100
# gain 1, offset 10 (100DN) was used for unbinned, 0.8 e/DN
# gain 1, offset 10 (100DN) was used for 2x2, 3.2 e/DN
# gain 10, offset 10 (100DN) was used for 2x2, 2.7 e/DN
# gain 100, offset 10 (100DN) was used for 2x2, 1.0 e/DN

# ****************************************************************
# add remote commands to server
# ****************************************************************
azcam.db.par_table["cmos_gain"] = "controller.camera.Gain"

# ****************************************************************
# instrument
# ****************************************************************
if 0:
    instrument = InstrumentQB()
else:
    instrument = InstrumentEB()

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = TempConASCOM()
tempcon.control_temperature = -10.0
tempcon.initialize()

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureASCOM()
filetype = "FITS"  # BIN FITS
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.image.filename = "/data/ASI6200MM/image.fits"  # .bin .fits

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_ASI6200MM.txt")
system = System("ASI6200MM", template)

# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_asi6200MM)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

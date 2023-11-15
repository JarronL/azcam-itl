import os

import azcam
from azcam_server.tools.ascom.controller_ascom import ControllerASCOM
from azcam_server.tools.ascom.exposure_ascom import ExposureASCOM
from azcam_server.tools.ascom.tempcon_ascom import TempConASCOM
from azcam.header import System
from azcam_server.tools.ds9display import Ds9Display

from azcam_itl.detectors import detector_imx411
from azcam_itl.instruments.instrument_qb import InstrumentQB

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerASCOM()
controller.driver = "ASCOM.MoravinstCCD.GXCamera64"

# init now due to threading issue
try:
    controller.nx = 14208
    controller.ny = 10656
    controller.initialize()
    controller.camera.Gain = 3000
except Exception as e:
    print(e)
    print("could not initialize camera")

# ASCOM GainMax is 4030

# gain 10, binned 2x2, 3.0 e/DN
# gain 2000, binned 2x2, 1.6 e/DN

# gain 0, offset 10 (100DN) was used for unbinned, 0.76 e/DN
# gain 10, offset 10 (100DN) was used for unbinned, 0.76 e/DN
# gain 1000, offset 10 (100DN) was used for unbinned, 0.59 e/DN


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
# instrument = Instrument()
instrument = InstrumentQB()

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
exposure.image.filename = "/data/IMX411/image.fits"  # .bin .fits

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_IMX411.txt")
system = System("IMX411", template)

# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_imx411)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

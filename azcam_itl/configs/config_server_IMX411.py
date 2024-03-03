import os

import azcam
from azcam.server.tools.ascom.controller_ascom import ControllerASCOM
from azcam.server.tools.ascom.exposure_ascom import ExposureASCOM
from azcam.header import System
from azcam.server.tools.ds9display import Ds9Display

from azcam_itl.detectors import detector_imx411

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
    # gains around 1 e/DN
    # controller.camera.Gain = 3000  # 2x2
    controller.camera.Gain = 1  # unbinned
except Exception as e:
    print(e)
    print("could not initialize camera")

# ASCOM GainMax is 4030

# ****************************************************************
# add remote commands to server
# ****************************************************************
azcam.db.par_table["cmos_gain"] = "controller.camera.Gain"

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

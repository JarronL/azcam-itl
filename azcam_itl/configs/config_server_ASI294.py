import os
import sys

import azcam
from azcam_itl.detectors import detector_asi294
from azcam.server.tools.ascom.controller_ascom import ControllerASCOM
from azcam.server.tools.ascom.exposure_ascom import ExposureASCOM
from azcam.header import System
from azcam.server.tools.tempcon import TempCon
from azcam.server.tools.ds9display import Ds9Display

# ****************************************************************
# controller
# ****************************************************************
try:
    controller = ControllerASCOM()
    controller.driver = "ASCOM.ASICamera2.Camera"
    # init now due to threading issue
    controller.initialize()
    controller.nx = 8288
    controller.ny = 5644
    controller.camera.Gain = 1
    controller.camera.Offset = 10
except Exception as e:
    azcam.log(e)

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
# add remote commands to server
# ****************************************************************
azcam.db.par_table["cmos_gain"] = "controller.camera.Gain"

# ****************************************************************
# temperature controller
# ****************************************************************
azcam.db.tools["tempcon"].control_temperature = -20
azcam.db.tools["tempcon"].initialize()

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureASCOM()
filetype = "FITS"  # BIN FITS
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.image.filename = "/data/asi294/image.fits"  # .bin .fits

# ****************************************************************
# remote image
# ****************************************************************
if 0:
    remote_imageserver_host = "lesser"
    remote_imageserver_port = 6543
    exposure.sendimage.set_remote_imageserver(
        remote_imageserver_host,
        remote_imageserver_port,
        "azcam",
        "/azcam/soguider/image.bin",
    )

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_ASI294.txt")
system = System("ASI294", template)

# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_asi294)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

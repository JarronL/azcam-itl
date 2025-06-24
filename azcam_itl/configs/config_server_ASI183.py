import os
import sys

import azcam
from azcam_itl.detectors import detector_asi183
from azcam.tools.ascom.controller_ascom import ControllerASCOM
from azcam.tools.ascom.exposure_ascom import ExposureASCOM
from azcam.header import System
from azcam.tools.tempcon import TempCon

# ****************************************************************
# controller
# ****************************************************************
try:
    controller = ControllerASCOM()
    controller.driver = "ASCOM.ASICamera2.Camera"
    # init now due to threading issue
    controller.initialize()
    controller.nx = 5496
    controller.ny = 3672

    controller.camera.Gain = 120  # 120 is medium gain
    controller.camera.Offset = 10

except Exception as e:
    azcam.log(e)

"""
ZWO ASI183 data

self.camera.Gain = 200  # 0.4 e/DN, 1.8 e noise
self.camera.Gain = 150  # 0.7 e/DN, 2.0 e noise
self.camera.Gain = 100  # 1.3 e/DN, 2.3 e noise
self.camera.Gain = 50   # 2.1 e/DN, 2.7 e noise
self.camera.Gain = 0    # 3.6 e/DN, 3.0 e noise
self.camera.Offset = 10
 """

# ****************************************************************
# add remote commands to server
# ****************************************************************
azcam.db.par_table["cmos_gain"] = "controller.camera.Gain"

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = azcam.db.tools["tempcon"]
tempcon.control_temperature = +10.0
# Try to initialize the temperature controller
tempcon.initialize()
if tempcon.is_initialized:
    cid = tempcon.control_temperature_id
    ctemp_set = tempcon.control_temperature
    ctemp_sensor = tempcon.get_temperature(cid)
    channel_vals = [0, 1]
    print('')
    print(f"Control sensor temp on Ch {channel_vals[cid]}: {ctemp_sensor} C")
    print(f"Control sensor setpoint: {ctemp_set} C")
    print('')
else:
    azcam.exceptions.warning("WARNING: Temperature controller could not initialize!")

# ****************************************************************
# instrument
# ****************************************************************
# Turn off shutter strobe
azcam.db.tools["instrument"].shutter_strobe = 0

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureASCOM()
filetype = "FITS"  # BIN FITS
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.image.filename = "/data/asi183/image.fits"  # .bin .fits

# ****************************************************************
# remote image
# ****************************************************************
# remote_imageserver_host = "lesser"
# remote_imageserver_port = 6543
# exposure.sendimage.set_remote_imageserver(
#     remote_imageserver_host,
#     remote_imageserver_port,
#     "azcam",
#     "/azcam/soguider/image.bin",
# )

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_ASI183.txt")
system = System("ASI183", template)

# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_asi183)

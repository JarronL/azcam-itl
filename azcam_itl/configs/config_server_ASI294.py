import os
import sys

import azcam
from azcam_itl.detectors import detector_asi294
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
    controller.nx = 8288
    controller.ny = 5644

    controller.camera.Gain = 120  # 120 is medium gain
    controller.camera.Offset = 10

except Exception as e:
    azcam.log(e)

"""
ZWO ASI294 data
HCG is automatic when gain above 120

1/8/2x2 = 1.0 e/DN
120/10/2x2 = 0.2 e/DN  1.8 e noise
120/10/1x1 = 0.06 e/DN
120/10/4x4 = 0.90 e/DN
300/30/1x1 = 0.01 e/DN  1.6 e noise
0/10/1x1 = 0.19 e/DN  2.9 e noise

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
tempcon = azcam.db.tools["tempcon"]
tempcon.control_temperature = +20.0
# Try to initialize the temperature controller
try:
    tempcon.initialize()
    cid = tempcon.control_temperature_id
    ctemp_set = tempcon.control_temperature
    ctemp_sensor = tempcon.get_temperature(cid)
    channel_vals = [0, 1]
    print('')
    print(f"Control sensor temp on Ch {channel_vals[cid]}: {ctemp_sensor} C")
    print(f"Control sensor setpoint: {ctemp_set} C")
    print('')
except:
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
if controller.is_initialized:
    exposure.set_detpars(detector_asi294)
else:
    azcam.exceptions.warning(
        "ASI294 controller is not initialized, cannot set detector parameters."
    )


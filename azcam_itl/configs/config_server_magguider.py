import os

from azcam_itl.detectors import detector_ccd57
from azcam_mag.controller_mag import ControllerMag
from azcam_mag.exposure_mag import ExposureMag
from azcam_mag.tempcon_mag import TempConMag
from azcam_mag.udpinterface import UDPinterface

import azcam
from azcam.tools.instrument import Instrument

# broadcast:
if 0:
    udpobj = UDPinterface()
    reply = udpobj.GetIDs()
    if reply == []:
        azcam.log("No systems responded to broadcast")
        guider_address = "guider"
        guider_port = 2425
    for system in reply:
        tokens = system[0].split(" ")
        azcam.log(f"Found {tokens[2]} at ({tokens[4]}:{int(tokens[3])})")
        guider_address = tokens[4]
        guider_port = int(tokens[3])
        # reply = udpobj.GetIP('guider_z1')
        break  # for now, use first response
else:
    guider_address = "10.0.1.100"
    guider_port = 2425
    guider_address = "guider2"
    guider_port = 2405

print("Using:", guider_address, guider_port)
# ****************************************************************
# controller
# ****************************************************************
controller = ControllerMag()
controller.camserver.set_server(guider_address, guider_port)
controller.timing_file = os.path.join(azcam.db.datafolder, "dspcode", "gcam_ccd57.s")
# ****************************************************************
# instrument
# ****************************************************************
instrument = Instrument()

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = TempConMag()

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureMag()
# filetype = "FITS"
filetype = "BIN"
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]

# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_ccd57)

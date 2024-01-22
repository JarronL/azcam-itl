import os

import azcam
from azcam_server.tools.instrument import Instrument
from azcam_server.tools.mag.controller_mag import ControllerMag
from azcam_server.tools.mag.exposure_mag import ExposureMag
from azcam_server.tools.mag.tempcon_mag import TempConMag
from azcam_server.tools.mag.udpinterface import UDPinterface

from azcam_itl.detectors import detector_ccd57

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

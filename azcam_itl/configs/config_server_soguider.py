import os
import sys

import azcam
from azcam.server.tools.mag.controller_mag import ControllerMag
from azcam.server.tools.mag.exposure_mag import ExposureMag
from azcam.server.tools.mag.tempcon_mag import TempConMag
from azcam.server.tools.mag.udpinterface import UDPinterface

from azcam_itl.detectors import detector_ccd57

try:
    i = sys.argv.index("-broadcast")
    BROADCAST = 1
except ValueError:
    BROADCAST = 0

# broadcast:
if BROADCAST:
    udpobj = UDPinterface()
    reply = udpobj.GetIDs()
    if reply == []:
        azcam.log("No systems responded to broadcast")
        guider_address = "guider2"
        guider_port = 2405
    for system in reply:
        tokens = system[0].split(" ")
        azcam.log(f"Found {tokens[2]} at ({tokens[4]}:{int(tokens[3])})")
        guider_address = tokens[4]
        guider_port = int(tokens[3])
        # reply = udpobj.GetIP('guider_z1')
        break  # for now, use first response
else:
    guider_address = "guider2"
    guider_port = 2405

azcam.log("Using guide camera:", guider_address, guider_port)

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerMag()
controller.camserver.set_server(guider_address, guider_port)
controller.timing_file = os.path.join(azcam.db.datafolder, "dspcode/gcam_ccd57.s")

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
exposure.image.filename = "/azcam/soguider/image.bin"
exposure.test_image = 0
exposure.display_image = 0
exposure.image.make_lockfile = 1


# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_ccd57)

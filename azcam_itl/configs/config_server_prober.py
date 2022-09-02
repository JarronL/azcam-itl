import os
import sys

from azcam_arc.controller_arc import ControllerArc
from azcam_arc.exposure_arc import ExposureArc

import azcam
from azcam.tools.system import System
from azcam_itl.instruments.instrument_prober import InstrumentProber
from azcam_itl.tempcons.tempcon_prober import TempConProber
from azcam_ds9.ds9display import Ds9Display

subsystem = sys.argv[-1]
if subsystem not in ["LVM"]:
    subsystem = "LVM"

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArc()
controller.timing_board = "arc22"
controller.clock_boards = ["arc32"]
controller.video_boards = ["arc47", "arc47"]
controller.utility_board = None
controller.set_boards()
host = "conserverprober"
port = 2405
controller.camserver.set_server(host, port)
controller.utility_file = ""
controller.pci_file = os.path.join(azcam.db.datafolder, "dspcode", "dsppci3", "pci3.lod")

if subsystem == "LVM":
    controller.timing_file = os.path.join(
        azcam.db.datafolder, "dspcode", "dsptiming_LVM", "LVM_prober_config0.lod"
    )

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentProber()
instrument.enabled = 0

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = TempConProber()

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureArc()
filetype = "MEF"
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.folder = azcam.db.datafolder

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_prober.txt")
system = System("prober", template)

# ****************************************************************
# detector
# ****************************************************************
if subsystem == "LVM":
    detector_sta4850_prober = {
        "name": "STA4850",
        "description": "STA STA4850 CCD on ITL prober",
        "ref_pixel": [2040, 2040],
        "format": [4080, 4, 0, 20, 4080, 0, 0, 0, 0],
        "focalplane": [1, 1, 2, 2, "0132"],
        "roi": [1, 4080, 1, 4080, 1, 1],
        "ext_position": [[1, 1], [2, 1], [2, 2], [1, 2]],
        "jpg_order": [1, 2, 3, 4],
    }

    exposure.set_detpars(detector_sta4850_prober)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

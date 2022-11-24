import sys
import os

import azcam
from azcam.tools.system import System
from azcam.tools.archon.controller_archon import ControllerArchon
from azcam.tools.archon.exposure_archon import ExposureArchon
from azcam.tools.archon.tempcon_archon import TempConArchon
from azcam.tools.ds9.ds9display import Ds9Display

from azcam_itl.detectors import detector_sta0500
from azcam_itl.instruments.instrument_bb import InstrumentBB

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArchon()
controller.camserver.port = 4242
controller.camserver.host = "10.0.0.2"
controller.heater_board_installed = 1

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentBB()
azcam.log(f"Instrument is Boson Bench")

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = TempConArchon()

# ****************************************************************
# exposure
# ****************************************************************
filetype = "MEF"
exposure = ExposureArchon()
exposure.fileconverter.set_detector_config(detector_sta0500)
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.add_extensions = 1

# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_sta0500)

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_OSU4k.txt")
system = System("OSU4k", template)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

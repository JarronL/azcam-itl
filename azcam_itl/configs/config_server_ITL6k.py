"""
This is for the ST4500 6kx6k CCD in the ITL3 dewar.
"""

import os

import azcam
from azcam.tools.system import System
from azcam.tools.ds9display import Ds9Display
from azcam.tools.archon.controller_archon import ControllerArchon
from azcam.tools.archon.exposure_archon import ExposureArchon
from azcam.tools.tempcon_cryocon24 import TempConCryoCon24
from azcam.tools.tempcon import TempCon
from azcam.tools.instrument import Instrument

from azcam_itl.detectors import detector_sta4500
from azcam_itl.instruments.instrument_qb import InstrumentQB
from azcam_itl.instruments.instrument_eb import InstrumentEB

INSTRUMENT = None  # None, EB, QB

# ****************************************************************
# instrument
# ****************************************************************
if INSTRUMENT is None:
    instrument = Instrument()
elif INSTRUMENT == "EB":
    instrument = InstrumentEB()
    azcam.log(f"Instrument is Electron Bench")
elif INSTRUMENT == "QB":
    instrument = InstrumentQB()
    azcam.log(f"Instrument is Quantum Bench")

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArchon()
controller.camserver.port = 4242
controller.camserver.host = "10.0.2.12"  # ITL3

# ****************************************************************
# temperature controller
# ****************************************************************
if INSTRUMENT is None:
    tempcon = TempCon()
elif INSTRUMENT == "EB":
    tempcon = TempConCryoCon24()
    tempcon.host = "10.0.0.45"  # EB
    tempcon.control_temperature = -100.0
    tempcon.init_commands = [
        "input A:units C",
        "input B:units C",
        "loop 1:type pid",
        "input A:isenix 2",
        "input B:isenix 2",
        "loop 1:range mid",
        "loop 1:maxpwr 100",
    ]
elif INSTRUMENT == "QB":
    tempcon = TempConCryoCon24()
    tempcon.host = "10.0.0.44"  # QB
    tempcon.control_temperature = -100.0
    tempcon.init_commands = [
        "input A:units C",
        "input B:units C",
        "loop 1:type pid",
        "input A:isenix 2",
        "input B:isenix 2",
        "loop 1:range mid",
        "loop 1:maxpwr 100",
    ]

# ****************************************************************
# exposure
# ****************************************************************
filetype = "MEF"
exposure = ExposureArchon()
exposure.fileconverter.set_detector_config(detector_sta4500)
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.add_extensions = 1

# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_sta4500)

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_ITL6k.txt")
system = System("ITL3", template)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

import os

import azcam
from azcam.header import System
from azcam_server.tools.ds9display import Ds9Display
from azcam_server.tools.archon.controller_archon import ControllerArchon
from azcam_server.tools.archon.exposure_archon import ExposureArchon
from azcam_server.tools.tempcon_cryocon24 import TempConCryoCon24
from azcam_server.tools.archon.tempcon_archon import TempConArchon

from azcam_itl.detectors import (
    detector_sta4850,
    detector_sta4850_2amps_side,
    detector_sta4850_2amps_top,
)
from azcam_itl.instruments.instrument_qb import InstrumentQB
from azcam_itl.instruments.instrument_eb import InstrumentEB
from azcam_itl.instruments.instrument_arduino import InstrumentArduino

# optional configuration options
LVM_2amps = 0
LVM_science = 0
LVM_webserver = 0
EB = 1

# ****************************************************************
# instrument
# ****************************************************************
if EB:
    instrument = InstrumentEB()
    instrument.pressure_ids = [0, 1]
    azcam.log(f"Instrument is Electron Bench")
else:
    instrument = InstrumentQB()
    azcam.log(f"Instrument is Quantum Bench")

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArchon()
controller.camserver.port = 4242
if LVM_science:
    controller.camserver.host = "10.0.0.2"  # LVM cryostat
else:
    controller.camserver.host = "10.0.2.11"  # ITL2 for characterization

# ****************************************************************
# temperature controller
# ****************************************************************
if LVM_science:
    tempcon = TempConArchon()
    controller.heater_board_installed = 1
else:
    tempcon = TempConCryoCon24()
    tempcon.host = "10.131.0.10"  # QB
    tempcon.control_temperature = -110.0
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
if LVM_2amps:
    exposure.fileconverter.set_detector_config(detector_sta4850_2amps_side)
    exposure.fileconverter.set_detector_config(detector_sta4850_2amps_top)
else:
    exposure.fileconverter.set_detector_config(detector_sta4850)
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.add_extensions = 1

exposure.image.focalplane.gains = [
    1.0,
    1.0,
    1.0,
    1.0,
]
exposure.image.focalplane.rdnoises = [
    5.0,
    5.0,
    5.0,
    5.0,
]

# ****************************************************************
# detector
# ****************************************************************
if LVM_2amps:
    # exposure.set_detpars(detector_sta4850_2amps_side)
    exposure.set_detpars(detector_sta4850_2amps_top)
else:
    exposure.set_detpars(detector_sta4850)

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_ITL4k.txt")
system = System("ITL4k", template)

# ****************************************************************
# define display
# ****************************************************************
display = Ds9Display()

# ****************************************************************
# special
# ****************************************************************
# arduino = InstrumentArduino()
# azcam.db.tools["arduino"] = arduino

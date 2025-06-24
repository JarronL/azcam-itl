"""
Server config file for DESI.

Usage example:
C:\Python311\Scripts\ipython.exe ipython --ipython-dir=/data/ipython --profile azcamserver -i -m azcam_itl.server -- -system DESI -tempcon QB -instrument QB
"""

import os

import azcam
import azcam.exceptions
from azcam.header import System
from azcam.tools.archon.controller_archon import ControllerArchon
from azcam.tools.archon.exposure_archon import ExposureArchon
from azcam.tools.focus import Focus

from azcam_itl.detectors import detector_sta4150_4amp, detector_sta4150_2amp_left

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArchon()
controller.camserver.port = 4242
controller.camserver.host = "10.0.0.11"  # ITL2
# timing_file = os.path.join(azcam.db.datafolder, "archon", "DESI_ITL_final.ncf")
# controller.timing_file = timing_file

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureArchon()
exposure.fileconverter.set_detector_config(detector_sta4150_4amp)
filetype = "MEF"
exposure.filetype = exposure.filetypes[filetype]
exposure.image.filetype = exposure.filetypes[filetype]
exposure.add_extensions = 0
exposure.image.focalplane.gains = 4 * [2.8]
exposure.image.focalplane.rdnoises = 4 * [5.0]

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = azcam.db.tools["tempcon"]
tempcon.control_temperature = -110.0
tempcon.control_temperature_id = 3
tempcon.temperature_ids = [3, 1]  # ITL2
# Try to initialize the temperature controller
tempcon.initialize()
if tempcon.is_initialized:
    cid = tempcon.control_temperature_id
    ctemp_set = tempcon.control_temperature
    ctemp_sensor = tempcon.get_temperature(cid)
    channel_vals = ['A', 'B', 'C', 'D']
    print('')
    print(f"Control sensor temp on Ch {channel_vals[cid]}: {ctemp_sensor} C")
    print(f"Control sensor setpoint: {ctemp_set} C")
    print('')
else:
    azcam.exceptions.warning("WARNING: Temperature controller could not initialize!")

# ****************************************************************
# system header
# ****************************************************************
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_DESI.txt")
system = System("DESI", template)
system.set_keyword("DEWAR", "ITL2", "Dewar name")

# ****************************************************************
# detector
# ****************************************************************
exposure.set_detpars(detector_sta4150_4amp)

# ****************************************************************
# focus
# ****************************************************************
focus = Focus()
focus.initialize()

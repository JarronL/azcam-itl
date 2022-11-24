"""
Instrument server application on ITL ElectronBench.
"""

import azcam
from azcam_itl.instruments.instrument_eb import InstrumentEB

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentEB()
instrument.pressure_ids = [0]

# instrument.initialize()

azcam.db.tools["cmdserver"].logcommands = 1

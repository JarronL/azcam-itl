"""
Instrument server application on ITL ElectronBench.
"""

from azcam_itl.instruments.instrument_eb import InstrumentEB

import azcam

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentEB()
instrument.pressure_ids = [0]

# instrument.initialize()

azcam.db.tools["cmdserver"].logcommands = 1

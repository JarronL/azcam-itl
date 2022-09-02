"""
Instrument server application on ITL ElectronBench.
"""

from azcam_itl.instruments.instrument_eb_server import EBInstrumentServer

import azcam

# ****************************************************************
# instrument
# ****************************************************************
instrument = EBInstrumentServer()
# instrument.initialize()

azcam.db.tools["cmdserver"].logcommands = 1

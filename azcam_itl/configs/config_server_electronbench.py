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

azcam.db.cmdserver.logcommands = 1

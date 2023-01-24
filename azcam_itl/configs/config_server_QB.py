"""
Instrument server application on ITL QuantumBench.
"""

import azcam
from azcam_itl.instruments.instrument_qb import InstrumentQB

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentQB()

# instrument.initialize()

azcam.db.cmdserver.logcommands = 1

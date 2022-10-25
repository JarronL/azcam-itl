"""
Instrument server application on ITL QuantumBench.
"""

from azcam_itl.instruments.instrument_qb import InstrumentQB

import azcam

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentQB()

# instrument.initialize()

azcam.db.tools["cmdserver"].logcommands = 1

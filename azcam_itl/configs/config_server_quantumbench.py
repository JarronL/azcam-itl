"""
Instrument server application on ITL QuantumBench.
"""

import azcam
from azcam_itl.instruments.instrument_qb_server import InstrumentQBServer

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentQBServer()

azcam.db.tools["cmdserver"].logcommands = 1

print("Initializing instruments")
instrument.initialize()
print("Finished")

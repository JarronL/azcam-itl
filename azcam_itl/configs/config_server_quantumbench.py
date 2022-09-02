"""
Instrument server application on ITL QuantumBench.
"""

from azcam_itl.instruments.instrument_qb_server import InstrumentQBServer

import azcam

# ****************************************************************
# instrument
# ****************************************************************
instrument = InstrumentQBServer()

azcam.db.tools["cmdserver"].logcommands = 1

print("Initializing instruments")
instrument.initialize()
print("Finished")

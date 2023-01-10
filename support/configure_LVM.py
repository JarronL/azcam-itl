"""
Configuration script for LVM.
"""

import azcam
from azcam import db

db.systemname = "LVM"

db.LVM_2amps = 0
db.LVM_science = 0
db.LVM_webserver = 0
db.LVM_nearir = 0

if 0:
    if db.mode == "server":
        bench = azcam.utils.prompt("EB or QB (e or q", "q")
        if bench == "e":
            db.LVM_science = 1
        else:
            db.LVM_science = 0

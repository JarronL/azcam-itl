"""
Start azcamserver in Windows Terminal.

Arguments example:
  " -system LVM"
"""

import os
import sys

if len(sys.argv) > 1:
    args = " -- " + " ".join(sys.argv[1:])
else:
    #args = "-system LVM"
    args = ""

cl = f"poetry run start_server -- {args}"
os.system(cl)


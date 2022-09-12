"""
Start azcamconsole in virtual environment.

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

cl = f"poetry run start_console -- {args}"
os.system(cl)


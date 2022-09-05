"""
Start azcamserver in Windows Terminal using poetry.
Arguments example: " -system LVM"
"""

import os
import sys

wt = "wt --tabColor #009900"
poetry = "poetry run"
shell = f"ipython --profile azcamserver -i -m azcam_itl.server"

if len(sys.argv) > 1:
    args = " -- -- " + " ".join(sys.argv[1:])
else:
    args = ""

cl = f"{wt} {poetry} {shell} {args}"
os.system(cl)

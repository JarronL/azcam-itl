"""
Start azcamserver in Windows Terminal.

Arguments example:
  " -system LVM"
To run under poetry virtual environment, from working directory /azcam/azcam-itl/support/bin, do:
  "poetry run start_server.py"
"""

import os
import sys

wt = "wt -w azcam --title azcamserver --tabColor #990000"
shell = f"ipython --profile azcamserver -i -m azcam_itl.server"

if len(sys.argv) > 1:
    args = " -- " + " ".join(sys.argv[1:])
else:
    args = ""

cl = f"{wt} {shell} {args}"
os.system(cl)


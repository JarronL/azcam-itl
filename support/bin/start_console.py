"""
Start azcamconsole in Windows Terminal.

Arguments example:
  " -system LVM"
"""

import os
import sys

wt = "wt -w azcam --title AzCamConsole --tabColor #000099"
shell = f"ipython --profile azcamconsole -i -m azcam_itl.console"

if len(sys.argv) > 1:
    args = " -- " + " ".join(sys.argv[1:])
else:
    args = ""

cl = f"{wt} {shell} {args}"
os.system(cl)


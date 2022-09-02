"""
Start azcamconsole in Windows Terminal.
"""

import os
import sys

terminal = "wt -w azcam -p AzCamConsole --title AzCamConsole"
shell = f"ipython --profile azcamconsole -i -m azcam_itl.console"

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
if len(sys.argv) > 1:
    args = " -- " + " ".join(arguments)
else:
    args = ""

cl = f"{terminal} {shell}{args}"
os.system(cl)

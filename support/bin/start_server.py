"""
Start azcamserver in Windows Terminal.
"""

import os
import sys

wt = "wt -w azcam -p AzCamServer --title AzCamServer"
#ipython = f"ipython --profile azcamserver --TerminalInteractiveShell.term_title_format=Azcam -i -m azcam_itl.server"
ipython = f"ipython --profile azcamserver -i -m azcam_itl.server"

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
if len(sys.argv) > 1:
    args = " -- " + " ".join(arguments)
else:
    args = ""

cl = f"{wt} {ipython}{args}"
os.system(cl)

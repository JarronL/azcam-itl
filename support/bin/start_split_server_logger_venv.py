"""
Start azcamserver and logger in split Windows Terminal.
"""

import os
import sys

wt = "wt -w azcam --title AzCamServer --tabColor #990000 "

shell1 = f"\\azcam\\azcam-itl\\support\\bin\\start_server_venv1.bat"
shell2 = f"python \\azcam\\azcam-itl\\support\\bin\\start_ITL_logger.py"

if len(sys.argv) > 1:
    args = " -- " + " ".join(sys.argv[1:])
else:
    args = ""

cl = f"{wt} {shell1} -- {args}; split-pane -V --title AzCamLogger --tabColor #009900 {shell2}"
os.system(cl)

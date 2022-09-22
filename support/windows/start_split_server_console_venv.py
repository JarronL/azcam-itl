"""
Start azcamserver and azcamconsole in split Windows Terminal.
"""

import os
import sys
import time

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)

shell1 = f"\\azcam\\azcam-itl\\support\\bin\\start_server_venv1.bat"
shell2 = f"\\azcam\\azcam-itl\\support\\bin\\start_console_venv1.bat"

python = f"wt -w azcam -p AzCamServer --title AzCamServer --tabColor #990000"
cl = f"{python} {shell1} -- {args}"
os.system(cl)

time.sleep(1)

python = f"wt -w azcam split-pane -V -p AzCamConsole --title AzCamConsole --tabColor #000099"
cl = f"{python} {shell2} -- {args}"
os.system(cl)

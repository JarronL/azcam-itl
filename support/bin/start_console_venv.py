"""
Start azcamserver in Windows Terminal using azcam virtual environment.

Arguments example:
  " -system LVM"
"""

import os
import sys

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)

wt = "wt -w azcam --title AzCamConsole --tabColor #000099"
shell = f"\\azcam\\azcam-itl\\support\\bin\\start_console_venv1.bat"

cl = f"{wt} {shell} -- {args}"
os.system(cl)


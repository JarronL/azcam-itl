"""
Start azcamserver in Windows Terminal.

Arguments example:
  " -system LVM"
"""

import os
import sys

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)

wt = "wt -w azcam --title AzCamServer --tabColor #990000"
shell = f"\\azcam\\azcam-itl\\support\\bin\\start_server_venv1.bat"

cl = f"{wt} {shell} -- {args}"
os.system(cl)


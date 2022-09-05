"""
Start azcamserver and logger in different Windows Terminal tabs.
"""

import os
import sys

wt = "wt -w azcam --title AzCamServer"
poetry = "poetry run"
shell1 = f"ipython  --profile azcamserver -i -m azcam_itl.server"
shell2 = f"ipython  -m start_logger.py"

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
if len(sys.argv) > 1:
    args = " -- " + " ".join(arguments)
else:
    #args = " -system LVM"  # example
    args = ""

cl = f"{wt} {poetry} {shell1} -- -- {args}; split-pane -V  --tabColor #990000 --title AzCam {poetry} {shell2}"
os.system(cl)

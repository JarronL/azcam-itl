"""
Start azcamserver and logger in different Windows Terminal tabs.
"""

import os
import sys

wt = "wt -w azcam --title AzCamServer --tabColor #990000 "
poetry = "poetry run"
shell1 = f"ipython --profile azcamserver -i -m azcam_itl.server"
shell2 = f"python -m start_ITL_logger.py"

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
if len(sys.argv) > 1:
    args = " -- " + " ".join(arguments)
else:
    #args = " -system LVM"  # example
    args = ""

cl = f"{wt} {poetry} {shell1} -- -- {args}; split-pane -V --title AzCam --tabColor #009900 {poetry} {shell2}"
os.system(cl)

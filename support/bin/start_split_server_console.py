"""
Start azcamserver and azcamconsole in different Windows Terminal tabs.
"""

import os
import sys

wt = "wt -w azcam"
poetry = "poetry run"
shell1 = f"ipython  --profile azcamserver -i -m azcam_itl.server"
shell2 = f"ipython --profile azcamconsole -i -m azcam_itl.console"

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
if len(sys.argv) > 1:
    args = " -- " + " ".join(arguments)
else:
    #args = " -system LVM"  # example
    args = ""

cl = f"{wt} --title AzCamServer --tabColor #990000 {poetry} {shell1} -- -- {args}; split-pane -V --title AzCamConsole --tabColor #000099 {poetry} {shell2} -- -- {args}"
os.system(cl)

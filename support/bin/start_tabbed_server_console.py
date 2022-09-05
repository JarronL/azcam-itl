"""
Start azcamserver and azcamconsole in different Windows Terminal tabs.
"""

import os
import sys
import time

poetry = "poetry run"
poetry = ""

python = f"wt -w azcam -p AzCamServer --title AzCamServer --tabColor #990000 {poetry} ipython --profile azcamserver -i "
arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)
cl = f"{python} -m azcam_itl.server -- {args}"
os.system(cl)

time.sleep(1)

python = f"wt -w azcam new-tab -p AzCamConsole --title AzCamConsole --tabColor #000099 {poetry} ipython --profile azcamconsole -i "
arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)
cl = f"{python} -m azcam_itl.console -- {args}"
os.system(cl)

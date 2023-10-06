"""
Start azcamserver and azcamconsole in split Windows Terminal.
"""

import os
import sys
import time

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)

python = f"wt -w azcam -p AzCamServer --title AzCamServer --tabColor 990000 ipython --profile azcamserver -i "
cl = f"{python} -m azcam_itl.server -- {args}"
os.system(cl)

time.sleep(1)

python = f"wt -w azcam split-pane -V -p AzCamConsole --title AzCamConsole --tabColor 000099 ipython --profile azcamconsole -i "
cl = f"{python} -m azcam_itl.console -- {args}"
os.system(cl)

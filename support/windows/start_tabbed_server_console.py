"""
Start azcamserver and azcamconsole in different tabs Windows Terminal.
"""

import os
import sys
import time

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)

# cmd = f"wt -w azcam -p AzCamServer --title AzCamServer --tabColor 990000 ipython --profile azcamserver -i -m azcam_itl.server -- {args}"
# print(cmd)
# os.system(cmd)

# time.sleep(1)

cmd = f"wt -w azcam new-tab -p AzCamConsole --title AzCamConsole --tabColor 000099 ipython --profile azcamconsole -i -m azcam_itl.console -- {args}"
cmd = "wt ipython --profile azcamconsole -i -m azcam_itl.console"
print(cmd)
os.system(cmd)

"""
Start azcamserver and azcamconsole in different Windows Terminal tabs.
"""

import os
import sys
import time

python = f"wt -w azcam -p AzCamServer --tabColor #990000 ipython --profile azcamserver --TerminalInteractiveShell.term_title_format=AzCamServer -i "
arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)
cl = f"{python} -m azcam_itl.server -- {args}"
os.system(cl)

time.sleep(1)

python = f"wt -w azcam new-tab -p AzCamConsole --tabColor #000099 ipython --profile azcamconsole --TerminalInteractiveShell.term_title_format=AzCamConsole -i "
arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)
cl = f"{python} -m azcam_itl.console -- {args}"
os.system(cl)

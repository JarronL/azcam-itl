"""
Start azcamserver and azcamconsole in different Windows Terminal tabs.
"""

import os
import sys

profile1 = "azcamserver"
profile2 = "azcamconsole"
python1 = f"-p AzCamServer --tabColor #000099 ipython --profile {profile1} -i -m azcam_itl.server"
python2 = f"-p AzCamConsole ipython --profile {profile2} --TerminalInteractiveShell.term_title_format=Azcam -i -m azcam_itl.console"

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
if len(arguments) > 0:
    args = "-- " + " ".join(arguments)
else:
    args = ""

cl = f"wt -w azcam {python1} {args}; split-pane -V {python2} {args}"
os.system(cl)

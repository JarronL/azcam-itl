"""
Start azcamserver and azcamconsole in different Windows panes.
"""

import os
import sys

python1 = f"-p AzCamServer --tabColor #000099 ipython --profile azcamserver --TerminalInteractiveShell.term_title_format=AzCam -i -m azcam_itl.server"
python2 = f"-p AzCamServer python -m start_logger.py"

arguments = sys.argv[1:] if len(sys.argv) > 1 else [""]
args = " ".join(arguments)

cl = f"wt -- {args}; split-pane -V {python2} -- {args}"
os.system(cl)

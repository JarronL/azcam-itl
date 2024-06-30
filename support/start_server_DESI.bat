"""
Python process start file
"""

import subprocess

OPTIONS = "-system DESI"
CMD = f"ipython --profile azcamserver -i -m azcam_itl.server -- {OPTIONS}"

p = subprocess.Popen(
    CMD,
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

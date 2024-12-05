"""
Python process start file
"""

import subprocess

OPTIONS = "-system DESI -instrument QB"
CMD = f"ipython ipython --ipython-dir=/data/ipython --profile azcamserver -i -m azcam_itl.server -- {OPTIONS}"

p = subprocess.Popen(
    CMD,
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

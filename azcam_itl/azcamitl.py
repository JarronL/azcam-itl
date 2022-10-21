"""
Common start script for azcam_itl
Runs azamserver or azcamconsole in Ipython under Windows or Linux.
"""

import os
import sys

CONSOLE = False
SERVER = True  # default

args=sys.argv[1:]

if "-console" in args:
    CONSOLE = True
    SERVER = False
if "-server" in args:
    CONSOLE = False
    SERVER = True

if os.name == "posix":
    AZCAM_DATAROOT="~/data"
    os.environ['AZCAM_DATAROOT']=AZCAM_DATAROOT
    print(f'AzCam data root is {AZCAM_DATAROOT}')

    if SERVER:
        command = f"ipython --profile azcamserver -i -c \"import azcam_itl.server ; from azcam.cli import *\" -- {' '.join(args)}"
    elif CONSOLE:
        command = f"ipython --profile azcamconsole -i -c \"import azcam_itl.console ; from azcam.cli import *\" -- {' '.join(args)}"
    os.system(command)

else:
    AZCAM_DATAROOT='/data'
    os.environ['AZCAM_DATAROOT']=AZCAM_DATAROOT

    if SERVER:
        cmds = [
            "ipython --profile azcamserver -i -c" ,
            "\"import azcam_itl.server ; from azcam.cli import *\"",
            f" -- {' '.join(args)}",
        ]
    if CONSOLE:
        cmds = [
            "ipython --profile azcamconsole -i -c" ,
            "\"import azcam_itl.console ; from azcam.cli import *\"",
            f" -- {' '.join(args)}",
        ]
    
    command = " ".join(cmds)
    os.system(command)

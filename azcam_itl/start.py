"""
Start script for azcam_itl package.
Runs azamserver or azcamconsole

Usage Example:
>> ipython -m azcam_itl.start -i -- -console -system DESI
"""

import sys

# set defaults
CONSOLE = False
SERVER = True

args = sys.argv[1:]

if "-console" in args:
    CONSOLE = True
    SERVER = False
if "-server" in args:
    CONSOLE = False
    SERVER = True

if SERVER:
    import azcam_itl.server_itl
    from azcam.cli import *

elif CONSOLE:
    import azcam_itl.console_itl
    from azcam.cli import *

"""
Startup command for azcam-itl
Usage:
  python itl.py -console
  python itl.py -server -system xxx

For installations, this is the "itl" command.
"""

import os
import sys


def main():

    args = sys.argv[1:]

    PACKAGE = "azcam_itl"
    STARTMOD = "itl_start"

    if "-console" in args:
        tabColor = "#000099"
        tabTitle = "azcamconsole"
    elif "-server" in args:
        tabColor = "#990000"
        tabTitle = "azcamserver"
    else:
        # assume console mode
        tabColor = "#000099"
        tabTitle = "azcamconsole"

    if os.name == "posix":
        cmds = [
            f". ~/azcam/venvs/azcam/bin/activate ; python3 -m {PACKAGE}.{STARTMOD}",
            f"{' '.join(args)}",
        ]
    else:
        cmds = [
            f"wt -w azcam --suppressApplicationTitle=True --title {tabTitle} --tabColor {tabColor}",
            "cmd /k",
            f'"/azcam/venvs/azcam/Scripts/activate.bat & python -m {PACKAGE}.{STARTMOD}"',
            f"{' '.join(args)}",
        ]
    command = " ".join(cmds)
    os.system(command)


if __name__ == "__main__":
    main()

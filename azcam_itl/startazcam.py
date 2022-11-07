"""
Startup command for azcam
Usage:
  python azcam -package azcam-itl -console

For installations, this is the "azcam" command.
"""

import os
import sys

import azcam


def main():

    args = sys.argv[1:]

    try:
        i = sys.argv.index("-startup")  # underscore not hypen
        startmod = sys.argv[i + 1]
    except ValueError:
        raise azcam.AzcamError("No starting package specified")

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
            f". ~/azcam/venvs/azcam/bin/activate ; python3 -m {startmod}",
            f"{' '.join(args)}",
        ]
    else:
        cmds = [
            f"wt -w azcam --suppressApplicationTitle=True --title {tabTitle} --tabColor {tabColor}",
            "cmd /k",
            f'"/azcam/venvs/azcam/Scripts/activate.bat & python -m {startmod}"',
            f"{' '.join(args)}",
        ]
    command = " ".join(cmds)
    os.system(command)


if __name__ == "__main__":
    main()

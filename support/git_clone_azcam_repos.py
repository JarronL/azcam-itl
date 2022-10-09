# clone repos from github

import os
import subprocess

packages = [
    "azcam",
    "azcam-arc",
    "azcam-archon",
    "azcam-ascom",
    "azcam-cryocon",
    "azcam-ds9",
    "azcam-ds9-winsupport",
    "azcam-expstatus",
    "azcam-fastapi",
    "azcam-focus",
    "azcam-imageserver",
    "azcam-mag",
    "azcam-monitor",
    "azcam-observe",
    "azcam-scripts",
    "azcam-testers",
    "azcam-tool",
    "azcam-webtools",
    "azcam-itl",
    "azcam-90prime",
    "azcam-bcspec",
    "azcam-bluechan",
    "azcam-lbtguiders",
    "azcam-mont4k",
    "azcam-soguiders",
    "azcam-vatt4k",
    "azcam-vattspec",
    "azcam-osu4k",
    "azcam-pepsi",
]
github_root = "https://github.com/mplesser/"

for repo in packages:
    r = os.path.join(".", os.path.abspath(repo))
    if os.path.exists(r):
        print(f"{r} already exists and will not be cloned")
        continue
    else:
        print(f"{r} will be cloned")

    if 1:
        try:
            s = f"git clone {github_root}{repo}.git"
            p = subprocess.Popen(s, shell=True)
            p.wait()
        except Exception as e:
            print(e)

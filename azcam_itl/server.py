"""
azcam server script for ITL systems.

Usage: python -m azcam_itl.server
"""

import azcam_itl.server_itl

# CLI commands - -m command line flags brings these into CLI namespace
from azcam.cli import *

del azcam.cli

"""
start_logger.py
"""

import os
import socketserver

wt = "wt --title AzCamLogger"
poetry = "poetry run"
shell = f"python -m support.bin.itl_logger"

cl = f"{wt} {poetry} {shell}"
os.system(cl)

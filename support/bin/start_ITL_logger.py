"""
azcam_itl logger

To run under a virtual environment, from working directory /azcam/azcam-itl/support/bin, do:
  "poetry run start_ITL_logger.py"
"""


import os
import socketserver
from azcam.logging_server_tcp import LoggingStreamHandler

port = 2404

print(f"Logging server running on port {port}")
logging_server = socketserver.TCPServer(("localhost", port), LoggingStreamHandler)
logging_server.serve_forever()

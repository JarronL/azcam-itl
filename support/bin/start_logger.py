"""
start_logger.py
"""

import socketserver

from azcam.logging_server_tcp import LoggingStreamHandler


def start_logger(port: int = 2404):

    # set window title
    # ctypes.windll.kernel32.SetConsoleTitleW("azcamlogger")
    print(f"Logging server running on port {port}")
    logging_server = socketserver.TCPServer(("localhost", port), LoggingStreamHandler)
    logging_server.serve_forever()


start_logger()

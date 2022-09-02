import sys
import subprocess


def start_tcp_logserver():

    s = f'python -c "from azcam.tools.logging_servers import start_and_serve_tcp; start_and_serve_tcp()"'
    subprocess.Popen(s, creationflags=subprocess.CREATE_NEW_CONSOLE)


if __name__ == "__main__":
    args = sys.argv[1:]
    start_tcp_logserver(*args)

@echo off

ipython.exe --profile azcamserver --TerminalInteractiveShell.term_title_format=filters_eb -i -m azcam_itl.servers.filters_server_eb -- -port 2406

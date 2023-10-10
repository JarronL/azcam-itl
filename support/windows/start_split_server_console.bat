@echo off

Rem Start azcamserver and azcamconsole in split Windows Terminal panes.

SET OPTIONS= --size 180,30 --pos 20,750

wt -w azcam %OPTIONS% -p AzCamServer --title AzCamServer ipython --profile azcamserver -i -m azcam_itl.server -- %*

timeout 2 > NUL

wt -w azcam split-pane -V -p AzCamConsole --title AzCamConsole ipython --profile azcamconsole -i -m azcam_itl.console -- %*

@echo off

Rem Start azcamserver and azcamconsole in split Windows Terminal panes.

Rem May need to run as admin on some systems.

SET OPTIONS= --size 180,30 --pos 20,750

wt -w azcam %OPTIONS% --title AzCamServer ipython --profile azcamserver -i -m azcam_itl.server -- %*

timeout 2 > NUL

wt -w azcam split-pane -V --title AzCamConsole ipython --profile azcamconsole -i -m azcam_itl.console -- %*

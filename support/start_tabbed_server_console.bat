@echo off

Rem Start azcamserver and azcamconsole in different tabs with Windows Terminal.
Rem May need to run as admin on some systems.
Rem Best practice is to copy this file to Desktop and edit size and position.

SET OPTIONS= --size 120,40 --pos 20,550

wt -w azcam %OPTIONS% --title AzCamServer ipython --profile azcamserver -i -m azcam_itl.server -- %*

timeout 2 > NUL

wt -w azcam new-tab --title AzCamConsole ipython --profile azcamconsole -i -m azcam_itl.console -- %*

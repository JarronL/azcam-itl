@echo off
Rem Start azcamserver and azcamconsole in different tabs Windows Terminal.

wt -w azcam -p AzCamServer --title AzCamServer --tabColor "#990000" ipython --profile azcamserver -i -m azcam_itl.server -- %1 %2 %3 %4 %5 %6 %7 %8 %9

timeout /t 1 /nobreak

wt -w azcam new-tab -p AzCamConsole --title AzCamConsole --tabColor "#000099" ipython --profile azcamconsole -i -m azcam_itl.console -- %1 %2 %3 %4 %5 %6 %7 %8 %9

pause

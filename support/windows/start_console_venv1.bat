@echo off

call C:\data\venvs\azcam\Scripts\activate.bat

ipython -i -m azcam_itl.console %1 %2 %3 %4 %5 %6

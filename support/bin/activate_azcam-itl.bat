@echo off
rem run azcam-itl code in a Windows Terminal using virtual environment

rem args are: mode system venv
rem example: server LVM venv

rem get mode
if %1 EQU server (
    SET profile=azcamserver
    SET mode=server
)
if %1 EQU console (
    SET profile=azcamconsole 
    SET mode=console
)
IF [%3] == [] GOTO RUN
if %3 EQU venv (
    call C:\data\venvs\azcam\Scripts\activate.bat
)

:RUN
rem open wt
wt -p %profile% ipython --profile %profile% -i -m azcam_itl.%mode% -- -system %2

@echo off

echo Updating pip
C:\data\venvs\azcam\Scripts\python.exe -m pip install --upgrade pip

echo Installing in edit mode
cd ..\..
pip install -e .

pause

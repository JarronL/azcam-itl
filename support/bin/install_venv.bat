@echo off

wt \data\venvs\azcam\Scripts\activate.bat

C:\data\venvs\azcam\Scripts\python.exe -m pip install --upgrade pip

cd ..\..
pip install -e .

pause

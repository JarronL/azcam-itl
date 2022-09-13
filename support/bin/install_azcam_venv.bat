@echo off

echo Activating azcam VE
call \data\venvs\azcam\Scripts\activate.bat

echo Updating pip
C:\data\venvs\azcam\Scripts\python.exe -m pip install --upgrade pip

echo Installing azcam code in edit mode
cd ..\..\..

pip install -e azcam
pip install -e azcam-monitor
pip install -e azcam-fastapi
pip install -e azcam-arc
pip install -e azcam-archon
pip install -e azcam-ascom
pip install -e azcam-cryocon
pip install -e azcam-ds9
pip install -e azcam-expstatus
pip install -e azcam-focus
pip install -e azcam-imageserver
pip install -e azcam-mag
pip install -e azcam-observe
pip install -e azcam-scripts
pip install -e azcam-testers
pip install -e azcam-webtools

pip install -e azcam-itl

pause

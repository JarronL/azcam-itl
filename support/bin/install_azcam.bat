@echo off

echo Updating pip
python.exe -m pip install --upgrade pip

echo Installing in edit mode
cd ..\..
pip install -e .

pause

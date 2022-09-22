@echo off

SET GITHUB=https://github.com/mplesser

echo Cloning azcam repos
cd ..\..\..

git clone %GITHUB%/azcam
git clone %GITHUB%/azcam-monitor
git clone %GITHUB%/azcam-fastapi
git clone %GITHUB%/azcam-arc
git clone %GITHUB%/azcam-archon
git clone %GITHUB%/azcam-ascom
git clone %GITHUB%/azcam-cryocon
git clone %GITHUB%/azcam-ds9
git clone %GITHUB%/azcam-expstatus
git clone %GITHUB%/azcam-focus
git clone %GITHUB%/azcam-imageserver
git clone %GITHUB%/azcam-mag
git clone %GITHUB%/azcam-observe
git clone %GITHUB%/azcam-scripts
git clone %GITHUB%/azcam-testers
git clone %GITHUB%/azcam-webtools

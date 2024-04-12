@echo off

start/min "azcammonitor" python -m azcam.monitor -- -configfile "/azcam/azcam-itl/support/parameters_monitor_itl.ini"

rem start "azcammonitor" ipython -m azcam.monitor -i -- -configfile "/azcam/azcam-itl/support/parameters_monitor_itl.ini"

rem ipython -m azcam.monitor -i -- -configfile "/azcam/azcam-itl/support/parameters_monitor_itl.ini"

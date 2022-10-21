# install script for azcam packages
# execute from package root folder

import os

# get root for azcam (change to CLI)
if os.name == "posix":
    AZCAM_ROOT = os.path.join(os.environ["HOME"],"azcam")
    PYTHON = "python3"
else:
    AZCAM_ROOT = "/azcam"
    PYTHON = "python"

# check for and create VE if necessary
ve = os.path.join(AZCAM_ROOT,"venvs","azcam")
if not os.path.exists(ve):
    print(f"Creating azcam virtual environment {ve}")
    os.makedirs(ve)
    os.system(f'{PYTHON} -m venv {ve}')

# install 
if os.name == "posix":
    commands = [
        'sudo apt-get install python3-tk',
        f'. {AZCAM_ROOT}/venvs/azcam/bin/activate ; pip install -e .',
    ]

    for command in commands:
        os.system(command)

else:
    commands = [
        f'{AZCAM_ROOT}/venvs/azcam/scripts/activate.bat ',
        f'& pip install -e .',
    ]

    command = ''
    for cmd in commands:
        command = command + cmd
    os.system(command)

# finish
print("Finished")

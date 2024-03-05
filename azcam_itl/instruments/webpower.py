import os
import subprocess

import keyring

import azcam
import azcam.exceptions


class WebPowerClass(object):
    """
    Defines the web power switch interface.
    """

    def __init__(self):

        # server and user for keyring password
        self.service_name = ""
        self.username = ""
        self.hostname = ""

        f1 = os.path.join(os.path.dirname(__file__), "UU.W32.exe")
        f1 = os.path.normpath(f1)
        if os.path.exists(f1):
            self.batchfile = f1
            self.batchfile_folder = os.path.dirname(self.batchfile)
        else:
            raise azcam.exceptions.AzCamError("could not find outlet control program")

    def initialize(self):
        """
        Initialize power switch.
        """

        return

    def turn_on(self, OutletNumber):
        """
        Turns ON an outlet.
        """

        pw = keyring.get_password(self.service_name, self.username)

        s = f"{self.batchfile} {self.hostname} {self.username}:{pw} {OutletNumber}on"
        with open(os.devnull, "w") as fnull:
            p1 = subprocess.Popen(
                s, shell=True, cwd=self.batchfile_folder, stdout=fnull, stderr=fnull
            )
            p1.wait()

        return

    def turn_off(self, OutletNumber):
        """
        Turns OFF an outlet.
        """

        pw = keyring.get_password(self.service_name, self.username)

        s = f"{self.batchfile} {self.hostname} {self.username}:{pw} {OutletNumber}off"
        with open(os.devnull, "w") as fnull:
            p1 = subprocess.Popen(
                s, shell=True, cwd=self.batchfile_folder, stdout=fnull, stderr=fnull
            )
            p1.wait()

        return

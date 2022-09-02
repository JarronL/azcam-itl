import threading
import time

import azcam


class AutoFill(object):
    """
    LN2 autofill class.
    """

    def __init__(self):

        self.autofillPort = 1  # web power switch outlet
        self.autofillDelay = 1.0  # loop time (sec)
        self.autofillTemperature = -999.0  # temperature for autofill activation
        self.autofillSwitch = 0  # flag for autofill switch (LN2 delivery)
        self.autofillState = 0  # flag for autostate (loop on or off)

    # ************************************************************
    # LN2 Autofill
    # ************************************************************
    def set_autofill_state(self, State=0):
        """
        Sets autofill state: 1 or 0.
        """

        State = int(State)

        if State == 0:
            self.power.turn_off(self.autofillPort)
            azcam.log("stopping autofill loop")
            self.autofillState = 0

        elif State == 1:
            azcam.log("starting autofill loop")
            self.autofillState = 1
            self.autofillThread = threading.Thread(target=self.autofill_loop, args=[])
            self.autofillThread.start()

        return

    def set_autofill_temperature(self, Temperature=-999):
        """
        Set the single dewar temperature when autofill is turned OFF.
        """

        self.autofillTemperature = Temperature

        return

    def autofill_loop(self):
        """
        Loop routine to run autofill, usually started in a thread from autofill() method.
        """

        currentswitch = self.autofillSwitch

        while 1:

            if not self.autofillState:
                break
            # get dewtemp
            try:
                reply = azcam.db.tools["tempcon"].get_temperatures()
            except Exception as message:
                try:
                    azcam.log("stopping autofill loop: %s" % message)
                    self.autofillThread.stop()
                except Exception:
                    pass
                return

            # compare temp
            dewtemp = reply[1]
            if dewtemp > self.autofillTemperature:
                self.autofillSwitch = 1
            else:
                self.autofillSwitch = 0

            # toggle
            if currentswitch != self.autofillSwitch:
                if self.autofillSwitch:
                    reply = self.power.turn_on(self.autofillPort)
                else:
                    reply = self.power.turn_off(self.autofillPort)
                currentswitch = self.autofillSwitch

            # delay
            time.sleep(self.autofillDelay)

        return

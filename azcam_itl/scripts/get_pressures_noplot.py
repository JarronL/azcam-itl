import datetime
import sys
import time
from statistics import mean

import azcam


class GetPressures(object):
    """
    Get instrument pressures and plot using matplotlib animation.
    """

    def __init__(self) -> None:
        self.pressure_now = 0
        self.times = []
        self.pressures = []
        self.timestart = None
        self.delay = 0.0
        self.start_offset = 0
        self.xs = []
        self.y0 = []
        self.y1 = []

    def setup(self):
        self.init()

    def init(self):
        """
        Initialize.
        """

        data_txt_hdr = "Seconds\tPressure\tTime"
        self.datafile = open("Pressure.txt", "a+")
        self.datafile.write("# " + data_txt_hdr + "\n")

        self.timestart = datetime.datetime.now()

        return

    def update(self):
        """
        Update pressures.
        """

        timenow = datetime.datetime.now()
        s = str(timenow)
        secs = timenow - self.timestart
        secs1 = secs.total_seconds()
        secs1 += self.start_offset

        # get pressures
        pressures = azcam.db.tools["instrument"].get_pressures()

        # get tempeatures
        # temps = azcam.db.tools["tempcon"].get_temperatures()
        # camtemp, dewtemp = temps[0:2]

        self.xs.append(datetime.datetime.now().strftime("%H:%M:%S"))
        self.y0.append(pressures[0])
        if len(pressures) == 2:
            self.y1.append(pressures[1])
            s = f"{secs1:.0f}\t{pressures[0]:1.2e}\t{pressures[1]:1.2e}\t{timenow}"
        else:
            s = f"{secs1:.0f}\t{pressures[0]:1.2e}\t{timenow}"
            # s = f"{secs1:.0f}\t{pressures[0]:1.2e}\t{pressures[1]:1.2e}\t{timenow}\t{dewtemp:.1f}\t{camtemp:.1f}"
        azcam.log(s)
        self.datafile.write(s + "\n")
        self.datafile.flush()

        if azcam.utils.check_keyboard() == "q":
            self.datafile.close()
            status = 1
        else:
            status = 0

        return status

    def run(self):

        self.setup()

        while 1:
            if self.update():
                break
            time.sleep(self.delay)

        return


def get_pressures_noplot(delay: float = 0.0, start_offset=0):
    """
    Read and plot pressure using matplotlib animation.
    """

    get_pressures_realtime = GetPressures()
    get_pressures_realtime.delay = delay
    get_pressures_realtime.start_offset = start_offset
    anim = get_pressures_realtime.run()

    return anim

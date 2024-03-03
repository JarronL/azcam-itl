import datetime
import sys
import time
from statistics import mean

import azcam
import azcam.utils

import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import MaxNLocator


class GetPressures(object):
    """
    Get instrument pressures and plot using matplotlib animation.
    """

    def __init__(self) -> None:
        self.pressure_now = 0
        self.times = []
        self.pressures = []
        self.ax = None
        self.timestart = None
        self.lines = None
        self.delay = 0.0

    def setup(self):
        self.fig, self.ax = azcam.plot.plt.subplots()
        self.fig.subplots_adjust(left=0.18, bottom=0.20, right=0.95, top=0.9)
        self.ax.grid(1)

        plt.title("Measured Pressure")
        plt.ylabel("Pressure [Torr]")
        plt.xlabel("Time")
        plt.xticks(rotation=45, ha="right")

        (self.artist,) = self.ax.plot([], [])

        return (self.artist,)

    def init(self):
        """
        Initialize animation
        """

        data_txt_hdr = "Seconds\tPressure\tTime"
        self.datafile = open("Pressure.txt", "a+")
        self.datafile.write("# " + data_txt_hdr + "\n")

        data_txt_hdr = "Seconds\tPressure\tTime"
        self.datafile = open("Pressure.txt", "a+")
        self.datafile.write("# " + data_txt_hdr + "\n")

        self.timestart = datetime.datetime.now()

        return (self.artist,)

    def update(self, i, xs, ys):
        """
        Periodically called from FuncAnimation.
        """

        timenow = datetime.datetime.now()
        s = str(timenow)
        secs = timenow - self.timestart
        secs1 = secs.total_seconds()

        # get new pressure each time animate is called
        plist = []
        for _ in range(5):
            plist.append(azcam.db.tools["instrument"].get_pressures()[0])
        p = mean(plist)

        xs.append(dt.datetime.now().strftime("%H:%M:%S"))
        ys.append(p)

        self.ax.plot(xs, ys)
        # self.ax.semilogy(xs, ys)

        self.ax.xaxis.set_major_locator(MaxNLocator(20))

        print(f"{secs1:.0f}\t\t{p:.2e}\t\t{s}")
        s = f"{secs1:.0f}\t\t{p:1.2e}\t{timenow}"
        self.datafile.write(s + "\n")

        if azcam.utils.check_keyboard() == "q":
            self.datafile.close()
            self.ani.pause()
            print("Paused plotting script and wote data file")

        return (self.artist,)

    def run(self):

        self.setup()
        # self.init()

        anim = animation.FuncAnimation(
            self.fig,
            self.update,
            init_func=self.init,
            fargs=(self.times, self.pressures),
            interval=int(self.delay * 1000),
            blit=False,
        )
        plt.show()

        return anim


def get_pressures_realtime(delay: float = 0.0):
    """
    Read and plot pressure using matplotlib animation.
    """

    get_pressures_realtime = GetPressures()
    get_pressures_realtime.delay = delay
    anim = get_pressures_realtime.run()

    return anim

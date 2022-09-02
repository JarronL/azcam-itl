import datetime
import time
from statistics import mean
import azcam

import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


class PlotPressures(object):
    """
    Get instrument pressures and plot.
    """

    def __init__(self) -> None:
        self.pressure_now = 0
        self.times = []
        self.pressures = []
        self.ax = None
        self.timestart = None
        self.lines = None
        self.delay = 0.0

        self.xs = []
        self.ys = []
        self.ys1 = []
        self.ys2 = []

        self.datafilename = "pressure.txt"
        plt.interactive(1)

    def setup(self):
        """
        Setup plot and data output header.
        """

        self.fig, self.ax = azcam.plot.plt.subplots()
        self.fig.subplots_adjust(left=0.18, bottom=0.20, right=0.95, top=0.9)
        self.ax.grid(1)
        self.ax.xaxis.set_major_locator(MaxNLocator(20))

        plt.title("Measured Pressure")
        plt.ylabel("Pressure [Torr]")
        plt.xlabel("Time")
        plt.xticks(rotation=45, ha="right")
        plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

        plt.ylim(1e-7, 1e-5)

        self.ax.plot([], [])

        print("Press spacebar anytime to write out data file")

        data_txt_hdr = "Seconds\tPressure\tTime"
        self.datafile = open(self.datafilename, "a+")
        self.datafile.write("# " + data_txt_hdr + "\n")

        data_txt_hdr = "Seconds\tPressure\tTime"
        self.datafile.write("# " + data_txt_hdr + "\n")

        self.timestart = datetime.datetime.now()
        self.lasttime = self.timestart

        azcam.plot.move_window(1, 100, 100)
        azcam.plot.update()

        # ignore first reading
        try:
            azcam.db.tools["instrument"].get_pressures()
        except Exception:
            pass

        return

    def update(self):
        """
        Periodically called get data and update plot.
        """

        timenow = datetime.datetime.now()
        s = str(timenow)
        secs = timenow - self.timestart
        secs1 = secs.total_seconds()

        # get new pressures
        try:
            pressures = azcam.db.tools["instrument"].get_pressures()
        except Exception as e:
            print(e)
            return

        numplots = len(pressures)

        self.ys.append(pressures[0])

        if numplots > 1:
            self.ys1.append(pressures[1])

        if numplots > 2:
            self.ys2.append(pressures[2])

        if 0:
            self.xs.append(dt.datetime.now().strftime("%H:%M:%S"))
        else:
            self.xs.append(secs1)

        # self.ax.cla()
        if self.linear:
            self.ax.plot(self.xs, self.ys, "b.")
            if numplots > 1:
                self.ax.plot(self.xs, self.ys1, "r.")
            if numplots > 2:
                self.ax.plot(self.xs, self.ys2, "g.")
        else:
            self.ax.semilogy(self.xs, self.ys, "b.")
            if numplots > 1:
                self.ax.semilogy(self.xs, self.ys1, "r.")
            if numplots > 2:
                self.ax.semilogy(self.xs, self.ys2, "g.")

        delta = (timenow - self.lasttime).total_seconds()

        azcam.log(f"{secs1:.0f}\t\t{[f'{p:1.2e}' for p in pressures]}\t\t{s}")
        s = f"{secs1:.0f}\t\t{[f'{p:1.2e}' for p in pressures]}\t\t{timenow}"

        if not self.datafile.closed:
            self.datafile.write(s + "\n")
        else:
            self.datafile = open(self.datafilename, "a+")
            self.datafile.write(s + "\n")
            print(f"reopened {self.datafilename=}")

        azcam.plot.update()

        self.lasttime = timenow

        return

    def run(self, linear):

        self.setup()

        self.linear = linear

        while 1:

            self.update()
            if azcam.utils.check_keyboard() == " ":
                self.datafile.close()
                print("Wrote data file")
            time.sleep(self.delay)

        return


def plot_pressures(delay: float = 0.0, linear=1):
    """
    Read and plot pressure.
    """

    plot_pressures = PlotPressures()
    plot_pressures.delay = delay
    plot_pressures.run(linear)

    return

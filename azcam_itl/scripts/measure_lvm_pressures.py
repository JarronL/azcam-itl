import datetime
import time
from statistics import mean
import azcam

import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


class MeasureLvmPressures(object):
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
        self.loop_delay = 30 * 60   # time between measurements
        self.warmup_delay = 3 * 60  # time to warmup after power on
        self.linear = 1

        self.xs = []
        self.ys = []
        self.ys1 = []
        self.ys2 = []

        self.datafilename = "pressure_lvm.txt"
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

        self.ax.plot([], [])

        data_txt_hdr = "Seconds\tPressure\tTime"
        self.datafile = open(self.datafilename, "a+")
        self.datafile.write("# " + data_txt_hdr + "\n")

        data_txt_hdr = "Seconds\tPressure\tTime"
        self.datafile.write("# " + data_txt_hdr + "\n")

        self.timestart = datetime.datetime.now()
        self.lasttime = self.timestart

        azcam.plot.move_window(1, 100, 100)
        azcam.plot.update()

        return

    def get_pressures(self):
        """
        Power on, warmup, measure pressures, power off.
        """

        instrument = azcam.db.tools["instrument"]
        server = azcam.db.tools["server"]

        # outlet 1 is Agilent on lid
        # outlet 2 is MKS on elbow
        # instrument.poweraux.turn_on(1)
        server.command("instrument.poweraux.turn_on 1")
        server.command("instrument.poweraux.turn_on 2")
        time.sleep(self.warmup_delay)

        if 1:
            pressures = instrument.get_pressures()
        else:
            pressures = [1.11e-1, 2.22e-2]
        self.numplots = len(pressures)

        # instrument.poweraux.turn_off(1)
        server.command("instrument.poweraux.turn_off 1")
        server.command("instrument.poweraux.turn_off 2")

        return pressures

    def update(self):
        """
        Periodically called get data and update plot.
        """

        timenow = datetime.datetime.now()
        s = str(timenow)
        secs = timenow - self.timestart
        secs1 = secs.total_seconds()

        # get new pressures
        pressures = self.get_pressures()

        if self.numplots == 1:
            self.ys.append(pressures[0])
        elif self.numplots == 2:
            self.ys.append(pressures[0])
            self.ys1.append(pressures[1])
        elif self.numplots == 3:
            self.ys.append(pressures[0])
            self.ys1.append(pressures[1])
            self.ys2.append(pressures[2])

        self.xs.append(dt.datetime.now().strftime("%H:%M:%S"))

        # self.ax.cla()
        if self.linear:
            self.ax.plot(self.xs, self.ys)
            if self.numplots > 1:
                self.ax.plot(self.xs, self.ys1)
            if self.numplots > 2:
                self.ax.plot(self.xs, self.ys2)
        else:
            self.ax.semilogy(self.xs, self.ys)
            if self.numplots > 1:
                self.ax.semilogy(self.xs, self.ys1)
            if self.numplots > 2:
                self.ax.semilogy(self.xs, self.ys2)

        print(f"{secs1:.0f}\t\t{[f'{p:1.2e}' for p in pressures]}\t\t{s}")
        s = f"{secs1:.0f}\t\t{[f'{p:1.2e}' for p in pressures]}\t\t{timenow}"

        self.datafile = open(self.datafilename, "a+")
        self.datafile.write(s + "\n")
        self.datafile.close()

        azcam.plot.update()

        self.lasttime = timenow

        return

    def run(self):

        self.setup()

        while 1:

            self.update()
            if azcam.utils.check_keyboard() == " ":
                self.datafile.close()
                print("Wrote data file")

            time.sleep(self.loop_delay)

        return


def measure_lvm_pressures():
    """
    Read pressure with power cycling.
    """

    measure_pressure = MeasureLvmPressures()
    measure_pressure.run()

    return

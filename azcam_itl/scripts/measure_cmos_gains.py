import sys
from statistics import mean
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

import azcam
import azcam_console.plot


class MeasureCmosGains(object):
    """
    Get camera gain and noise as a function of camera gain setting.
    """

    def __init__(self) -> None:
        self.gains = {}
        self.noises = {}

        self.ax1 = None
        self.ax2 = None
        self.lines = None
        self.delay = 0.0

        self.x_plot = []
        self.y_plot = []

        self.datafilename_gain = "camera_gains.txt"
        self.datafilename_noise = "camera_noise.txt"

        plt.ion()

    def setup(self):
        """
        Setup plot and data output header.
        """

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, sharex=True)
        # self.fig.suptitle("Camera Gain and Noise")
        self.fig.subplots_adjust(left=0.18, bottom=0.15, right=0.95, top=0.9)

        self.ax1.grid(1)
        self.ax1.set_title("Measured System Gain")
        self.ax1.set_ylabel("Gain [e/DN]")
        # self.ax1.ticklabel_format(axis="y", style="plain", scilimits=(0, 0))
        # self.ax1.plot([], [])

        self.ax2.grid(1)
        self.ax2.xaxis.set_major_locator(MaxNLocator(20))
        # self.ax2.set_title("Measured System Nosie")
        self.ax2.set_ylabel("Noise [e]")
        self.ax2.set_xlabel("Camera Gain Setting")
        # self.ax2.ticklabel_format(axis="y", style="plain", scilimits=(0, 0))
        # self.ax2.plot([], [])

        data_txt_hdr = "Gain_Setting\tSystem_Gain"
        self.datafile_gain = open(self.datafilename_gain, "a+")
        self.datafile_gain.write("# " + data_txt_hdr + "\n")

        data_txt_hdr = "Gain_Setting\tSystem_Noise"
        self.datafile_noise = open(self.datafilename_noise, "a+")
        self.datafile_noise.write("# " + data_txt_hdr + "\n")

        azcam_console.plot.move_window(1, 100, 100)
        azcam_console.plot.update()

        return

    def measure(self, gain_settings: list):
        """
        Measure and record system gain.
        """

        self.setup()

        self.gains = {}
        self.x_plot = []
        self.y1_plot = []
        self.y2_plot = []

        plt.sca(self.ax1)
        plt.ylim(0, 1.5)
        plt.xticks(rotation=45, ha="right")

        plt.sca(self.ax2)
        plt.ylim(0, 8)
        plt.xlim(0, max(gain_settings))
        plt.xticks(rotation=45, ha="right")

        for gain_setting in gain_settings:
            # set gain here
            azcam.log(f"Settin camera gain to {gain_setting}")
            azcam.db.parameters.set_par("cmos_gain", gain_setting)

            # measure gain
            try:
                azcam.db.tools["gain"].find()
                gains = azcam.db.tools["gain"].system_gain
                noises = azcam.db.tools["gain"].noise
            except Exception as e:
                print(e)
                return

            azcam.log(f"Measured gain [e/DN] and noises [e]: {gains}:{noises}")
            self.gains[gain_setting] = gains
            self.noises[gain_setting] = noises

            # data files
            s = f"{gain_setting}\t\t{[float(f'{g:1.2f}') for g in gains]}"
            if not self.datafile_gain.closed:
                self.datafile_gain.write(s + "\n")
            else:
                self.datafile_gain = open(self.datafilename_gain, "a+")
                self.datafile_gain.write(s + "\n")

            s = f"{gain_setting}\t\t{[float(f'{n:1.1f}') for n in noises]}"
            if not self.datafile_noise.closed:
                self.datafile_noise.write(s + "\n")
            else:
                self.datafile_noise = open(self.datafilename_noise, "a+")
                self.datafile_noise.write(s + "\n")

            self.y1_plot.append(gains)
            self.y2_plot.append(noises)
            self.x_plot.append(gain_setting)

            # self.ax.cla()
            self.ax1.plot(self.x_plot, self.y1_plot, "b.")
            self.ax2.plot(self.x_plot, self.y2_plot, "r.")

            azcam_console.plot.update()

        self.datafile_gain.close()
        self.datafile_noise.close()

        azcam_console.plot.plt.show()
        fignum = self.fig.number
        azcam_console.plot.save_figure(fignum, "camera_gain_noise.png")

        return


def measure_cmos_gains(gain_settings: list = [1, 100]):
    """
    Measure CMOS gains.
    """

    measurecmosgains = MeasureCmosGains()

    # measurecmosgains.setup()

    measurecmosgains.measure(gain_settings)

    return measurecmosgains


# start
if __name__ == "__main__":
    args = sys.argv[1:]
    measure_cmos_gains(*args)

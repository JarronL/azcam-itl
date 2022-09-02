"""
plot pressure
"""

import datetime
import sys

import azcam
from azcam.functions.plot import plt

# import seaborn
# seaborn.set_theme(style="ticks", font_scale=1.25)

# plt.style.use("Solarize_Light2")


def get_pressure_temperature(delay=1.0, start_offset=0):

    plt.ion()

    # setup plot
    fig = plt.figure()
    fig.suptitle("Pressures and Temperatures")

    ax1 = fig.add_subplot(2, 1, 1)
    ax1.grid(1)
    plt.ylabel("Pressure [Torr]")
    plt.xlabel("Time [secs]")
    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

    ax2 = fig.add_subplot(2, 1, 2)
    ax2.grid(1)
    plt.ylabel("Temperatures [C]")
    plt.xlabel("Time [secs]")

    times = []
    pressures1 = []
    pressures2 = []
    camtemps = []
    dewtemps = []

    timestart = datetime.datetime.now()

    data_txt_hdr = "Seconds\tPressures\tCamtemp\tDewtemp\tTime"
    with open("Pressure_temperature.txt", "a+") as datafile:
        datafile.write("# " + data_txt_hdr + "\n")

        loop = 1
        print(data_txt_hdr)
        while loop:

            timenow = datetime.datetime.now()
            s = str(timenow)
            secs = timenow - timestart
            secs1 = secs.total_seconds()
            secs1 += start_offset
            times.append(secs1)

            p1, p2 = azcam.db.tools["instrument"].get_pressures()
            pressures1.append(p1)
            pressures2.append(p2)

            temps = azcam.db.tools["tempcon"].get_temperatures()
            camtemp, dewtemp = temps[0:2]
            camtemps.append(camtemp)
            dewtemps.append(dewtemp)

            azcam.log(f"{secs1:.0f}\t{p1:.02e}\t{p2:.02e}\t{camtemp:.01f}\t{dewtemp:.01f}\t\t{s}")

            ax1.plot(times, pressures1, azcam.plot.style_lines[0])
            ax1.plot(times, pressures2, azcam.plot.style_lines[1])

            ax2.plot(times, camtemps, azcam.plot.style_lines[1])
            ax2.plot(times, dewtemps, azcam.plot.style_lines[2])

            azcam.plot.update()

            s = f"{secs1:.0f}\t{p1:1.2e}\t{p2:1.2e}\t{camtemp:0.1f}\t{dewtemp:.1f}\t{timenow}"
            datafile.write(s + "\n")
            datafile.flush()

            if 1:
                azcam.plot.plt.tight_layout()

            if azcam.utils.check_keyboard() == "q":
                break

            azcam.plot.delay(delay)

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 0:
        delay = int(args[0])
    else:
        delay = 60
    get_pressure_temperature(delay, start_offset=0)

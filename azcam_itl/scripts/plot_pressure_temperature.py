"""
plot pressure
"""

import datetime
import sys

import azcam


def plot_pressure_temperature(delay=1.0):

    azcam.plot.plt.ion()

    # setup plot
    fig = azcam.plot.plt.figure()
    fig.suptitle("Pressure and Temperatures")

    ax1 = fig.add_subplot(2, 1, 1)
    ax1.grid(1)
    azcam.plot.plt.ylabel("Pressure[Torr]")
    azcam.plot.plt.xlabel("Time [secs]")

    ax2 = fig.add_subplot(2, 1, 2)
    ax2.grid(1)
    azcam.plot.plt.ylabel("Temperatures [C]")
    azcam.plot.plt.xlabel("Time [secs]")

    times = []
    pressures = []
    camtemps = []
    dewtemps = []

    timestart = datetime.datetime.now()

    loop = 1
    print("Secs\tPressure\tTemperatures\tTime")
    while loop:

        timenow = datetime.datetime.now()
        s = str(timenow)
        secs = timenow - timestart
        secs1 = secs.total_seconds()
        times.append(secs1)

        p = azcam.db.tools["instrument"].get_pressures()[0]
        pressures.append(p)

        temps = azcam.db.tools["tempcon"].get_temperatures()
        camtemp, dewtemp = temps[0:2]
        camtemps.append(camtemp)
        dewtemps.append(dewtemp)

        azcam.log(f"{secs1:.0f}\t{p:.02e}\t{camtemp:.01f}\t{dewtemp:.01f}\t\t{s}")

        ax1.semilogy(times, pressures, azcam.plot.style_lines[0])

        ax2.plot(times, camtemps, azcam.plot.style_lines[1])
        ax2.plot(times, dewtemps, azcam.plot.style_lines[2])

        azcam.plot.update()

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
        delay = 10
    plot_pressure_temperature(delay)

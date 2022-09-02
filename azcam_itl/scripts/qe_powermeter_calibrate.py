"""
Measure flux with Newport power meter.
"""

import sys
import time

import azcam
import azcam.sockets


def qe_powermeter_calibrate(wavelengths):
    """
    Obtains values for multiple wavelengths by selecting wavelength and obtaining readings
    from power meter.

    :param wavelengths: list of wavelengths for each measurement
    :return: None
    """

    fluxes = []
    fluxes_close = []
    fluxes_open = []

    instrument = azcam.db.tools["instrument"]

    # 0 for QB, connection to remote server on conserver1
    if 0:
        server = azcam.sockets.SocketInterface("conserver1", 2402)
        if server.open():
            print("Connected to azcamserver")
            server.command("Register qe_console")
        else:
            print("Not connected to azcamserver")
    else:
        server = azcam.db.tools["server"]

    data_txt_hdr = "Wavelength" + "\t" + "Flux" + "\t\t" + "Light" + "\t\t" + "Dark"
    print(data_txt_hdr)

    instrument.set_comps("S")

    # Iterate through wavelengths and obtain readings
    for wave in wavelengths:

        instrument.comps_off()
        instrument.set_wavelength(wave)
        time.sleep(4)
        flux_close = server.command(f"instrument.get_power {wave}")

        instrument.comps_on()
        time.sleep(2)
        flux_open = server.command(f"instrument.get_power {wave}")

        # convert to floats
        flux_close = float(flux_close)
        flux_open = float(flux_open)
        flux = flux_open - flux_close

        s = f"{wave:.0f}\t\t{flux:1.3e}\t{flux_open:1.3e}\t{flux_close:1.3e}"
        print(s)

        # add readings to lists
        fluxes.append(flux)
        fluxes_close.append(flux_close)
        fluxes_open.append(flux_open)

    instrument.comps_off()

    # put data in txt file
    with open("flux_cal.txt", "w+") as datafile:
        datafile.write("# " + data_txt_hdr + "\n")
        for i, wave in enumerate(wavelengths):
            data_txt_line = (
                f"{wave:.0f}\t{fluxes[i]:1.3e}\t{fluxes_open[i]:1.3e}\t{fluxes_close[i]:1.3e}"
            )
            datafile.write(data_txt_line + "\n")

    return


if __name__ == "__main__":
    args = sys.argv[1:]

    # waves = [330, 350, 370, 400, 500, 600, 700, 800, 900, 1000]  # BB
    # waves = [int(w) for w in range(300, 1110, 10)]  # QB
    waves = [
        360,
        400,
        450,
        500,
        550,
        600,
        650,
        700,
        750,
        800,
        850,
        900,
        950,
        980,
        1000,
    ]  # LVM QB

    # qe_diode_calibrate(*args)
    qe_powermeter_calibrate(waves)

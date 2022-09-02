import ctypes
import time

import numpy as np

import azcam


class CommandError(Exception):
    """The function in the usbdll.dll was not sucessfully evaluated"""


class NewPort_1936r:
    def __init__(self):
        pass

    def initialize(self, **kwargs):
        try:
            self.LIBNAME = kwargs.get(
                "LIBNAME", r"C:\Program Files\Newport\Newport USB Driver\Bin\usbdll.dll"
            )
            # azcam.log(self.LIBNAME)
            self.lib = ctypes.windll.LoadLibrary(self.LIBNAME)
            self.product_id = kwargs.get("product_id", 0xCEC7)
            self.open_device_with_product_id()
        except (WindowsError, CommandError) as e:
            azcam.log(str(e))
            # raise CommandError('could not open detector library will all the functions in it: %s' % LIBNAME)
        else:
            self.instrument = (
                self.get_instrument_list()
            )  # here instrument[0] is the device id, [1] is the model
            # number and [2] is the serial number
            [self.device_id, self.model_number, self.serial_number] = self.instrument

        return

    def open_device_all_products_all_devices(self):
        status = (
            self.lib.newp_usb_init_system()
        )  # Should return a=0 if a device is connected
        if status != 0:
            raise CommandError()
        else:
            azcam.log("Success!! your are connected to one or more of Newport products")

    def open_device_with_product_id(self):
        """
        opens a device with a certain product id
        """
        cproductid = ctypes.c_int(self.product_id)
        useusbaddress = ctypes.c_bool(1)  # We will only use deviceids or addresses
        num_devices = ctypes.c_int()
        # try:
        status = self.lib.newp_usb_open_devices(
            cproductid, useusbaddress, ctypes.byref(num_devices)
        )

        if status != 0:
            self.status = "Not Connected"
            raise CommandError(
                "ERROR: Newport 1936 failed to initialize. Make sure it is connected; try the method "
                "'.restart_device()'"
            )
        else:
            azcam.log(
                "Number of devices connected: "
                + str(num_devices.value)
                + " device/devices"
            )
            self.status = "Connected"
        # except CommandError as e:
        #    azcam.log(e)
        #    sys.exit(1)

    def close_device(self):
        """
        Closes the device
        :raise CommandError:
        """
        status = self.lib.newp_usb_uninit_system()  # closes the units

        """
        # if status == 0, then device still somehow connected. Raise error
        if status:
            raise CommandError()
        else:
            azcam.log("Closed the newport device connection. Have a nice day!")
        """

        return

    def restart_device(self):
        self.close_device()
        self.__init__()

        return

    def get_instrument_list(self):
        arInstruments = ctypes.c_int()
        arInstrumentsModel = ctypes.c_int()
        arInstrumentsSN = ctypes.c_int()
        nArraySize = ctypes.c_int()
        try:
            status = self.lib.GetInstrumentList(
                ctypes.byref(arInstruments),
                ctypes.byref(arInstrumentsModel),
                ctypes.byref(arInstrumentsSN),
                ctypes.byref(nArraySize),
            )
            if status != 0:
                raise CommandError("Cannot get the instrument_list")
            else:
                instrument_list = [
                    arInstruments.value,
                    arInstrumentsModel.value,
                    arInstrumentsSN.value,
                ]
                azcam.log(
                    "Arrays of Device Id's: Model number's: Serial Number's: "
                    + str(instrument_list)
                )
                return instrument_list
        except CommandError as e:
            azcam.log(e)

        return

    def read(self):
        """
        This simply reads the current data on the buffer, this is useful when an issue occurred and data "got stuck" in the buffer.
        :return: reading on device
        """
        response = ctypes.create_string_buffer(b"\000" * 1024)
        leng = ctypes.c_ulong(1024)
        read_bytes = ctypes.c_ulong()
        cdevice_id = ctypes.c_long(self.device_id)
        status = self.lib.newp_usb_get_ascii(
            cdevice_id, ctypes.byref(response), leng, ctypes.byref(read_bytes)
        )
        if status != 0:
            raise CommandError(
                "Invalid reading, something must be wrong with your query or there is nothing to read"
            )
        else:
            answer = response.value[0 : read_bytes.value].rstrip(b"\r\n")

        return answer.decode(encoding="ascii")

    def query(self, query_string):
        """
        Write a query and read the response from the device
        :rtype : String
        :param query_string: Check Manual for commands, ex '*IDN?'
        :return: :raise CommandError:
        """
        query_byte = query_string.encode("ascii")
        query = ctypes.create_string_buffer(query_byte)
        leng = ctypes.c_ulong(ctypes.sizeof(query))
        status = self.lib.newp_usb_send_ascii(self.device_id, ctypes.byref(query), leng)
        if status != 0:
            raise CommandError("Something apperars to be wrong with your query string")
        else:
            pass
        time.sleep(0.2)
        answer = self.read()

        return answer

    def write(self, command_string):
        """
        Write a string to the device
        :param command_string: Name of the string to be sent. Check Manual for commands
        :raise CommandError:
        """
        command_byte = command_string.encode("ascii")
        command = ctypes.create_string_buffer(command_byte)
        length = ctypes.c_ulong(ctypes.sizeof(command))
        cdevice_id = ctypes.c_long(self.device_id)
        status = self.lib.newp_usb_send_ascii(cdevice_id, ctypes.byref(command), length)
        try:
            if status != 0:
                raise CommandError(
                    "Connection error or  Something apperars to be wrong with your command string"
                )
            else:
                pass
        except CommandError as e:
            azcam.log(e)

        return

    def select_units(self, units):
        """
        This is a parser for units string to convert to acceptable command for device and set the corresponding units
        :param units: string unit ex: volts, watts, watts/cm^2, joule
        :return: It sets the units to such.
        """
        this_val = 0
        units_dic = {
            "amps,amp,current": "0",
            "watts,watt,wattage": "2",
            "watts/cm2,watts/cm^2,watts/cm": "3",
            "dbm": "6",
        }
        for key, val in units_dic.items():
            for key2 in key.split(","):
                if key2 == units.lower():
                    this_val = val
        assert this_val in units_dic.values(), "Invalid unit String, try again"
        self.write("PM:UNITs " + this_val)

        return

    def set_wavelength(self, wavelength):
        """
        Sets the wavelength on the device
        :param wavelength: float (nanometers)
        """
        if isinstance(wavelength, float):
            azcam.log("Warning: Wavelength has to be an integer. Converting to integer")
            wavelength = int(wavelength)
        if (
            int(self.query("PM:MIN:Lambda?"))
            <= wavelength
            <= int(self.query("PM:MAX:Lambda?"))
        ):
            self.write("PM:Lambda " + str(wavelength))
        else:
            azcam.log("Wavelenth out of range, use the current lambda")

        return

    def set_filtering(self, filter_type=0):
        """
        Set the filtering on the device
        :param filter_type:
        0:No filtering
        1:Analog filter
        2:Digital filter
        3:Analog and Digital filter
        """
        if isinstance(filter_type, int):
            if filter_type == 0:
                self.write("PM:FILT 0")  # no filtering
            elif filter_type == 1:
                self.write("PM:FILT 1")  # Analog filtering
            elif filter_type == 2:
                self.write("PM:FILT 2")  # Digital filtering
            elif filter_type == 1:
                self.write("PM:FILT 3")  # Analog and Digital filtering

        else:  # if the user gives a float or string
            azcam.log(
                "Wrong datatype for the filter_type. No filtering being performed"
            )
            self.write("PM:FILT 0")  # no filtering

        return

    def read_buffer(self, wavelength=700, buff_size=1000, interval_ms=1):
        """
        Stores the power values at a certain wavelength.
        :param wavelength: float: Wavelength at which this operation should be done. float.
        :param buff_size: int: nuber of readings that will be taken
        :param interval_ms: float: Time between readings in ms.
        :return: [actual_wavelength,avg_power,std_power]
        """
        self.set_wavelength(wavelength)
        self.write("PM:DS:Clear")
        self.write("PM:DS:SIZE " + str(buff_size))
        self.write(
            "PM:DS:INT " + str(interval_ms * 10)
        )  # to set 1 ms rate we have to give int value of 10. This is strange as manual says the INT should be in ms
        self.write("PM:DS:ENable 1")
        while (
            int(self.query("PM:DS:COUNT?")) < buff_size
        ):  # Waits for the buffer is full or not.
            time.sleep(0.001 * interval_ms * buff_size / 10)
        actual_wavelength = self.query("PM:Lambda?")
        avg_power = self.query("PM:STAT:MEAN?")
        std_power = self.query("PM:STAT:SDEV?")
        self.write("PM:DS:Clear")

        return [actual_wavelength, avg_power, std_power]

    def read_instant_power(self, wavelength=700):
        """
        reads the instantaneous power
        :param wavelength:
        :return:[actualwavelength,power]
        """
        self.set_wavelength(wavelength)
        actualwavelength = self.query("PM:Lambda?")
        power = self.query("PM:Power?")

        return [actualwavelength, power]

    def sweep(self, swave, ewave, interval, buff_size=1000, interval_ms=1):
        """
        Sweeps over wavelength and records the power readings. At each wavelength many readings can be made
        :param swave: int: Start wavelength
        :param ewave: int: End Wavelength
        :param interval: int: interval between wavelength
        :param buff_size: int: nunber of readings
        :param interval_ms: int: Time betweem readings in ms
        :return:[wave,power_mean,power_std]
        """
        self.set_filtering()  # make sure their is no filtering
        data = []
        num_of_points = int((ewave - swave) / (1 * interval)) + 1

        for i in np.linspace(swave, ewave, num_of_points).astype(int):
            data.extend(self.read_buffer(i, buff_size, interval_ms))
        data = [float(x) for x in data]
        wave = data[0::3]
        power_mean = data[1::3]
        power_std = data[2::3]

        return [wave, power_mean, power_std]

    def sweep_instant_power(self, swave, ewave, interval):
        """
        Sweeps over wavelength and records the power readings. only one reading is made
        :param swave: int: Start wavelength
        :param ewave: int: End Wavelength
        :param interval: int: interval between wavelength
        :return:[wave,power]
        """
        self.set_filtering(self.device_id)  # make sure there is no filtering
        data = []
        num_of_points = int((ewave - swave) / (1 * interval)) + 1
        for i in np.linspace(swave, ewave, num_of_points).astype(int):
            data.extend(self.read_instant_power(i))
        data = [float(x) for x in data]
        wave = data[0::2]
        power = data[1::2]

        return [wave, power]

    def plotter_instantpower(self, data):
        """
        Plot the instant power and nothing else
        :param data: Data list must be a list of two list. The first list must contain the wavelengths to be plotted, while
        the second list must contain the power value of those wavelengths.
        :return: A plot of the values as points.
        """
        azcam.plot.plt.close("All")
        azcam.plot.plt.plot(data[0], data[1], "-ro")
        azcam.plot.plt.show()

        return

    def plotter(self, data):
        """
        Plot all data. Must include error bars.
        :param data: [wavelengths, values, error bars]
        :return: A plot of the values as points with error bars
        """
        azcam.plot.plt.close("All")
        azcam.plot.plt.errorbar(data[0], data[1], data[2], fmt="ro")
        azcam.plot.plt.show()

        return

    def plotter_spectra(self, dark_data, light_data):
        azcam.plot.plt.close("All")
        azcam.plot.plt.errorbar(dark_data[0], dark_data[1], dark_data[2], fmt="ro")
        azcam.plot.plt.errorbar(light_data[0], light_data[1], light_data[2], fmt="go")
        azcam.plot.plt.show()

        return

    def console(self):
        """
        opens a console to send commands. See the commands in the user manual.
        For ITL Purposes. I suggest to not use this. It has bugs.
        """
        azcam.log(
            "You are connected to the first device with deviceid/usb address "
            + str(self.serial_number)
        )
        cmd = ""
        while cmd != "exit()":
            cmd = input("Newport console, Type exit() to leave> ")
            if cmd.find("?") >= 0:
                answer = self.query(cmd)
                azcam.log(answer)
            elif cmd.find("?") < 0 and cmd != "exit()":
                self.write(cmd)
        else:
            azcam.log("Exiting the Newport console")

        return


if __name__ == "__main__":
    # Initialze a instrument tool. You might have to change the LIBname or product_id.
    nd = NewPort_1936r()
    # Print the status of the newport detector.
    azcam.log(nd.status)

    if nd.status == "Connected":
        azcam.log("Serial number is " + str(nd.serial_number))
        azcam.log("Model name is " + str(nd.model_number))
        # azcam.log(nd.query('ERRors?'))
        # Print the IDN of the newport detector.
        azcam.log("Connected to " + nd.query("*IDN?"))

        # 100 reading of the newport detector at 500 nm wavelength and plot them
        [actualwavelength, mean_power, std_power] = nd.read_buffer(
            wavelength=500, buff_size=10, interval_ms=1
        )
        azcam.log(actualwavelength, mean_power, std_power)
        dark_data = nd.sweep(510, 550, 10, buff_size=10, interval_ms=1)

        nd.plotter(dark_data)

        # sweep the wavelength of the detector from 500 to 550 with an interval of 10 nm. At each wavelength the buffer size is 10 and the time between samples is 1 ms
        light_data = nd.sweep(500, 550, 10, buff_size=10, interval_ms=1)
        nd.plotter_spectra(dark_data, light_data)

        # Give the instant_power
        data = nd.sweep_instant_power(400, 410, 2)
        nd.plotter_instantpower(data)

        # opens a console
        # nd.console()

        # Close the device
        nd.close_device()

    elif nd.status != "Connected":
        azcam.log("Cannot connect.")

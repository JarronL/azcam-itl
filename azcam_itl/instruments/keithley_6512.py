import math
import time
import warnings
from statistics import stdev

import pyvisa

warnings.filterwarnings("error")

"""
conserver1 @ ITL:
 GPIB0 - Instrument 0 - Primary address 22
 connected to GPIB-USB-HS
"""


def round_sigfigs(num, sig_figs=5):
    """Round to specified number of sigfigs. Default 5 sigfigs
    round_sigfigs(0, sig_figs=4)
    0
    int(round_sigfigs(12345, sig_figs=2))
    12000
    int(round_sigfigs(-12345, sig_figs=2))
    -12000
    int(round_sigfigs(1, sig_figs=2))
    1
    '{0:.3}'.format(round_sigfigs(3.1415, sig_figs=2))
    '3.1'
    '{0:.3}'.format(round_sigfigs(-3.1415, sig_figs=2))
    '-3.1'
    '{0:.5}'.format(round_sigfigs(0.00098765, sig_figs=2))
    '0.00099'
    '{0:.6}'.format(round_sigfigs(0.00098765, sig_figs=3))
    '0.000988'
    """
    if num != 0:
        return round(num, -int(math.floor(math.log10(abs(num))) - (sig_figs - 1)))
    else:
        return 0  # Can't take the log of 0


class DEVICE(object):
    """
    This class allows you to manipulate VISA compatible devices and includes subclasses for the following devices:
    KEITHLEY 6512 ELECTROMETER
    """

    def __init__(self, device):
        self.RM = pyvisa.ResourceManager()
        try:
            self.device = self.RM.open_resource(device)
        except pyvisa.VisaIOError:
            warnings.warn(Warning())
            # raise Exception("The device was not detected or mislabeled, please make sure it is connected with the label 'electrometer'.")
        else:
            self.name = device

    def query_val(self, given_fn):
        """
        This function will take a function compatible with the device and get a value.
        :param given_fn: function must be compatible with device, have termination and return a pure value (no strings)
        :return: return the rounded value for the given function
        """
        try:
            x = float(self.device.query(given_fn))
        except ValueError:
            raise Exception(
                "The value obtained from "
                + self.name
                + " using the function: "
                + given_fn
                + " is not a 'pure value', try again"
            )
        else:
            x = round_sigfigs(x)
            return x

    def close_up(self):
        # (default)
        try:
            self.device.close()
        except AttributeError:
            print("Device was never open")

    def restart_device(self):
        self.close_up()
        self.__init__(self.name)


class EM6512(DEVICE):
    def __init__(self, device):
        """
        This class allows you to create an object out of the connection to a KEITHLEY 6512 EM used in ITL.
        """

        super().__init__(device)

        self.dev = device

    def initialize(self):
        """
        ITL Initialize.
        """

        try:
            super(EM6512, self).__init__(self.dev)
        except Warning:
            print(
                "ERROR: %s failed to initialize. Make sure it is connected and labeled. "
                "; try method '.restart_device()''." % str(self.dev)
            )
        else:
            # zero machine
            self.device.write("Z0XC1XZ1C0X")
            self.defaults()

        return

    def parse_fn(self, given_fn):
        functions = {
            "voltage,volts,volt,voltages": "F0",
            "current,amps": "F1",
            "charges,charge,coulombs,coul,couls": "F3",
            "resistance,ohms,ohm,resistances": "F2",
        }
        for key, val in functions.items():
            keys = key.split(",")
            if given_fn in keys or given_fn == val:
                return val
        else:
            raise Exception(
                "Invalid function; The given function doesn't match my available functions"
            )

    def defaults(self):
        self.device.write("F0XR0XC1XZ0XN0XT6XG0XQ7XM00XK0X")

    def get_val(self, given_fn):
        """
        This function is to get an instantenous value. One reading is made.
        :param given_fn: the function such as, volts, ohms, coul, amps
        :return: return the single value
        """
        given_fn = self.parse_fn(given_fn)
        function_cmd = "G1C0" + given_fn + "X"
        x = self.query_val(function_cmd)
        return x

    def init_value_storage(self):
        self.defaults()
        # Enable data storage, conversion rate
        self.device.write("Q0C0X")
        # SQR on data storage full
        self.device.write("M2X")

    def wait_datafull(self, timer, counts):
        print("Storing data...")
        # this is an estimated limit of how long it should take for the device to store the counts.
        limit = 36 * counts / 100
        # Check if data storage full
        while True:
            # read data condition word
            data_word = self.device.query("U2X")
            # read specific letter /  check if data storage is full.. the argument must be 1.
            elapsed = time.perf_counter() - timer
            if int(data_word[4]) or elapsed > limit:
                break
            # wait 2 seconds
            time.sleep(2)

    def read_datastorage(self, counts):
        # Set reading mode to data storage
        self.device.write("C1B1G2X")
        print("Reading data...")
        values = []
        for i in range(counts):
            value = self.query_val("G1X")
            values.append(value)
        return values

    def sweep_values(self, given_fn, counts):
        """
        The function will gather values and wait for the multimeter to store the values. It then reads the number of
        counts necessary and averages them. The function will return the average value and it will print the time it took.
         takes approximately 36 secs. We are working on reducing this time.
        :param given_fn: Value type to gather. E.g. ohms,volts,etc.
        :param counts: Number of times you want to measure
        :return: returns the values, average, and standard deviation
        """
        if counts > 100:
            print(
                "The count cannot exceed 100, we'll perform a sweep for 100 values now..."
            )
            counts = 100
        self.init_value_storage()
        given_fn = self.parse_fn(given_fn)
        self.device.write(given_fn + "X")
        start = time.perf_counter()
        self.wait_datafull(start, counts)
        elapsed = time.perf_counter() - start
        print(
            "The data was stored during a period of "
            + str(round_sigfigs(elapsed))
            + " seconds"
        )
        values = self.read_datastorage(counts)
        avg_val = round_sigfigs(sum(values) / len(values))
        return values, avg_val, stdev(values)


if __name__ == "__main__":
    # electrometer = EM6512("electrometer")
    # electrometer = EM6512("COM6")
    electrometer = EM6512("ASRL1::INSTR")

    # print(electrometer.avg_value("volts",25))
    # print(electrometer.get_val("volts"))
    # electrometer.close_up()

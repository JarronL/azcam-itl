import time
import threading

import serial

import azcam
import azcam.exceptions


class FilterControllerBB(object):
    """
    Defines the filers controller interface (Oriel wheels) on COMs 12,13,14.
    COM12 - Filter 1
    COM13 - Filter 2
    COM14 - Filter 3
    """

    def __init__(self, ports=["COM1", "COM2", "COM3"]):

        # dict {wavelength_str:[filter positions]} - {"clear": [1, 1]}
        self.filter_wavelengths = {}
        self.filter_positions = []
        self.available_filter_positions = [
            [1, 2, 3, 4, 5, 6],
            [1, 2, 3, 4, 5, 6],
            [1, 2, 3, 4, 5, 6],
        ]

        self.ComPort1 = ports[0]  # Wheel 1 in boson Lab
        self.ComPort2 = ports[1]  # Wheel 2 in boson Lab
        self.ComPort3 = ports[2]  # Wheel 3 in boson Lab
        self.BaudRate = 9600
        self.Parity = serial.PARITY_NONE
        self.ByteSize = 8
        self.StopBits = 1
        self.timeout = 3
        self.RtsCts = 0
        self.XonXoff = 0

        self.ser1 = 0
        self.ser2 = 0
        self.ser3 = 0

        self.verbosity = 1

        self.lock = threading.Lock()

    def initialize(self):
        """
        Initialize filters.
        """

        if self.ser1 == 0:
            self.ser1 = serial.Serial(
                port=self.ComPort1,
                baudrate=self.BaudRate,
                timeout=self.timeout,
                parity=self.Parity,
                stopbits=self.StopBits,
                bytesize=self.ByteSize,
                rtscts=self.RtsCts,
                xonxoff=self.XonXoff,
            )

        if self.ser2 == 0:
            self.ser2 = serial.Serial(
                port=self.ComPort2,
                baudrate=self.BaudRate,
                timeout=self.timeout,
                parity=self.Parity,
                stopbits=self.StopBits,
                bytesize=self.ByteSize,
                rtscts=self.RtsCts,
                xonxoff=self.XonXoff,
            )

        if self.ser3 == 0:
            self.ser3 = serial.Serial(
                port=self.ComPort3,
                baudrate=self.BaudRate,
                timeout=self.timeout,
                parity=self.Parity,
                stopbits=self.StopBits,
                bytesize=self.ByteSize,
                rtscts=self.RtsCts,
                xonxoff=self.XonXoff,
            )

        # open ports
        self.open_ports()

        self.ser1.flushInput()
        self.ser1.flushOutput()
        self.ser1.write(str.encode("HANDSHAKE 0\n"))
        self.ser1.write(str.encode("ESR?\n"))

        self.ser2.flushInput()
        self.ser2.flushOutput()
        self.ser2.write(str.encode("HANDSHAKE 0\n"))
        self.ser2.write(str.encode("ESR?\n"))

        self.ser3.flushInput()
        self.ser3.flushOutput()
        self.ser3.write(str.encode("HANDSHAKE 0\n"))
        self.ser3.write(str.encode("ESR?\n"))

        return

    def open_ports(self):
        """
        Open serial port.
        """

        if not self.ser1.isOpen():
            self.ser1.open()
        if not self.ser2.isOpen():
            self.ser2.open()
        if not self.ser3.isOpen():
            self.ser3.open()

        return

    def close_ports(self):
        """
        Close serial port.
        """

        try:
            self.ser1.close()
        except Exception:
            pass
        try:
            self.ser2.close()
        except Exception:
            pass
        try:
            self.ser3.close()
        except Exception:
            pass

        return

    def get_filter_positions(self):
        """
        Read current positions of all filter wheels.
        """

        with self.lock:
            self.open_ports()

            for portnum, port in enumerate([self.ser1, self.ser2, self.ser3]):
                loop = 1
                while loop:
                    port.flushInput()
                    port.write(str.encode("Filter?\n"))
                    time.sleep(0.05)
                    nchars = port.inWaiting()
                    if nchars == 11:
                        reply = port.read(nchars).decode()
                        break
                    else:
                        if self.verbosity > 1:
                            print(
                                f"get_filter_positions did not get 11 chars in loop:port {loop}:{portnum}"
                            )
                        loop += 1

                    if loop > 10:
                        self.close_ports()
                        raise azcam.exceptions.AzCamError(
                            f"Could not read filter {(portnum + 1)}"
                        )

                if self.verbosity > 1:
                    print("Filter? reply", reply.strip())
                f = reply[8]
                f = int(f)

                if portnum == 0:
                    filter1 = int(f)
                elif portnum == 1:
                    filter2 = int(f)
                elif portnum == 2:
                    filter3 = int(f)

        self.filter_positions = [filter1, filter2, filter3]

        return self.filter_positions

    def move_filters(self, filter1: int, filter2: int, filter3: int = -1):
        """
        Move all filter wheels.
        Args:
            filter1: filter wheel 1 position number
            filter2: filter wheel 2 position number
            filter3: filter wheel 3 position number
        """

        filter1 = int(filter1)
        filter2 = int(filter2)
        filter3 = int(filter3)

        with self.lock:
            self.open_ports()
            for portnum, port in enumerate([self.ser1, self.ser2, self.ser3]):
                if portnum == 0:
                    if filter1 == -1:
                        continue
                    filterpos = filter1
                elif portnum == 1:
                    if filter2 == -1:
                        continue
                    filterpos = filter2
                elif portnum == 2:
                    if filter3 == -1:
                        continue
                    filterpos = filter3

                port.write(str.encode("Filter %d\n" % filterpos))

        self.get_filter_positions()

        return

    def get_filters(self, filter_id=0):
        """
        Return unordered list of valid filter names.
        """

        a = list(self.filter_wavelengths.keys())

        return a

    def get_filter(self, filter_id=0):
        """
        Return the current filter position.
        """

        filts = self.get_filter_positions()

        return filts[int(filter_id)]

    def set_filter(self, filternum, filter_id=0):
        """
        Set a filter position.
        """

        f1 = -1
        f2 = -1
        f3 = -1

        if filter_id == 0:
            f1 = filternum
        elif filter_id == 1:
            f2 = filternum
        elif filter_id == 2:
            f3 = filternum

        self.move_filters(f1, f2, f3)

        return

    # ***************************************************************************
    # wavelengths
    # ***************************************************************************

    def get_wavelengths(self, wavelength_id=0):
        """
        Returns a list of valid wavelengths.
        Used for filter and LED based systems.
        wavelength_id is the wavelength mechanism ID.
        """

        return list(self.filter_wavelengths.keys())

    def set_wavelength(self, wavelength, wavelength_id=0):
        """
        Sets the current wavelength.
        """

        wave = str(wavelength).lower()
        wave = int(float(wave))
        wave = str(wave)

        if wave in list(self.filter_wavelengths.keys()):
            filts = self.filter_wavelengths[wave]
        elif wave == "0":
            filts = self.filter_wavelengths["clear"]
        elif wave == "-1":
            filts = self.filter_wavelengths["dark"]
        else:
            raise azcam.exceptions.AzCamError(
                f"invalid filter wavelength: {wavelength}"
            )

        self.move_filters(filts[0], filts[1])

        return

    def get_wavelength(self, wavelength_id=0):
        """
        Returns the current wavelength if defined.
        """

        reply = self.get_filter_positions()

        filts = reply[0:2]  # first 2 only

        found = 0
        for wave in self.filter_wavelengths:
            f = self.filter_wavelengths[wave][0:2]
            if filts == f:
                found = 1
                break

        if not found:
            raise azcam.exceptions.AzCamError("invalid wavelength read")

        if wave.isnumeric():
            wave = int(wave)
        self.wavelength = wave

        return wave

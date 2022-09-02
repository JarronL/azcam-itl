import serial

import azcam


class DiodeControllerClass(object):
    """
    Defines the diodes controller interface (Keithley 6482) on COM21.
    """

    def __init__(self, port="COM21"):

        self.ComPort = port
        self.BaudRate = 9600
        self.Parity = serial.PARITY_NONE
        self.ByteSize = 8
        self.StopBits = 1
        self.timeout = 3
        self.RtsCts = 0
        self.XonXoff = 0

        self.ser = 0

    def initialize(self):
        """
        Initialize controller.
        """

        reply = self.open_port()

        # set hi accuracy and autozero
        reply = self.ser.write(str.encode(":SYST:AZER ON\n"))
        reply = self.ser.read(28).decode()

        reply = self.ser.write(str.encode(":SENS1:CURR:NPLC 10\n"))
        reply = self.ser.read(28).decode()

        return

    def open_port(self):
        """
        Open serial port.
        """

        if self.ser == 0 or not self.ser.isOpen():
            try:
                self.ser = serial.Serial(
                    port=self.ComPort,
                    baudrate=self.BaudRate,
                    timeout=self.timeout,
                    parity=self.Parity,
                    stopbits=self.StopBits,
                    bytesize=self.ByteSize,
                    rtscts=self.RtsCts,
                    xonxoff=self.XonXoff,
                )
            except Exception as message:
                azcam.log(message)
                return ["ERROR", "could not open diode serial port"]

        return

    def read_diodes(self):
        """
        Read diode values.  First value is sphere, second is DUT.
        """

        reply = self.open_port()

        reply = self.ser.write(str.encode(":MEAS:CURR:DC?\n"))
        reply = self.ser.read(28).decode()
        reply = reply.strip()
        currents = reply.split(",")
        try:
            current1 = float(currents[0])
            current2 = float(currents[1])
        except Exception as message:
            azcam.log("Could not read currents:%s" % message)
            current1 = current2 = 0.0

        return [current1, current2]

    def close_port(self):
        """
        Close serial port.
        """

        try:
            self.ser.close()
        except Exception:
            pass

        return

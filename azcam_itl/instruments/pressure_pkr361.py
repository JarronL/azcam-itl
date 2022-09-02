import serial

import azcam


class PressureController(object):
    """
    Pressure controller for Pfeiffer PKR361.

    Using Fluke ADC for voltage conversion?
    """

    def __init__(self, port="COM1"):

        self.ComPort = port
        self.BaudRate = 600
        self.Parity = serial.PARITY_NONE
        self.ByteSize = 7
        self.StopBits = 2
        self.timeout = 2
        self.RtsCts = 0
        self.XonXoff = 0

        self.ser = 0

    def initialize(self):
        """
        Initialize controller.
        """

        reply = self.close_port()  # might be stuck open

        reply = self.open_port()

        return reply

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

                self.ser.setRTS(0)
                self.ser.setDTR(1)

            except Exception as message:
                azcam.log(message)
                return ["ERROR", "could not open pressure serial port"]

        return

    def read_pressure(self, pressure_id=0):
        """
        read pressure in Torr.
        """

        reply = self.open_port()

        reply = self.ser.write(str.encode("D"))
        reply = self.ser.read(14).decode()

        try:
            tokens = azcam.utils.parse(reply)
            v = float(tokens[1])
            pressure = 10 ** (1.667 * v - 11.46)
        except Exception as message:
            # azcam.log("Could not read pressure:%s" % message)
            pressure = -999.9

        return pressure

    def close_port(self):
        """
        Close serial port.
        """

        try:
            self.ser.close()
        except Exception:
            pass

        return

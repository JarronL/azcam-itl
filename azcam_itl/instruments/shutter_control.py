import serial

import azcam
import azcam.exceptions


class ShutterControllerClass(object):
    """
    Defines the shutter controller interface.

    Shutter Control (COM20):
    """

    def __init__(self, port="COM1"):

        self.ComPort = port
        self.BaudRate = 9600
        self.Parity = serial.PARITY_NONE
        self.ByteSize = 8
        self.StopBits = 1
        self.timeout = 10
        self.RtsCts = 0
        self.XonXoff = 0

        self.ser = 0

    def initialize(self):
        """
        Initialize shutter controller.
        """

        # TODO: May also want to cycle power

        # open port
        self.open_port()

        self.set_state("S")

        self.set_state("C")

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
                raise azcam.exceptions.AzcamError("could not open shutter serial port")

        return

    def write(self, Command):
        """
        Write a string to serial port.
        """

        self.open_port()

        self.ser.write(str.encode(Command))

        self.ser.flush()

        return

    def close_port(self):
        """
        Close serial port.
        """

        try:
            self.ser.close()
        except Exception:
            pass

        return

    def set_state(self, StateName):
        """
        Sets a shutter state.
        States are: S,F,L,G,O,C
        """

        reply = self.write(StateName)

        return reply

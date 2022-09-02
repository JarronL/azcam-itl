import serial


class ShutterControllerClassUSB(object):
    """
    Defines the shutter controller interface.

    Shutter Control (COM20):
    """

    def __init__(self, port):

        self.ComPort = port
        self.BaudRate = 115200
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
        May also want to cycle power...
        """

        # open port
        self.open_port()

        # self.set_state('S')

        # self.set_state('C')

        return

    def open_port(self):
        """
        Open serial port.
        """

        if self.ser == 0 or not self.ser.isOpen():
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

            # s=chr(254)+chr(248)
            # self.ser.write(s)
            # self.ser.flush()

        return

    def write(self, Command):
        """
        Write a byte to USB port.
        """

        self.open_port()

        s = chr(254) + chr(Command)

        self.ser.write(s)
        self.ser.flush()

        self.ser.read(1)

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
        Sets a shutter state by saving state.
        States are: S,F,L,G,O,C
        """

        self.state = StateName

        return

    def open_shutter(self):
        """
        Open active shutter.
        """

        code = 8  # relays 8-11

        self.write(code)

        return

    def close_shutter(self):
        """
        Close active shutter.
        """

        self.write(0)

        return

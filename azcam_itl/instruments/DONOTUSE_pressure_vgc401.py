import time

import serial

import azcam


class PressureController(object):
    """
    Pressure controller for Inficon VGC-401 and VGC-501.
    """

    def __init__(self, port="COM1"):

        self.ComPort = port
        # self.BaudRate = 9600
        self.BaudRate = 115200
        self.Parity = serial.PARITY_NONE
        self.ByteSize = 8
        self.StopBits = 1
        self.timeout = 2.0
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
            except Exception as message:
                azcam.log(message)
                azcam.log("could not open pressure serial port")

        return

    def close_port(self):
        """
        Close serial port.
        """

        try:
            self.ser.close()
        except Exception as e:
            pass

        return

    def command(self, command):
        """
        Send command to controller and read reply.
        """

        self.open_port()

        self.ser.write(str.encode(f"{command}\r\n"))
        reply = self.ser.read(3).decode()  # ACK CR LF
        if reply[0] == "\x15":
            print("NAK read from pressure controller")
            print(reply)
            return -999.9
        elif reply[0] == "\x06":
            # print("ACK read from pressure controller")
            pass

        self.ser.write(str.encode("\05"))  # ENQ

        reply = self.ser.read_until().decode()[:-2]  # strip \r\n

        return reply

    def test(self):
        """
        Test controller.
        """

        self.open_port()
        self.ser.reset_input_buffer()

        self.ser.write(str.encode("HDW\n"))
        print(self.ser.in_waiting)
        reply = self.ser.read(3).decode()  # ACK CR LF
        print(reply)
        reply = self.ser.write(str.encode("\05"))  # ENQ
        print(reply)
        reply = self.ser.read_until().decode()[:-1]  # strip CR
        print(reply)

        return reply

    def reset(self):
        """
        Reset controller.
        """

        self.open_port()
        self.ser.write(str.encode("HDW\n"))
        reply = self.ser.read(3).decode()  # ACK CR LF
        reply = self.ser.write(str.encode("\05"))  # ENQ

        reply = self.ser.write(str.encode("RES,1\n"))
        reply = self.ser.read(3).decode()  # ACK CR LF
        reply = self.ser.write(str.encode("\05"))  # ENQ
        reply = self.ser.read(1).decode()[:-1]  # strip CR

        return

    def read_continuous_data(self, loop=0):
        """
        Read continuous output before any commands are sent.
        """

        self.open_port()

        counter = 0
        while 1:
            reply = self.ser.read_until().decode()
            reply = reply[3:-2]
            try:
                p = float(reply)
            except ValueError:
                print("could not read pressure value")
                p = None
                break
            if not loop:
                break
            print(f"Reading: {counter}: {p:.1e} Torr")
            counter += 1

        return p

    def get_error_status(self):
        """
        get error status.
        """

        self.open_port()

        reply = self.ser.write(str.encode("ERR\n"))
        reply = self.ser.read(3).decode()  # ACK CR LF
        reply = self.ser.write(str.encode("\05"))  # ENQ
        reply = self.ser.read_until().decode()[:-1]  # strip CR

        return reply

    def read_pressure(self, pressure_id=0):
        """
        read pressure in Torr.
        """

        reply = self.command("PR1")

        try:
            # pressure = float(reply[2:])
            pressure = float(reply[2:])
        except Exception as message:
            # azcam.log("Could not read pressure:%s" % message)
            pressure = -999.9
            self.close_port()

        return pressure

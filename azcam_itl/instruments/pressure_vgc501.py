import time

import serial

import azcam
from azcam.functions.utils import check_keyboard


class PressureController(object):
    """
    Pressure controller for Inficon VGC-401, VGC-501, and TPG 361.
    """

    def __init__(self, port="COM1"):

        self.ComPort = port
        # self.BaudRate = 9600
        self.BaudRate = 115200
        self.Parity = serial.PARITY_NONE
        self.ByteSize = 8
        self.StopBits = 1
        self.timeout = 0  # 2.0
        self.RtsCts = 0
        self.XonXoff = 0

        self.ser = 0

    def initialize(self):
        """
        Initialize controller.
        """

        self.close_port()  # might be stuck open

        self.open_port()

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

        self.ser = 0

        return

    def read_port(self, number_bytes):
        """
        Read serial port.
        """

        reply = ""
        byte_count = 0
        loop = 50
        timeout = 1.0
        loop_time = 0.0

        while loop_time < timeout:

            # wait for bytes at port
            for lcount in range(loop):
                current_bytes = self.ser.in_waiting
                if current_bytes == 0:
                    time.sleep(0.01)
                else:
                    break

            if current_bytes > 0:
                reply1 = self.ser.read(current_bytes).decode()
                byte_count += current_bytes
                reply += reply1

            if byte_count >= number_bytes:
                break
            else:
                loop_time += 0.5

        return reply

    def clear(self, showdata=0):
        """
        Clear controller communications.
        """

        self.open_port()

        self.ser.reset_input_buffer()

        loop = 0
        while 1:
            if self.ser.in_waiting == 0:
                break
            reply = self.ser.read(1).decode()
            if showdata:
                print(loop, reply)
            loop += 1

        return

    def command(self, command):
        """
        Send command to controller and read reply.
        """

        self.open_port()

        self.clear()

        self.ser.write(str.encode(f"{command}\r\n"))
        reply = self.read_port(3)
        if reply == "":
            return ""
        # reply = self.ser.read(3).decode()  # ACK CR LF
        if reply[0] == "\x15":
            print("NAK read from pressure controller")
            print(reply)
            return -999.9
        elif reply[0] == "\x06":
            pass
            # print("ACK read from pressure controller")
        else:
            print(f"Bad reply from pressure controller: {reply}")
            pass

        self.ser.write(str.encode("\05"))  # ENQ

        # reply = self.ser.read_until().decode()[:-2]  # strip \r\n
        reply = self.read_port(15)[:-2]  # strip \r\n

        return reply

    def test(self):
        """
        Test controller.
        """

        # self.open_port()

        reply = self.command("TID")

        print(f"Gauge is: {reply}")

        reply = self.command("AYT")
        print(f"System info: {reply}")

        return

    def reset(self):
        """
        Reset controller.
        """

        self.open_port()

        reply = self.command("RES")
        azcam.log(f"Reset reply: {reply}")

        reply = self.command("SEN,2")  # turn on gauge

        return

    def read_continuous_data(self, loop=1):
        """
        Read continuous output before any commands are sent.
        """

        # may need to stop transmission, clear, and then restart
        self.command("TID")
        self.clear()

        reply = self.ser.write(str.encode("COM,1\r\n"))
        reply = self.ser.read(3).decode()  # ACK CR LF

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
            print(f"Reading: {counter}: {p:0.2e} Torr")
            counter += 1
            if check_keyboard(0) == "q":
                break

        return p

    def get_error_status(self):
        """
        get error status.
        """

        self.open_port()

        reply = self.ser.write(str.encode("ERR\r\n"))
        reply = self.ser.read(3).decode()  # ACK CR LF
        reply = self.ser.write(str.encode("\05"))  # ENQ
        reply = self.ser.read_until().decode()[:-2]  # strip CRLF

        return reply

    def read_pressure(self, pressure_id=0):
        """
        read pressure in Torr.
        """

        reply = self.command("PR1")

        try:
            pressure = float(reply[2:])
        except Exception as message:
            # azcam.log(f"Could not read pressure: {reply}")
            pressure = -999.9

        return pressure

    def power(self, state):
        """
        Turn sensor power on or off.
        """

        self.open_port()

        self.command(f"HVC,{state}")

        return

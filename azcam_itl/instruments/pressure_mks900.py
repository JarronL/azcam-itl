import time

import serial

import azcam
import azcam.exceptions


class PressureController(object):
    """
    Pressure controller for MKS900 gauge with PDR900 controller.
    """

    def __init__(self, port):

        self.ComPort = port
        self.BaudRate = 9600
        self.Parity = serial.PARITY_NONE
        self.ByteSize = 8
        self.StopBits = 1
        self.timeout = 0
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
                azcam.exceptions.AzcamError("could not open pressure serial port")

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

    def read_pressure(self, pressure_id: int = 1):
        """
        read pressure in Torr.
        """

        self.close_port()
        self.open_port()

        self.ser.write(str.encode(f"@253PR{pressure_id}?;FF"))
        reply = self.read_port(17)
        if reply == "":
            return -999

        # reply = self.ser.read(17).decode()
        reply = reply[7:14]
        try:
            pressure = float(reply)
        except Exception as message:
            # azcam.log("Could not read pressure:%s" % message)
            pressure = -999

        return pressure

    def command(self, code="SNC?;FF"):
        """
        Create and send a command.
        """

        self.open_port()

        command = f"@253{code}"
        self.ser.write(str.encode(command))

        reply = self.read_port(17)
        # reply = self.ser.read(17).decode()

        self.close_port()

        return reply

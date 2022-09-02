"""
Pollux stages class.

Axes are [1,2,3]
"""

# TODO: reformat to fix cases and variable names

import time

import serial

import azcam


class PolluxCtrl(object):
    def __init__(self):

        self.isInitialized = 0
        self.isOpen = 0
        self.ComPort = "COM3"
        self.BaudRate = 19200
        self.Parity = serial.PARITY_NONE
        self.ByteSize = 8
        self.StopBits = 1
        self.Timeout = 1
        self.RtsCts = 0
        self.XonXoff = 0
        self.maxCtrl = 3

    def initialize(self):

        if self.isInitialized:
            return

        # create serial object
        try:
            self.sPort = serial.Serial(
                port=self.ComPort,
                baudrate=self.BaudRate,
                timeout=self.Timeout,
                parity=self.Parity,
                stopbits=self.StopBits,
                bytesize=self.ByteSize,
                rtscts=self.RtsCts,
                xonxoff=self.XonXoff,
            )
        except Exception as message:
            azcam.log(message)
            self.sPort = 0

        # identify all controllers
        self.nAxis = 0

        if self.sPort != 0 and self.sPort.isOpen():
            self.identify()

        self.isInitialized = 1

        return

    def open_port(self):
        """
        Open serial port.
        26Oct2015 last change Zareba
        """

        if self.sPort == 0:
            try:
                self.sPort = serial.Serial(
                    port=self.ComPort,
                    baudrate=self.BaudRate,
                    timeout=self.Timeout,
                    parity=self.Parity,
                    stopbits=self.StopBits,
                    bytesize=self.ByteSize,
                    rtscts=self.RtsCts,
                    xonxoff=self.XonXoff,
                )

                message = (
                    "Port name = %s" % (self.sPort.name),
                    " Port is open = %s" % (self.sPort.isOpen()),
                )
                return ["OK", message]
            except Exception as message:
                return ["ERROR", message]

        else:
            try:
                if self.sPort.isOpen():
                    message = (
                        "Port name = %s" % (self.sPort.name),
                        " Port is open = %s" % (self.sPort.isOpen()),
                    )
                else:
                    self.sPort.open()
                    message = (
                        "Port name = %s" % (self.sPort.name),
                        " Port is open = %s" % (self.sPort.isOpen()),
                    )

                return ["OK", message]
            except Exception as message:
                return ["ERROR", message]

    def close_port(self):
        """
        Close serial port.
        22Oct2015 last change Zareba
        """

        try:
            if self.sPort != 0:
                self.sPort.close()
                return ["OK"]
            else:
                return ["ERROR", "Port not opened"]
        except Exception as message:
            return ["ERROR", message]

    def get_port_status(self):
        """
        Get serial port status.
        22Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                message = (
                    "Port name = %s" % (self.sPort.name),
                    " Port is open = %s" % (self.sPort.isOpen()),
                )
                return ["OK", message]

            except Exception as message:
                return ["ERROR", message]
        else:
            return ["ERROR", "Serial port is not initialized"]

    def send_cmd(self, Command, getStatus=-1):
        """
        Send command.
        If getStatus != -1 get status after the command is sent to the controller.
        26Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                if self.sPort.isOpen():
                    cmd = Command + "\r\n"

                    reply = self.sPort.write(str.encode(cmd))
                    # self.sPort.flush()

                    if getStatus != -1:
                        reply = self.sPort.readline().decode().strip("\r\n")
                        return ["OK", reply]
                    else:
                        return ["OK"]

                else:
                    return ["ERROR", "Serial port is not opened"]

            except Exception as message:
                return ["ERROR", message]
            pass

        else:
            return ["ERROR", "Serial port is not initialized"]

    def get_reply(self):
        """
        Get reply from the controller. May return an empty string if no response is available.
        26Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                if self.sPort.isOpen():

                    reply = self.sPort.readline().decode().strip("\r\n")
                    return ["OK", reply]
                else:
                    return ["ERROR", "Serial port is not opened"]

            except Exception as message:
                return ["ERROR", message]
            pass

        else:
            return ["ERROR", "Serial port is not initialized"]

    def identify(self, disp=-1):
        """
        Identify.
        23Oct2015 last change Zareba
        """

        self.nAxis = 0
        self.nNames = []

        if self.sPort != 0:

            try:
                if not self.sPort.isOpen():
                    self.sPort = serial.Serial(
                        port=self.ComPort,
                        baudrate=self.BaudRate,
                        timeout=self.Timeout,
                        parity=self.Parity,
                        stopbits=self.StopBits,
                        bytesize=self.ByteSize,
                        rtscts=self.RtsCts,
                        xonxoff=self.XonXoff,
                    )

                for nport in range(1, self.maxCtrl + 1):
                    cmd = str(nport) + "  nidentify\r\n"
                    self.sPort.write(str.encode(cmd))

                    reply = self.sPort.readline().decode().strip("\r\n")

                    if len(reply) > 0:
                        self.nAxis += 1

                        self.nNames.append(reply.strip("r\n"))

                if disp != -1:
                    for nport in range(1, self.maxCtrl + 1):
                        azcam.log("Controller ", nport, " ", self.nNames[nport - 1])

                    message = "Found %s %s" % (self.nAxis, "controllers")
                    return ["OK", message]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def get_error(self, nAxis):
        """
        Get error of nAxis.
        26Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:

                cmd = str(nAxis) + "  gne\r\n"
                self.sPort.write(str.encode(cmd))

                reply = self.sPort.readline().decode().strip("\r\n")

                return ["OK", reply]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def get_pos(self, nAxis, Wait=0):
        """
        Get position of nAxis.
        18May2017 last change Zareba
        """

        if self.sPort != 0:
            try:

                if Wait:
                    loop = 0
                    while loop < 200:
                        reply = self.get_status(nAxis)
                        try:
                            flag = int(reply[1])
                        except Exception as e:
                            flag = 1

                        if flag == 1:
                            loop += 1
                            time.sleep(0.2)
                            continue
                        else:
                            loop = 200

                cmd = str(nAxis) + "  npos\r\n"
                self.sPort.write(str.encode(cmd))

                reply = self.sPort.readline().decode().strip("\r\n")

                reply = float(reply)

                return ["OK", reply]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def get_motion(self, nAxis, Wait=0):
        """
        Get motion. TEST TEST TEST
        04May16 last change MPL
        """

        if self.sPort != 0:
            try:

                loop = 0
                while 1 and loop < 20:
                    reply = self.get_status(nAxis)
                    try:
                        flag = int(reply[1])
                    except Exception as e:
                        flag = 1

                    if Wait:
                        if flag == 1:
                            loop += 1
                            time.sleep(0.2)
                            continue
                        else:
                            return ["OK", flag]
                    else:
                        break

                return ["OK", flag]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def get_status(self, nAxis):
        """
        Get status of nAxis.
        26Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:

                cmd = str(nAxis) + "  nst\r\n"
                self.sPort.write(str.encode(cmd))

                reply = self.sPort.readline().decode().strip("\r\n")

                return ["OK", reply.strip()]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def get_switch_status(self, nAxis):
        """
        Get switch status of nAxis.
        26Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:

                cmd = str(nAxis) + "  getswst\r\n"
                self.sPort.write(str.encode(cmd))

                reply = self.sPort.readline().decode().strip("\r\n")

                return ["OK", reply]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def get_limits(self, nAxis):
        """
        Get limits for nAxis.
        23Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(nAxis) + "  getnlimit\r\n"
                self.sPort.write(str.encode(cmd))

                reply = self.sPort.readline().decode().strip("\r\n")

                return ["OK", reply]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def get_velocity(self, nAxis):
        """
        Get velocity for nAxis.
        26Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(nAxis) + "  gnv\r\n"
                self.sPort.write(str.encode(cmd))

                reply = self.sPort.readline().decode().strip("\r\n")

                return ["OK", reply]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def set_velocity(self, nAxis, value):
        """
        Set velocity for nAxis.
        26Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(format(value, "f")) + " " + str(nAxis) + "  snv\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def get_acceleration(self, nAxis):
        """
        Get acceleration for nAxis.
        23Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(nAxis) + "  gna\r\n"
                self.sPort.write(str.encode(cmd))

                reply = self.sPort.readline().decode().strip("\r\n")

                return ["OK", reply]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def set_acceleration(self, nAxis, value):
        """
        Set acceleration for nAxis.
        23Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(format(value, "f")) + " " + str(nAxis) + "  sna\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def move_absolute(self, nAxis, pos):
        """
        Move to absolute position.
        24Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(format(pos, "f")) + " " + str(nAxis) + "  nm\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def move_relative(self, nAxis, step):
        """
        Move relative.
        24Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(format(step, "f")) + " " + str(nAxis) + "  nr\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def calibrate(self, nAxis):
        """
        Calibrate nAxis - move to the left position.
        24Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(nAxis) + "  ncal\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def range_measure(self, nAxis):
        """
        Measure range of nAxis - move to the right position.
        24Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(nAxis) + "  nrm\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def set_home(self, nAxis):
        """
        Set home position for nAxis.
        24Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(0) + " " + str(nAxis) + "  setnpos\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def home(self, nAxis):
        """
        Go to home position for nAxis - equivalent to the absolute move to 0 position.
        24Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(0) + " " + str(nAxis) + "  nm\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def reset(self, nAxis):
        """
        Reset controller.
        24Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(nAxis) + "  nreset\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def reset_all(self):
        """
        Reset controller.
        24Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:

                for nport in range(1, self.maxCtrl + 1):
                    cmd = str(nport) + "  nreset\r\n"
                    self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

    def stop_all(self):
        """
        Stop movement for all controllers (axis).
        24Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = chr(0x03) + "\r\n"
                self.sPort.write(str.encode(cmd))

                return ["OK"]

            except Exception as message:
                return ["ERROR", message]

        else:
            return ["ERROR", "Serial port is not initialized"]

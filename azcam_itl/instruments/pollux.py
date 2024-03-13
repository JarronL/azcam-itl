"""
Pollux stages class.

Axes are [1,2,3]

Serial port is mapped to COM13 on quantum PC through moxaeb. 
"""

# TODO: reformat to fix cases and variable names

import time

import serial

import azcam
import azcam.exceptions


class PolluxCtrl(object):
    def __init__(self):
        self.initialized = 0
        self.isOpen = 0
        self.ComPort = "COM13"
        self.BaudRate = 19200
        self.Parity = serial.PARITY_NONE
        self.ByteSize = 8
        self.StopBits = 1
        self.Timeout = 1
        self.RtsCts = 0
        self.XonXoff = 0
        self.maxCtrl = 3

        self.valid_axes = [1, 2, 3]

    def initialize(self):
        if self.initialized:
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

        self.initialized = 1

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

    def send_cmd(self, command: str, readback: bool = True):
        """
        Send a command to the pollux stage and optional read reply.
        Includes string cleanup.
        """

        if self.sPort.isOpen():
            cmd = command + "\r\n"

            reply = self.sPort.write(str.encode(cmd))
            # self.sPort.flush()

            if readback:
                reply = self.sPort.readline().decode().strip("\r\n").strip()
                return reply
            else:
                return

        else:
            raise azcam.exceptions.AzcamError("Pollux serial port not open")

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

        cmd = str(nAxis) + "  gne\r\n"
        try:
            reply = self.send_cmd(cmd, True)
        except Exception:
            reply = self.send_cmd(cmd, True)

        return reply

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
                while 1 and loop < 100:
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
        """

        cmd = str(nAxis) + "  nst"
        reply = self.send_cmd(cmd, True)

        return ["OK", reply]

    def get_switch_status(self, nAxis):
        """
        Get switch status of nAxis.
        26Oct2015 last change Zareba
        """

        if self.sPort != 0:
            try:
                cmd = str(nAxis) + "  getswst\r\n"
                self.sPort.write(str.encode(cmd))

                reply = self.sPort.readline().decode().strip("\r\n").strip()

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

        cmd = str(nAxis) + "  getnlimit"

        reply = self.send_cmd(cmd, True)
        return ["OK", reply]

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
        """

        cmd = str(format(value, "f")) + " " + str(nAxis) + "  snv"
        self.send_cmd(cmd, False)

        return

    def get_acceleration(self, nAxis):
        """
        Get acceleration for nAxis.
        23Oct2015 last change Zareba
        """

        cmd = str(nAxis) + "  gna"
        reply = self.send_cmd(cmd, True)

        return reply

    def set_acceleration(self, nAxis, value):
        """
        Set acceleration for nAxis.
        23Oct2015 last change Zareba
        """

        cmd = str(format(value, "f")) + " " + str(nAxis) + "  sna"
        self.send_cmd(cmd, False)

        return

    def move_absolute(self, nAxis, pos):
        """
        Move to absolute position.
        """

        cmd = str(format(pos, "f")) + " " + str(nAxis) + "  nm"
        self.send_cmd(cmd, False)

        return

    def move_relative(self, nAxis, step):
        """
        Move relative.
        """

        cmd = str(format(step, "f")) + " " + str(nAxis) + "  nr"
        self.send_cmd(cmd, False)

        return

    def calibrate(self, nAxis):
        """
        Calibrate nAxis - move to the left position.
        24Oct2015 last change Zareba
        """

        self.get_error(nAxis)

        cmd = str(nAxis) + "  ncal"
        self.send_cmd(cmd, False)

        self.get_motion(nAxis, True)

        return

    def range_measure(self, nAxis):
        """
        Measure range of nAxis - move to the right position.
        """

        cmd = str(nAxis) + "  nrm"
        self.send_cmd(cmd, False)

        self.get_motion(nAxis, True)

        return

    def set_home(self, nAxis):
        """
        Set home position for nAxis.
        """

        cmd = str(0) + " " + str(nAxis) + "  setnpos"
        self.send_cmd(cmd, False)

        return

    def go_home(self, nAxis):
        """
        Go to home position for nAxis - equivalent to the absolute move to 0 position.
        """

        cmd = str(0) + " " + str(nAxis) + "  nm"
        self.send_cmd(cmd, False)

        return

    def reset(self, nAxis):
        """
        Reset controller.
        """

        cmd = str(nAxis) + "  nreset\r\n"
        self.send_cmd(cmd, False)

        return

    def reset_all(self):
        """
        Reset all controllers.
        """

        for nAxis in range(1, self.maxCtrl + 1):
            self.reset(nAxis)

        return

    def stop_all(self):
        """
        Stop movement for all controllers.
        """

        cmd = chr(0x03)
        self.send_cmd(cmd, False)

        return

import pyvisa

"""
Install PYVISA from NI and pip install pyvisa
"""


class VisaComm(object):
    """
    Class for VISA GPIB communications.
    Common class used by all VISA (GPIB) instruments.
    """

    def __init__(self, Adress):

        self.Adress = Adress
        self.timeout = 60000  # default 60 sec timeout

        # logging for debug
        # pyvisa.log_to_screen()

    def open_comm(self):
        """
        Open communications to hardware and test.
        """
        self.rm = pyvisa.ResourceManager()
        self.rm.list_resources()

        self.instr = self.rm.open_resource(self.Adress)

        self.clear_bus()

        return

    def set_timeout(self, Timeout=-1):
        """
        Set communications timeout  in millisecs.
        Use -1 for no timeout.
        """

        if Timeout == -1:
            del self.instr.timeout
        else:
            self.instr.timeout = Timeout

        return

    def clear_bus(self):
        """
        Clear any data on communication bus.
        """

        self.set_timeout(10)

        # clear bus
        loop = 1
        while loop:
            try:
                self.receive()
            except Exception:
                loop = 0

        self.set_timeout(self.timeout)

        return

    def command(self, Command):
        """
        Write command to instrument and return reply.
        """

        reply = self.instr.query(Command)
        reply = reply.strip()

        return reply

    def send(self, Command):
        """
        Send command to instrument (no reply is read).
        """

        self.instr.write(Command)

        return

    def receive(self):
        """
        Read VISA "bus" (without first sending command).
        """

        reply = self.instr.read()

        return reply

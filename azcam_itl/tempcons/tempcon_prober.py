import azcam
from azcam.tools.tempcon import TempCon


class TempConProber(TempCon):
    def __init__(self, tool_id="tempcon", description="prober tempcon"):

        super().__init__(tool_id, description)

    def get_temperature(self, temperature_id: int = 0):
        """
        Read temperature from prober instrument.
        """

        reply = azcam.db.tools["instrument"].get_temperature()
        temp = float(reply)

        return temp

    def get_temperatures(self, temperature_id: int = 0):
        """
        Read temperature from prober instrument.
        """

        temp = self.get_temperature()

        return [temp, temp]

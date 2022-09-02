"""
Server-side script for instrument checkout
Makes "ITL" in LEDs on Keithley switcher
"""

import sys

import azcam


def switcher_setup_script():
    """ """

    # Usage: load switcher_setup_script.py
    azcam.db.tools["instrument"].switcher.open_all()

    # make ITL on front panel
    leds = [
        "1!1",
        "1!2",
        "1!3",
        "1!4",
        "1!5",
        "1!13",
        "1!23",
        "1!31",
        "1!32",
        "1!33",
        "1!34",
        "1!35",
        "2!1",
        "2!2",
        "2!3",
        "2!4",
        "2!5",
        "2!13",
        "2!23",
        "2!33",
        "3!1",
        "3!11",
        "3!21",
        "3!31",
        "3!32",
        "3!33",
        "3!34",
    ]

    for chan in leds:
        azcam.db.tools["instrument"].switcher.close_switch(chan)

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    switcher_setup_script(*args)

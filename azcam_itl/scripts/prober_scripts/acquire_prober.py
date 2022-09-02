# Acquire AC data using the ITL Prober.

import datetime
import os
import time

import azcam
from azcam_itl import itlutils


def run_script(script_name):
    """
    Runs a script, either with absolute path or assumes it is in the search path.
    This method is exposed as the *Run* command when using IPython.

    :param str script_name: filename of script to run
    :return None:
    """

    # find arguments
    args = ""
    cmd = script_name.split(" ")
    if len(cmd) != 1:
        script_name = cmd[0]
        args = " ".join(cmd[1:])

    # find the file
    # try script_name as-is
    try:
        reply = azcam.utils.find_file(script_name, 1)
        script_name = reply
    except FileNotFoundError:
        # try ScriptName.py
        try:
            reply = azcam.utils.find_file(script_name + ".py", 1)
            script_name = reply
        except azcam.AzcamError:
            try:
                # try ScriptName.pyw
                reply = azcam.utils.find_file(script_name + ".pyw", 1)
                script_name = reply
            except azcam.AzcamError as e:
                raise azcam.AzcamError(f"could not run script {script_name}: {e}")

    # fix the slashes
    sname = os.path.abspath(script_name)

    # run it
    s = "run %s %s" % (sname, args)
    azcam.db.ip.magic(s)

    return


def acquire_prober(acquire_script=""):
    """
    Acquire a suite of test images for all amps of a detector.
    """

    # special case for console code using hardware directly
    from azcam_itl.instruments.instrument_prober import ProberInstrument

    instrument = ProberInstrument()

    # set DEBUG to test without prober hardware
    DEBUG = 0

    # add script names here, they keys are "DEVICE ID" from prober
    acquire_scripts = {
        "STA4150": "acquire_prober_sta4150",
        "LSST": "acquire_prober_lsst",
        "VIRUS": "acquire_prober_virus",
    }

    die_names = {}
    # STA3800
    die_names["lsst"] = {"X0Y0": 3, "X0Y1": 1, "X1Y0": 4, "X1Y1": 2}

    # STA4400
    die_names["wfs"] = {
        "X0Y0": 7,
        "X0Y1": 5,
        "X0Y2": 3,
        "X0Y3": 1,
        "X1Y0": 8,
        "X1Y1": 6,
        "X1Y2": 4,
        "X1Y3": 2,
    }

    # VIRUS
    die_names["virus"] = {
        "X0Y2": "1",
        "X1Y2": "2",
        "X2Y2": "3",
        "X0Y1": "4",
        "X1Y1": "5",
        "X2Y1": "6",
        "X0Y0": "7",
        "X1Y0": "8",
        "X2Y0": "9",
    }

    # STA4150
    die_names["desi"] = {"X0Y0": 1}

    print("\nStarting AcquireProber\n")

    run_acquire_script = 1

    Wait = 1

    # initialize communication to prober
    if not DEBUG:
        azcam.db.tools["instrument"].initialize()

    # check device ID from prober
    if not DEBUG:
        device_id = azcam.db.tools["instrument"].prober.command("$?PDLD")
        device_id = device_id[1:].strip('"')
    else:
        device_id = "LSST"
    print("Prober reports device ID is: %s" % device_id)

    if device_id in acquire_scripts:
        acquire_script = acquire_scripts[device_id]
    else:
        print("acquisition script not found - Aborting!")
        print("   Valid names are:")
        print(acquire_scripts.keys())
        print()
        return

    # check temperature
    if not DEBUG:
        temp = instrument.get_temperature()
    else:
        temp = -99.99
    print("Prober reports temperature is %.1f" % temp)

    # close azcamtool to avoid conflict
    print()
    input("Close azcamtool now to avoid conflict - press Enter to continue....")
    print()

    if not DEBUG:
        reply = instrument.prober.clear_bus()

    # create log file
    cd = azcam.utils.curdir()
    with open(os.path.join(cd, "proberlog.txt"), "a+") as f:
        datestring = time.strftime("%m/%d/%Y")
        timestring = time.strftime("%H:%M:%S")
        titlestr = "# prober log file: %s:%s" % (datestring, timestring)
        f.write(titlestr + "\n")
        f.flush()

        # wait for Test Start from prober
        count = 0
        counters = ["|", "/", "|", "\\"]
        print("Waiting for prober TS command (press q to exit)...")
        while Wait:
            try:
                print(counters[count % 4], end="\r")
                if not DEBUG:
                    instrument.prober.set_timeout(1000)
                    reply = instrument.prober.receive()
                else:
                    time.sleep(1)
            except Exception:
                count += 1
                key = azcam.utils.check_keyboard()
                if key == "q":
                    print()
                    return
                continue

            # exit with no hardware
            if DEBUG:
                return

            print()
            reply = reply.strip()
            if reply == "":
                continue
            print("Prober command received: %s" % reply)
            # f.write('command from prober: %s\n' % reply)

            instrument.prober.set_timeout(60000)

            if reply == "TS":

                print("Received Test Start from prober...")

                reply = instrument.prober.command("$?PDLD")
                product = reply[1:].strip('"')

                reply = instrument.prober.command("?W0")
                wafer = reply  # includes lot number: devicetype-lotname-01

                reply = instrument.prober.command("?P")  # example:X-2Y3
                position = reply
                name = "%s_%s_%s" % (product, wafer, position)

                # log info
                diename = die_names[product.lower()][position]
                logdata = "AC_probed: %s die: %s temp: %.1f" % (name, diename, temp)
                f.write("%s\n" % logdata)
                f.flush()

                s = "%s %s" % (acquire_script, name)
                time.sleep(2)
                if run_acquire_script:
                    print("Running %s" % s)
                    run_script(s)
                else:
                    print("Debug: not running %s" % s)

                # reply to prober test is complete
                reply = instrument.prober.send("TC0")

                Wait = 1

            elif reply == "PC":
                print("Wafer is complete, waiting for next wafer...")
                print()
                Wait = 1

            elif reply == "EC1":
                print("Cassette is finished, stopping testing.")
                Wait = 0

            else:
                print("Unexpected command:%s, waiting..." % reply)
                Wait = 1

    # send email notice
    finishedtime = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
    message = "Prober script finished today at: %s" % (finishedtime)
    itlutils.mailto("holguin@itl.arizona.edu", "AcquierProber acquire script finished", message)

    return reply

# grade .dcparsed files

import os

import azcam


def grade_dcparse_file(filename):
    """
    Grade a .dcparsed data file.
    """

    startfolder = azcam.utils.curdir()
    header_lines = 3

    # indexes to data file
    # index_pin1 = 1
    # index_pin2 = 2
    index_type1 = 5
    index_type2 = 6
    index_name1 = 3
    index_name2 = 4
    index_ohms = 7

    # check filetype
    if not filename.endswith(".dcparsed"):
        return "ERROR filename not type .dcparsed"

    # move to folder and read input file
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    azcam.utils.curdir(dirname)
    with open(basename, "r") as fin:
        if not fin:
            azcam.utils.curdir(startfolder)
            return "ERROR could not open file %s" % filename

        lines_in = fin.readlines()
    fin.close()
    numlines = len(lines_in)

    n = 0
    numfails = 0
    for line in lines_in:
        line = line.strip()
        if len(line) == 0:
            continue
        n += 1

        # ship header
        if n <= header_lines:
            continue

        key = azcam.utils.check_keyboard(0)
        if key == "q" or key == "Q":
            print("Aborting...")
            azcam.utils.curdir(startfolder)
            return "ABORTED from keyboard"

        tokens = azcam.utils.parse(line)
        if len(tokens) == 0:
            continue
        if tokens[0] == "#":
            continue
        try:
            # pin1 = tokens[index_pin1]
            # pin2 = tokens[index_pin2]
            name1 = tokens[index_name1]
            name2 = tokens[index_name2]
            type1 = tokens[index_type1]
            type2 = tokens[index_type2]
            ohms = abs(float(tokens[index_ohms]))
        except Exception as message:
            if n != numlines:  # ignore last line error
                print("ERROR parsing line %d:%s" % (n, repr(message)))
                # azcam.utils.curdir(startfolder)
                # fout.close()
                # return 'ERROR parsing line %d:%s' % (n,repr(message))

        # **********************************************************************
        # grading section
        # **********************************************************************

        # make changes here!!!
        current_limit = 2500.0
        short_limit = 20.0e6
        gate_short_limit = 20.0e6  # 10 megaohms for gates (clocks)

        # quiet = 0

        # unshorted pins
        if ohms > short_limit:
            pass

        # same names and current limited
        elif name1 == name2 and ohms < current_limit:
            pass

        # both pins are grounds and current limited
        elif type1 == "GND" and type2 == "GND" and ohms < current_limit:
            pass

        # both pins are grounds and high resistance
        elif type1 == "GND" and type2 == "GND" and (current_limit < ohms < short_limit):
            pass

        # both pins are diodes and current limited
        elif type1 == "DIODE" and type2 == "DIODE" and ohms < current_limit:
            pass

        # pins are diode and ground and current limited
        elif type1 == "DIODE" and type2 == "GND" and ohms < current_limit:
            pass

        # both pins ground and diode and current limited
        elif type1 == "GND" and type2 == "DIODE" and ohms < current_limit:
            pass

        # pins are diode and ground and high resistance
        elif (
            type1 == "DIODE" and type2 == "GND" and (current_limit < ohms < short_limit)
        ):
            pass

        # both pins ground and diode and high resistance
        elif (
            type1 == "GND" and type2 == "DIODE" and (current_limit < ohms < short_limit)
        ):
            pass

        # both pins are diodes and high resistance
        elif (
            type1 == "DIODE"
            and type2 == "DIODE"
            and (current_limit < ohms < short_limit)
        ):
            pass

        # ignore if either is an NC pin
        elif name1 == "NC" or name2 == "NC":
            pass

        # optional - ignore high resistance grounds
        elif type1 == "GND" and type2 == "GND" and (current_limit < ohms < short_limit):
            pass

        # additional grading
        elif type1 == "GATE" and type2 == "GND" and (ohms > gate_short_limit):
            pass
            print("*** highrho pass")

        elif type1 == "GND" and type2 == "GATE" and (ohms > gate_short_limit):
            pass
            print("*** highrho pass")

        # everything else
        else:
            numfails += 1

        # **********************************************************************
        # printout section
        # **********************************************************************

        """
        s = "%05d %-7s %-7s %7s %7s %5s %5s %10.3g" % (
            n,
            pin1,
            pin2,
            name1,
            name2,
            type1,
            type2,
            ohms,
        )
        """

    if numfails == 0:
        Grade = "PASS"
    else:
        # s = "Number_Fails: %d" % numfails
        Grade = "FAIL"

    azcam.utils.curdir(startfolder)

    return Grade


# SPECIAL
"""
elif pin1.startswith("SC") or pin2.startswith("SC"):
    print("*** Ignoring scupper")
    # quiet=1
    pass

# SPECIAL
elif pin1.startswith("S3") and pin2.startswith("RD"):
    print("*** Ignoring S3-RD short")
    # quiet=1
    pass
"""

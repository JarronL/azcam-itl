# script to parse .dcprobe files

import os
import shlex

import azcam


def parse_dcprobe_file(filename, CurrentLimit=-1, ShortLimit=-1):
    """
    Parse ITL .dcprobe data file.
    Verbose = 0 => no printout during analysis
            = 1 => print every line
            = 2 => print outputs only
    """

    startfolder = azcam.utils.curdir()
    header_lines = 3

    # indexes to data file
    # index_current = 2
    index_pin1 = 3
    index_pin2 = 4
    index_name1 = 5
    index_name2 = 6
    index_type1 = 7
    index_type2 = 8
    index_ohms = 9
    # index_flag = 10

    # check filetype
    if not filename.endswith(".dcprobe"):
        return "ERROR filename not type .dcprobe"

    # test limits
    if CurrentLimit == -1:
        current_limit = 2500.0  # ohms: < this is current limited
    else:
        current_limit = float(CurrentLimit)
    if ShortLimit == -1:
        short_limit = 20.0e6  # ohms: > this not shorted
    else:
        short_limit = float(ShortLimit)

    # move to folder and read input file
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    azcam.utils.curdir(dirname)
    with open(basename, "r") as fin:
        if not fin:
            azcam.utils.curdir(startfolder)
            return "ERROR could not open file %s" % filename

        lines_in = fin.readlines()
    numlines = len(lines_in)

    outfile = basename.rstrip(".dcprobe")
    outfile = outfile + ".dcparsed"

    # open output file (report)
    with open(outfile, "w") as fout:

        # write report file header
        s = "# %s" % basename
        fout.write(s + "\n")
        s = "# Input_File: %s" % filename
        fout.write(s + "\n")
        s = "# Parser_Parameters: Current_Limit: %.0f Ohms, Short_Limit: %.0f Ohms" % (
            current_limit,
            short_limit,
        )
        fout.write(s + "\n")

        chanlist = lines_in[1].split(".txt")[0]
        s = "# Channel_List: %s" % chanlist
        fout.write(s + "\n")
        fout.write("#\n")

        print("Processing %s to %s" % (filename, outfile))

        lines_out = []
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
                fout.close()
                return "ABORTED from keyboard"

            lex = shlex.shlex(line)
            lex.whitespace_split = True
            tokens = list(lex)
            try:
                pin1 = tokens[index_pin1]
                pin2 = tokens[index_pin2]
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
            # analysis section
            # **********************************************************************

            # unshorted pins
            if ohms > short_limit:
                rule = "unshorted"

            # same names and current limited
            elif name1 == name2 and ohms < current_limit:
                rule = "samename"

            # both pins are grounds and current limited
            elif type1 == "GND" and type2 == "GND" and ohms < current_limit:
                rule = "grounds"

            # both pins are grounds and high resistance
            elif (
                type1 == "GND"
                and type2 == "GND"
                and (current_limit < ohms < short_limit)
            ):
                rule = "grounds"

            # both pins are diodes and current limited
            elif type1 == "DIODE" and type2 == "DIODE" and ohms < current_limit:
                rule = "diodes"

            # pins are diode and ground and current limited
            elif type1 == "DIODE" and type2 == "GND" and ohms < current_limit:
                rule = "diodes"

            # both pins ground and diode and current limited
            elif type1 == "GND" and type2 == "DIODE" and ohms < current_limit:
                rule = "diodes"

            # pins are diode and ground and high resistance
            elif (
                type1 == "DIODE"
                and type2 == "GND"
                and (current_limit < ohms < short_limit)
            ):
                rule = "diodes"

            # both pins ground and diode and high resistance
            elif (
                type1 == "GND"
                and type2 == "DIODE"
                and (current_limit < ohms < short_limit)
            ):
                rule = "diodes"

            # both pins are diodes and high resistance
            elif (
                type1 == "DIODE"
                and type2 == "DIODE"
                and (current_limit < ohms < short_limit)
            ):
                rule = "diodes"

            # ignore if either is an NC pin
            elif name1 == "NC" or name2 == "NC":
                rule = "nc"

            # optional - ignore high resistance grounds
            elif (
                type1 == "GND"
                and type2 == "GND"
                and (current_limit < ohms < short_limit)
            ):
                rule = "grounds"

            # fail everything else
            else:
                rule = "fail"
                numfails += 1

            # **********************************************************************
            # printout section
            # **********************************************************************

            if (
                rule == "unshorted"
                or rule == "samename"
                or rule == "grounds"
                or rule == "diodes"
                or rule == "nc"
            ):
                pnt = 0
            else:
                pnt = 1  # was 1
            if pnt:
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
                print(s)
                lines_out.append(s + "\n")

            # limit testing for debug
            # if n>500: break

        s = "Combinations: %d" % n
        fout.write("# %s\n" % s)
        if numfails > 0:
            s = "Number_Fails: %d" % numfails
            print(s)
            fout.write("# %s\n" % s)
        fout.write("#\n")

        # write data to file
        fout.writelines(lines_out)

    azcam.utils.curdir(startfolder)
    return "OK"

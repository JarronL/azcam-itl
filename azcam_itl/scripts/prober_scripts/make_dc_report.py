"""
Run grade_dcparse_file on a batch of files

Usage:
 First Run parse_dcprobe_batch.py to create .dcparsed files.
 Then Run make_dc_report.py on folder with .dcparsed files to create final report.
"""

import os
import sys

import azcam


def grade_dcparse_batch(lot):
    """
    Parse a batch of ITL prober .dcprobe data files.
    """

    from .grade_dcparse_file import grade_dcparse_file

    PARSE = 1

    # STA3800
    die_names_sta3800 = {"X0Y0": 3, "X0Y1": 1, "X1Y0": 4, "X1Y1": 2}

    # STA4400
    die_names_sta4400 = {
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
    die_names_sta3600 = {
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
    die_names_sta4150 = {"X0Y0": 1}

    # changeme!
    die_names = die_names_sta3600

    root = azcam.utils.curdir()

    # flag for subfolders
    UseCurrentFolderOnly = 1

    if UseCurrentFolderOnly:
        print("Processing root folder only")

    print()
    print("Press q to quit or any other key to continue...")
    key = ""
    # key=azcam.utils.check_keyboard(1)
    if key.lower() == "q":
        return

    # make a list of filenames
    filenames = []
    if UseCurrentFolderOnly:
        filenames = [f for f in os.listdir(".") if os.path.isfile(f)]
    else:

        for root, directories, files in os.walk("./"):
            for filename in files:
                if not filename.endswith(".dcparsed"):
                    continue
                filename = os.path.join(root, filename)
                filename = os.path.abspath(filename)
                filename = os.path.normpath(filename)
                filenames.append(filename)

    if len(filenames) == 0:
        raise azcam.AzcamError("No .dcparsed files found")

    lines = []
    numfail = 0
    numpass = 0
    numfiles = 0
    for f in filenames:

        if f.endswith(".dcparsed"):
            numfiles += 1

            reply = grade_dcparse_file(f)

            if reply == "FAIL":
                numfail += 1
            elif reply == "PASS":
                numpass += 1

            s = "%s ==> %s" % (f, reply)
            lines.append(s + "\n")

    if numfiles == 0:
        raise azcam.AzcamError("No .dcparsed files found")

    # create report file
    ofile = f"Lot{lot}_dc_prober_report"
    with open(ofile + ".txt", "w") as fout:

        # stats
        s = "# Number pass: %d [%4.01f%%]" % (numpass, 100.0 * numpass / numfiles)
        print(s)
        fout.write(s + "\n")
        s = "# Number fail: %d [%4.01f%%]" % (numfail, 100.0 * numfail / numfiles)
        print(s)
        fout.write(s + "\n")
        s = "# Number total: %d" % numfiles
        print(s)
        fout.write(s + "\n")
        fout.write("\n")

        # write data to report file

        # do some parsing
        dcdata = []
        if PARSE:

            # header
            s = "# Wafer  Die    Lot      Position  Grade"
            fout.write(s + "\n")

            # file format should be:
            #    ProductFile_DeviceID-LotID-Wafer_XxYx.dcprobe
            #    Ex: LSST_STA3800C-180928-24_X1Y1.dcprobe

            index = 0
            for line in lines:
                groups = azcam.utils.parse(line)  # get groups
                g0 = groups[0]
                tokens = g0.split("_")  # split group

                if 1:  # LSST
                    lot = tokens[1].split("-")[1]
                    wafer = tokens[1].split("-")[2]
                    position = tokens[2].split(".")[0]
                    g2 = groups[2]
                    grade = g2

                else:  # VIRUS
                    lot = tokens[2]
                    wafer = tokens[3]
                    position = tokens[4].split(".")[0]
                    g2 = groups[2]
                    grade = g2

                # translate die name
                diename = die_names[position]

                # save for sorting
                dcdata.append([int(wafer), int(diename), grade, int(lot), position])
                index += 1

        # or write directly
        else:
            fout.writelines(lines)

        if not PARSE:
            return

        # sort and write to report file
        dcdata.sort()

        for d in dcdata:
            if d[2] == "PASS":
                s = "%-5d    %02d %10d %6s %9s <==" % (d[0], d[1], d[3], d[4], d[2])
            else:
                s = "%-5d    %02d %10d %6s %9s" % (d[0], d[1], d[3], d[4], d[2])
            fout.write(s + "\n")

    # write a datafile, use from xxx import dcdata to restore
    with open(ofile + ".py", "w") as datafile:
        datafile.write(f"dcdata={repr(dcdata)}\n")

    # finish
    print("Finished! Variable dcdata contains results")

    return dcdata


if __name__ == "__main__":
    args = sys.argv[1:]
    dcdata = grade_dcparse_batch(*args)

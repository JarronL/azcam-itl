# make prober report from AC and DC grade files
# 21Jan18 last change MPL

import os

import azcam


def make_ac_report():

    # folders to skip, starting string
    SkipFolders = []

    # VIRUS
    """
    DIENAME={
        'X0Y2':'1',
        'X1Y2':'2',
        'X2Y2':'3',
        'X0Y1':'4',
        'X1Y1':'5',
        'X2Y1':'6',
        'X0Y0':'7',
        'X1Y0':'8',
        'X2Y0':'9',
        }
    """

    # STA3800
    #   """
    DIENAME = {"X0Y0": 3, "X0Y1": 1, "X1Y0": 4, "X1Y1": 2}
    #    """

    # STA4150
    # DIENAME={'X0Y0':1}

    # STA4400
    """
    DIENAME={
        'X0Y0':7,
        'X0Y1':5,
        'X0Y2':3,
        'X0Y3':1,
        'X1Y0':8,
        'X1Y1':6,
        'X1Y2':4,
        'X1Y3':2,
        }
        """

    QUIT = 0
    lines = []
    NumTests = 0
    NumPass = 0
    NumACPass = 0
    NumFail = 0
    NumACFail = 0
    NumUnknown = 0
    NumTotal = 0
    data = []

    for root, dirs, files in os.walk("."):

        # optionally skip some folders
        sbreak = 0
        for skip in SkipFolders:
            if root.startswith(skip):
                print("Skipping", root)
                sbreak = 1
                break
        if sbreak:
            continue

        for f in files:

            tokens = f.split("_")
            if len(tokens) != 4:  # 4 for LSST, 7 for VIRUS
                continue

            if tokens[0].startswith("PASS"):
                ACGRADE = "PASS"
                NumACPass += 1
            elif tokens[0].startswith("FAIL"):
                ACGRADE = "FAIL"
                NumACFail += 1
            else:
                continue
                # ACGRADE='UNKNOWN'

            if 1:  # LSST
                ID = tokens[2].split("-")
                wafer = int(ID[2])
                device = tokens[3].strip(".txt")
                die = DIENAME[device]
                die = int(die)
                lot = tokens[2].split("-")[0]

            else:  # VIRUS
                wafer = int(tokens[5])
                device = tokens[6].split(".")[0]
                die = DIENAME[device]
                die = int(die)
                lot = tokens[4]

            if ACGRADE == "PASS":
                NumPass += 1
            elif ACGRADE == "FAIL":
                NumFail += 1
            else:
                NumUnknown += 1

            # save for sorting
            grade = ACGRADE
            data.append([wafer, die, grade, device, lot])

            NumTotal += 1

    # write output prober file
    ofile = os.path.join("./", "ac_prober_report.txt")
    with open(ofile, "w") as outfile:
        s = "# Top folder: " + azcam.utils.curdir() + "\n"
        outfile.writelines(s)

        s = "# Total AC Pass: %d/%d, Unknown: %d" % (NumACPass, NumTotal, NumUnknown)
        outfile.writelines(s + "\n")

        s = "# Total AC Fail: %d/%d" % (NumACFail, NumTotal)
        outfile.writelines(s + "\n")

        s = "# Wafer\tDie\tID\t\tPos\tAC_Grade\n"
        outfile.writelines(s + "\n")
        data.sort()

        for d in data:
            if d[2] == "PASS":
                s = "%02d\t%02d\t%6s\t%s\t%s <==" % (d[0], d[1], d[4], d[3], d[2])
            else:
                s = "%02d\t%02d\t%6s\t%s\t%s" % (d[0], d[1], d[4], d[3], d[2])
            outfile.write(s + "\n")

    return

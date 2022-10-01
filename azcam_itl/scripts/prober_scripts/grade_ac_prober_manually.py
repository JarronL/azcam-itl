# display and grade prober AC files interactively on ds9

import os
import sys
import time

import azcam
from azcam.utils import beep


def grade_ac_prober_file(filename, Grader=""):

    FreqYES = 2500  # Set Frequency To 2500 Hertz
    DurYES = 500  # Set Duration To 1000 ms == 1 second
    FreqNO = 1000  # Set Frequency To 2500 Hertz
    DurNO = 500  # Set Duration To 1000 ms == 1 second
    FreqATTN = 2000  # Set Frequency To 2500 Hertz
    DurATTN = 500  # Set Duration To 1000 ms == 1 second

    # folders to skip, starting string
    SkipFolders = []

    print()
    print("*** Display prober files on ds9 ***")
    print()
    print(
        "The options below are Return for next image, Snap, Pass, Fail, or Quit... ",
        end=" ",
    )
    print()

    # STA3800
    # """
    DIENAME = {"X0Y0": 3, "X0Y1": 1, "X1Y0": 4, "X1Y1": 2}
    # """

    # STA3600
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

    top = azcam.utils.curdir()

    # remove tempfile from previous runs
    tempfile = os.path.join(top, "TempDisplayFile")
    azcam.db.tools["display"].TempDisplayFile = tempfile
    if os.path.exists(tempfile):
        os.remove(tempfile)

    # get top level device folders
    for root, topfolders, filenames in os.walk("."):
        break

    # loop through all folders
    for topfolder in topfolders:

        sbreak = 0
        for skip in SkipFolders:
            if topfolder.startswith(skip):
                print("Skipping", topfolder)
                sbreak = 1
                break
        if sbreak:
            continue

        topfolder = os.path.abspath(os.path.join(top, topfolder))
        idstring = os.path.basename(topfolder)
        idstring = idstring.replace("#", "_")

        azcam.utils.curdir(topfolder)
        print()
        print("folder:", topfolder)
        print()
        passfile = os.path.join(top, "PASS-AC_%s.txt" % idstring)
        failfile = os.path.join(top, "FAIL-AC_%s.txt" % idstring)

        # walk through subfolders
        QUIT = 0
        NEXT = 0
        for root, dirnames, filenames in os.walk("."):

            if QUIT or NEXT:
                break

            sbreak = 0
            for skip in SkipFolders:
                if root.startswith(skip):
                    print("Skipping", root)
                    sbreak = 1
                    break
            if sbreak:
                continue

            numfiles = len(filenames)
            if "test.fits" in filenames:
                numfiles -= 1
            if "PASS.txt" in filenames:
                numfiles -= 1
            if "FAIL.txt" in filenames:
                numfiles -= 1

            n = 0
            QUIT = 0
            NEXT = 0
            if len(filenames) == 0:
                continue

            # new
            dienum = -1
            for die in DIENAME:
                if die in topfolder:
                    dienum = DIENAME[die]
                    break

            for f in filenames:
                n += 1
                if f == "test.fits":
                    continue
                if not f.endswith(".fits"):
                    continue

                print("Die: %02d, File %d/%d: %s" % (int(dienum), n, len(filenames), f))

                filename = os.path.join(root, f)
                filename = os.path.abspath(filename)
                snapfile = filename.replace(".fits", ".png")
                azcam.db.tools["display"].display(filename)
                azcam.db.tools["display"].zoom(0)

                QUIT = 0
                NEXT = 0
                while 1:
                    print("Enter return, s, p, f, or q: ", end=" ")
                    c = azcam.utils.check_keyboard(1).lower()
                    if c == "q":
                        QUIT = 1
                        break
                    elif c == "s":
                        print(azcam.db.tools["display"].SaveImage(snapfile))
                    elif c == "p":
                        beep(FreqYES, DurYES)
                        open(passfile, "w")
                        NEXT = 1
                        break
                    elif c == "f":
                        beep(FreqNO, DurNO)
                        open(failfile, "w")
                        NEXT = 1
                        break
                    elif ord(c) == 13:  # return
                        print()
                        break
                    else:
                        pass

                if NEXT or QUIT:
                    break

        # final grade
        if NEXT:
            continue
        elif not QUIT:
            beep(FreqATTN, DurATTN)
            while 1:
                print()
                print("Last chance! Enter p, f, or d [PASS, FAIL, DEFER]? ", end=" ")
                print()
                c = azcam.utils.check_keyboard(1).lower()
                if c == "p":
                    beep(FreqYES, DurYES)
                    open(passfile, "w")
                    break
                elif c == "f":
                    beep(FreqNO, DurNO)
                    open(failfile, "w")
                    break
                elif c == "d":
                    break
                else:
                    continue
        else:
            break

    # finished
    azcam.utils.curdir(top)

    return

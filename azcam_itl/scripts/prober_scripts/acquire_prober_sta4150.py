import os
import time

import azcam


def AcquireProberLsst(Name="", Root="/data/prober/STA4150"):
    """
    Acquire STA4150 characterization data on the ITL prober.
    """

    # parameters
    root = Root

    # *******************************************************
    # Define timing files for each configuration
    # *******************************************************
    timfiles = [
        os.path.join(
            azcam.db.systemfolder,
            "dspcode",
            "detectors",
            "sta4150",
            "dsptiming",
            "sta4150_config0.lod",
        )
    ]

    impars = {}
    azcam.utils.save_imagepars(impars)
    # *************************************************************************
    # Make data folder for hybrid
    # *************************************************************************
    if Name == "":
        name = azcam.utils.prompt("Enter device name", "snxxxxx")
    else:
        name = Name
    f = os.path.join(root, name)
    f = azcam.utils.fix_path(f)
    if not os.path.exists(f):
        os.mkdir(f)
        print("Created folder", f)
    azcam.utils.curdir(f)
    azcam.db.tools["parameters"].set_par("imagefolder", f)
    print("Moved to folder", f)

    # *************************************************************************
    # Create and move to a report folder
    # *************************************************************************
    orgfolder, reportfolder = azcam.utils.make_file_folder("report")
    azcam.utils.curdir(reportfolder)
    azcam.db.tools["parameters"].set_par("imagefolder", reportfolder)

    # *************************************************************************
    # Set image pars for testing
    # *************************************************************************
    azcam.db.tools["parameters"].set_par("imagetest", 0)
    azcam.db.tools["parameters"].set_par("imageroot", "itl.")
    azcam.db.tools["parameters"].set_par("imageautoname", 1)
    azcam.db.tools["parameters"].set_par("imageincludesequencenumber", 1)
    azcam.db.tools["parameters"].set_par("imageautoincrementsequencenumber", 1)

    # *************************************************************************
    # loop over configurations
    # *************************************************************************
    for cycle, tfile in enumerate(timfiles):

        print("Acquiring STA4150 data with %s" % os.path.basename(tfile))

        azcam.db.tools["parameters"].set_par(
            "imagesequencenumber", 1 + 100 * cycle
        )  # uniform image sequence numbers

        # set DSP code and reset camera
        azcam.db.tools["parameters"].set_par("TimingFile", tfile)
        azcam.db.tools["exposure"].reset()
        azcam.db.tools["exposure"].roi_reset()
        azcam.db.tools["exposure"].set_roi(-1, -1, -1, -1, 4, 4)
        azcam.db.tools["exposure"].flush(3)

        # clear device after reset
        time.sleep(5)
        azcam.db.tools["exposure"].test(0)

        # unbinned, full frame
        # **********************************
        azcam.db.tools["exposure"].set_roi(-1, -1, -1, -1, 1, 1)

        # Zero
        print("Acquiring bias image...")
        azcam.db.tools["exposure"].expose(0.0, "zero", "bias image")

        # Flat
        print("Acquiring grid image...")
        azcam.db.tools["exposure"].expose(5.0, "object", "grid image")

        # Dark
        print("Acquiring dark image...")
        azcam.db.tools["exposure"].expose(5.0, "dark", "dark image")

    imagenum = 1 * cycle + 1
    azcam.db.tools["parameters"].set_par("imagesequencenumber", imagenum)

    # make a dark subtracted flat
    azcam.db.tools["parameters"].set_par("imageautoname", 0)
    azcam.db.tools["exposure"].expose(1.0, "object", "grid flat")
    azcam.db.tools["exposure"].expose(1.0, "dark", "reference dark")
    flatname = "itl.%04d.fits" % imagenum
    darkname = "itl.%04d.fits" % (imagenum + 1)
    azcam.fits.sub(flatname, darkname, "grid.fits")
    azcam.db.tools["display"].display("grid.fits")

    # finish
    azcam.utils.restore_imagepars(impars, orgfolder)

    print("Script finished")

    return

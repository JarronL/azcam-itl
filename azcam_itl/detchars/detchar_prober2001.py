import datetime
import fnmatch
import os
import shutil

import azcam
from azcam_itl import itlutils
from azcam_testers.detchar import DetChar


class VirusDetChar(DetChar):
    def __init__(self):

        super().__init__()

        self.imsnap_scale = 1.0

        self.filename2 = ""
        self.itl_sn = -1
        self.itl_id = ""

        self.Project = ""
        self.customer = ""
        self.dewar = ""
        self.device_type = ""
        self.backside_bias = 0.0

        self.lot = "UNKNOWN"
        self.wafer = "UNKNOWN"
        self.die = "UNKNOWN"
        self.report_date = ""

        self.configuration = "CONFIG0"

        self.start_delay = 180  # aquisition starting delay in seconds

        # report parameters
        self.report_file = ""

        self.report_names = [
            "gain",
            "prnu",
            "ptc",
            "linearity",
            "qe",
            "dark",
            "defects",
            "fe55",
        ]
        self.report_files = {
            "dark": "dark/dark",
            "defects": "defects/darkdefects",
            "fe55": "fe55/fe55",
            "gain": "gain/gain",
            "linearity": "ptc/linearity",
            "ptc": "ptc/ptc",
            "prnu": "prnu/prnu",
            "qe": "qe/qe",
        }

    def acquire(self):
        """
        Acquire detector characterization data.
        """

        # self.root_folder = "/data/prober2001/VIRUS"  # 09Jul18 MPL
        self.root_folder = azcam.utils.curdir()

        print("Starting VIRUS acquisition sequence for EG prober 2001X")
        print("")

        self.setup()
        sn = "sn" + str(self.itl_sn)

        # *************************************************************************
        # set RootFolder (e.g. /data/VIRUS/sn9999
        # *************************************************************************
        s = os.path.join(self.root_folder, sn)
        self.root_folder = s.replace("\\", "/")
        if not os.path.exists(self.root_folder):
            os.makedirs(self.root_folder)
        print("RootFolder is %s" % self.root_folder)

        azcam.utils.curdir(self.root_folder)

        print("Testing device %s" % sn)

        # *************************************************************************
        # save current image parameters
        # *************************************************************************
        impars = {}
        azcam.utils.save_imagepars(impars)

        # *************************************************************************
        # Create and move to a dated folder
        # *************************************************************************
        today = datetime.datetime.strftime(datetime.datetime.now(), "%d%b%y").lower()
        currentfolder, reportfolder = azcam.utils.make_file_folder(today + "_", 1, 1)
        azcam.utils.curdir(reportfolder)
        azcam.db.tools["parameters"].set_par("imagefolder", reportfolder)

        # *************************************************************************
        # Acquire data
        # *************************************************************************
        azcam.db.tools["parameters"].set_par(
            "imagesequencenumber", 1
        )  # uniform image sequence numbers

        # reset camera
        print("Reset and Flush detector")
        azcam.db.tools["exposure"].reset()
        azcam.db.tools["exposure"].roi_reset()
        azcam.db.tools["exposure"].test(0)  # flush

        # dark signal
        azcam.db.tools["exposure"].test(0)
        azcam.db.tools["dark"].acquire()

        itlutils.imsnap(self.imsnap_scale, "last")

        azcam.utils.restore_imagepars(impars, currentfolder)

        # finish
        azcam.utils.restore_imagepars(impars, currentfolder)
        azcam.utils.curdir("..")

        print("detchar sequence finished")

        return

    def analyze(self):
        """
        Analyze data.
        """

        print("Begin analysis of STA3600 dataset")
        rootfolder = azcam.utils.curdir()

        if not self.is_setup:
            self.setup()

        # analyze bias
        azcam.utils.curdir("bias")
        azcam.db.tools["bias"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze superflats
        azcam.utils.curdir("superflat")
        azcam.db.tools["superflat"].analyze()
        azcam.utils.curdir(rootfolder)

        # analyze darks
        azcam.utils.curdir("dark")
        azcam.db.tools["dark"].analyze()
        azcam.utils.curdir(rootfolder)

        # make report
        self.report()

        return

    def cleanup(self):
        """
        Cleanup folders after data analysis.
        """

        self.remove_analysis_folders()
        self.remove_test_files()

        return

    def remove_test_files(self):
        """
        Remove (delete!) test.fits files from entire folder tree.
        """

        folder = azcam.utils.curdir()
        matches = []
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, "test.fits"):
                matches.append(os.path.join(root, filename))

        for t in matches:
            print("Deleting file", t)
            os.remove(t)

        print("Removed %d files" % len(matches))

        return

    def remove_analysis_folders(self):
        """
        Remove (delete!) analysis subfolders and all daa in them!
        """

        import fnmatch

        folder = azcam.utils.curdir()
        matches = []
        for root, dirnames, filenames in os.walk(folder):
            for dirname in fnmatch.filter(dirnames, "analysis*"):
                matches.append(os.path.join(root, dirname))

        for t in matches:
            print("Deleting folder", t)
            shutil.rmtree(t)

        print("Removed %d folders" % len(matches))
        return

    def setup(self):

        s = azcam.utils.curdir()
        try:
            x = s.index("/sn")
            if x > 0:
                sn = s[x + 3 : x + 8]
            else:
                sn = 0
        except ValueError:
            sn = 0
        itlsn = azcam.utils.prompt("Enter sensor serial number (integer)", sn)
        self.itl_sn = int(itlsn)

        return

        # ****************************************************************
        # Identification
        # ****************************************************************
        if self.itl_sn == 0 or self.itl_sn == -1:
            print("WARNING! Unspecified detector serial number")
            self.itl_sn = 0
            self.itl_id = "0"
        else:
            # get ID number in format NNN (package ID)
            dbinfo = itlutils.get_itldb_info(self.itl_sn)
            self.lot = dbinfo[1]
            self.device_type = dbinfo[2]
            self.wafer = dbinfo[3]
            self.die = dbinfo[4]
            self.itl_id = dbinfo[5]

        # device serial number
        self.itl_sn = int(itlsn)
        if self.itl_sn == 0 or self.itl_sn == -1:
            print("WARNING! Unspecified detector serial number")
            self.itl_sn = 0
            self.itl_id = "0"
        else:
            # get ID number in format NNN (package ID)
            dbinfo = itlutils.get_itldb_info(self.itl_sn)
            try:
                self.itl_id = "%s".strip() % dbinfo[5]
            except IndexError:
                self.itl_sn = 0
                self.itl_id = "000"

        # sponsor/report info
        self.customer = "Univ. Texas"
        self.Project = "VIRUS"
        azcam.db.tools["qe"].plot_title = "STA3600 Quantum Efficiency"

        self.is_setup = 1

        return


# create instance
detchar = VirusDetChar()

# ***********************************************************************************
# parameters
# ***********************************************************************************
azcam.utils.set_image_roi([[500, 1500, 200, 900], [2069, 2078, 100, 500]])

# bias
azcam.db.tools["bias"].number_images_acquire = 2
azcam.db.tools["bias"].number_flushes = 2

# dark
azcam.db.tools["dark"].number_images_acquire = 1
azcam.db.tools["dark"].exposure_time = 3.0
azcam.db.tools["dark"].overscan_correct = 1
azcam.db.tools["dark"].zero_correct = 1

# superflats
azcam.db.tools["superflat"].number_images_acquire = [1]
azcam.db.tools["superflat"].wavelength = -1
azcam.db.tools["superflat"].exposure_times = [1.0]

import datetime
import os
import subprocess
import time
import shutil

import azcam
from azcam_console.tools.testers.detchar import DetChar
from azcam_itl import itlutils


class DesiDetCharClass(DetChar):
    def __init__(self):
        super().__init__()

        self.is_retest = 0

        self.filename2 = ""
        self.itl_sn = -1
        self.itl_id = ""

        self.system = ""
        self.customer = ""
        self.dewar = ""
        self.device_type = ""
        self.backside_bias = 0.0

        self.lot = "UNKNOWN"
        self.wafer = "UNKNOWN"
        self.die = "UNKNOWN"
        self.report_date = ""
        self.report_comment = ""

        self.start_delay = 10  # acuisition starting delay in seconds

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
            "defects": "defects/defects",
            "fe55": "fe55/fe55",
            "gain": "gain/gain",
            "linearity": "ptc/linearity",
            "ptc": "ptc/ptc",
            "prnu": "prnu/prnu",
            "qe": "qe/qe",
        }

    def acquire(self, SN="prompt"):
        """
        Acquire detector characterization data.
        """

        if not self.is_setup:
            self.setup()
        sn = "sn" + str(self.itl_sn)

        print("Testing device %s" % sn)

        # *************************************************************************
        # save current image parameters
        # *************************************************************************
        impars = {}
        azcam.utils.save_imagepars(impars)

        # *************************************************************************
        # Create and move to a report folder
        # *************************************************************************
        currentfolder, reportfolder = azcam.utils.make_file_folder("report", 1, 1)
        azcam.utils.curdir(reportfolder)
        azcam.db.parameters.set_par("imagefolder", reportfolder)

        print("Flush detector")
        azcam.db.tools["exposure"].roi_reset()
        azcam.db.tools["exposure"].test(0)

        try:
            # *************************************************************************
            # gain images
            # *************************************************************************
            azcam.db.tools["gain"].find()

            # *************************************************************************
            # calibrate detcal
            # *************************************************************************
            azcam.db.tools["detcal"].read_datafile(azcam.db.tools["detcal"].data_file)
            # azcam.db.tools["detcal"].calibrate()

            # *************************************************************************
            # Acquire data
            # *************************************************************************
            azcam.db.parameters.set_par("imagesequencenumber", 1)  # uniform image sequence numbers

            # clear device after reset delay
            print("Delaying start for %.0f seconds (to settle)..." % self.start_delay)
            time.sleep(self.start_delay)
            azcam.db.tools["exposure"].test(0)  # flush

            # bias images
            azcam.db.tools["bias"].acquire()

            # superflat sequence
            azcam.db.tools["superflat"].acquire()

            # PTC and linearity
            azcam.db.tools["ptc"].acquire()

            # QE and Prnu
            azcam.db.tools["qe"].acquire()

            # Dark signal
            azcam.db.tools["exposure"].test(0)
            azcam.db.tools["dark"].acquire()

            # Fe55
            azcam.db.tools["fe55"].acquire()

        except Exception:
            azcam.utils.restore_imagepars(impars, currentfolder)
            return

        # finish
        azcam.utils.restore_imagepars(impars, currentfolder)

        # send email notice
        finishedtime = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
        message = "Script finished today at: %s" % (finishedtime)
        itlutils.mailto("mlesser@arizona.edu", "DESI acquire script finished", message)

        print("detchar sequence finished")

        return

    def analyze(self):
        """
        Analyze data.
        """

        print("Begin analysis of DESI dataset")
        rootfolder = azcam.utils.curdir()

        if not self.is_setup:
            self.setup()

        # analyze bias
        azcam.utils.curdir("bias")
        azcam.db.tools["bias"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze gain
        azcam.utils.curdir("gain")
        azcam.db.tools["gain"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze superflats
        azcam.utils.curdir("superflat1")
        azcam.db.tools["superflat"].analyze()
        azcam.utils.curdir(rootfolder)

        # analyze PTC
        azcam.utils.curdir("ptc")
        azcam.db.tools["ptc"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze linearity from PTC data
        azcam.utils.curdir("ptc")
        azcam.db.tools["linearity"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze Fe-55
        azcam.utils.curdir("fe55")
        azcam.db.tools["fe55"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze darks
        azcam.utils.curdir("dark")
        azcam.db.tools["dark"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze defects
        azcam.db.tools["defects"].dark_filename = azcam.db.tools["dark"].dark_filename
        azcam.utils.curdir("dark")
        azcam.db.tools["defects"].analyze_bright_defects()
        azcam.db.tools["defects"].copy_data_files()
        azcam.utils.curdir(rootfolder)

        azcam.db.tools["defects"].flat_filename = azcam.db.tools["superflat"].superflat_filename
        azcam.utils.curdir("superflat1")
        azcam.db.tools["defects"].analyze_dark_defects()
        azcam.db.tools["defects"].copy_data_files()
        azcam.utils.curdir(rootfolder)

        azcam.utils.curdir("defects")
        azcam.db.tools["defects"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze qe
        azcam.utils.curdir("qe")
        azcam.db.tools["qe"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze prnu
        azcam.utils.curdir("qe")
        azcam.db.tools["prnu"].analyze()
        azcam.db.tools["prnu"].copy_data_files()
        azcam.utils.curdir(rootfolder)
        print("")

        # make report
        try:
            self.report()
        except Exception:
            pass

        return

    def report(self):
        """
        Make detector characterization report.
        Run setup() first.
        """

        if not self.is_setup:
            self.setup()

        folder = azcam.utils.curdir()
        self.report_folder = folder
        report_name = f"DESI_report_SN{self.itl_sn}.pdf"

        print("")
        print("Generating SN%s Report" % self.itl_sn)
        print("")

        # *********************************************
        # Combine PDF report files for each tool
        # *********************************************
        rfiles = [self.summary_report_file + ".pdf"]
        for r in self.report_names:  # add pdf extension
            f1 = self.report_files[r] + ".pdf"
            f1 = os.path.abspath(f1)
            if os.path.exists(f1):
                rfiles.append(f1)
            else:
                print("Report file not found: %s" % f1)
        self.merge_pdf(rfiles, report_name)

        # open report
        with open(os.devnull, "w") as fnull:
            s = "%s" % self.report_file
            subprocess.Popen(s, shell=True, cwd=folder, stdout=fnull, stderr=fnull)
            fnull.close()

        return

    def report_summary(self):
        """
        Create a ID and summary report.
        """

        if len(self.report_comment) == 0:
            self.report_comment = azcam.utils.prompt("Enter report comment")

        # get current date
        self.report_date = datetime.datetime.now().strftime("%b-%d-%Y")

        lines = []

        lines.append("# DESI Blue Detector Characterization Report")
        lines.append("")
        lines.append("|    |    |")
        lines.append("|:---|:---|")
        lines.append(f"|Customer       |LBNL|")
        lines.append(f"|ITL System     |DESI|")
        lines.append(f"|ITL ID         |{self.itl_id}|")
        lines.append(f"|ITL SN         |{int(self.itl_sn)}|")
        lines.append(f"|Type           |STA4150|")
        lines.append(f"|Lot            |{self.lot}|")
        lines.append(f"|Wafer          |{int(self.wafer):02d}|")
        lines.append(f"|Die            |{int(self.die)}|")
        lines.append(f"|Report Date    |{self.report_date}|")
        lines.append(f"|Author         |M. Lesser|")
        lines.append(f"|System         |ITL6|")
        lines.append(f"|Comment        |{self.report_comment}|")
        lines.append("")

        # add superflat image
        f1 = os.path.abspath("./superflat1/superflatimage.png")
        s = f"<img src={f1} width=350>"
        lines.append(s)
        lines.append("")
        lines.append("*Superflat Image.*")
        # lines.append("")

        # Make report files
        self.write_report(self.summary_report_file, lines)

        return

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

        dewar = 6
        operator = "mpl"

        # ****************************************************************
        # Identification
        # ****************************************************************
        if self.itl_sn == 0 or self.itl_sn == -1:
            azcam.AzcamWarning("Unspecified detector serial number")
            self.itl_sn = 0
            self.itl_id = "0"
        else:
            # get ID number in format NNN (package ID)
            self.lot = azcam.utils.prompt("Enter lot")
            self.device_type = azcam.utils.prompt("Enter device type")
            self.wafer = azcam.utils.prompt("Enter wafer")
            self.die = azcam.utils.prompt("Enter die")
            self.itl_id = azcam.utils.prompt("Enter ITL ID")

        # sponsor/report info
        self.customer = "LBNL"
        self.system = "DESI"

        self.dewar = "ITL6"  # Kadel

        self.summary_report_file = f"SummaryReport_SN{self.itl_sn}"

        self.is_setup = 1

        return

    def upload_prep(self):
        """
        Prepare a dataset for upload by creating a compressed tar
        file and checksum.
        :param foldername: the folder name to prepare.
        :param idstring: the output ID of the dataset.
        """

        idstring = f"sn{self.itl_sn}"

        cd = azcam.utils.curdir()
        foldername = cd

        # cleanup folder
        azcam.log("cleaning dataset folder")
        itlutils.cleanup_files(foldername)

        # copy folder to new name
        azcam.log(f"copying dataset to {idstring}")
        # shutil.copytree(os.path.basename(foldername), idstring)
        shutil.copytree(foldername, idstring)

        # make tar file
        azcam.log("making tar file")
        tarfile = itlutils.archive(idstring, "tar.gz")

        azcam.utils.curdir(cd)

        return tarfile

    def make_upload(self):
        """
        Prepare a dataset for upload by creating a compressed tar file.
        Start in report folder.
        """

        s = azcam.utils.curdir()
        try:
            x = s.index("/sn")
            if x > 0:
                sn = s[x + 3 : x + 8]
            else:
                sn = 0
        except ValueError:
            sn = 0

        tarfile = itlutils.archive("upload", "zip")
        os.rename(tarfile, f"sn{sn}.zip")

        return


# create instance
detchar = DesiDetCharClass()

# ***********************************************************************************
# parameters
# ***********************************************************************************
azcam.utils.set_image_roi([[1950, 2000, 400, 450], [2051, 2055, 400, 450]])

# detcal
azcam.db.tools["detcal"].bias_goal = 1000
# azcam.db.tools["detcal"].wavelengths = [360, 400, 450, 500, 550, 600]
azcam.db.tools["detcal"].wavelengths = [330, 350, 370, 400, 500, 600, 700]
azcam.db.tools["detcal"].exposure_times = {
    330: 10,
    350: 1,
    370: 1,
    400: 0.3,
    500: 0.3,
    600: 0.15,
    700: 0.1,
}
azcam.db.tools["detcal"].data_file = f"{azcam.db.datafolder}/detcal_desi.txt"

# bias
azcam.db.tools["bias"].number_images_acquire = 3
azcam.db.tools["bias"].number_flushes = 2
azcam.db.tools["bias"].grade_sensor = 0

# gain
azcam.db.tools["gain"].number_pairs = 1  #
azcam.db.tools["gain"].exposure_time = 0.1
azcam.db.tools["gain"].wavelength = 600  #
azcam.db.tools["gain"].video_processor_gain = 4 * [
    7.19 * 0.9
]  # 19apr17 inc. preamp (6.5 usec, VG=1)
azcam.db.tools["gain"].wavelength = -1
azcam.db.tools["gain"].grade_sensor = 0

# dark
azcam.db.tools["dark"].number_images_acquire = 3
azcam.db.tools["dark"].exposure_time = 600.0
azcam.db.tools["dark"].dark_fraction = -1  # no spec on individual pixels
azcam.db.tools["dark"].mean_dark_spec = (
    10.0 / 3600
)  # specification for mean dark signal (electrons/pixel/sec)
azcam.db.tools["dark"].use_edge_mask = 1  #
azcam.db.tools["dark"].bright_pixel_reject = 5.0  # e/pix/sec clip
azcam.db.tools["dark"].overscan_correct = 1  # flag to overscan correct images
azcam.db.tools["dark"].zero_correct = 1  # flag to correct with bias residuals
azcam.db.tools["dark"].grade_sensor = 1
azcam.db.tools["dark"].report_plots = ["darkimage"]  # plots to include in report

# superflats
azcam.db.tools["superflat"].exposure_times = [5.0]  # xxx electrons
azcam.db.tools["superflat"].wavelength = 400  # used for dark defects
azcam.db.tools["superflat"].number_images_acquire = [3]  # number of images
azcam.db.tools["superflat"].grade_sensor = 0

# ptc
azcam.db.tools["ptc"].wavelength = 600
azcam.db.tools["ptc"].gain_range = [0.0, 2.0]
azcam.db.tools["ptc"].overscan_correct = 0
azcam.db.tools["ptc"].flush_before_exposure = 1
azcam.db.tools["ptc"].exposure_levels = [
    1000,
    2000,
    5000,
    10000,
    20000,
    30000,
    40000,
    50000,
    60000,
    70000,
]
# azcam.db.tools["ptc"].exposure_times=[0.2,0.5,1,2,4,8,12,14,15]  # not using levels [0.1,0.2,0.5,1,2,3,4,5,6,7,8]
azcam.db.tools["ptc"].grade_sensor = 0

# linearity
azcam.db.tools["linearity"].wavelength = 600
azcam.db.tools["linearity"].use_ptc_data = 1
azcam.db.tools["linearity"].linearity_fit_min = 1000.0  # 200?
azcam.db.tools["linearity"].linearity_fit_max = 55000.0
azcam.db.tools["linearity"].max_residual_linearity = 0.01  # max residual for linearity
azcam.db.tools["linearity"].plot_specifications = 1
azcam.db.tools["linearity"].plot_limits = [-3.0, +4.0]
azcam.db.tools["linearity"].overscan_correct = 1
azcam.db.tools["linearity"].zero_correct = 0
azcam.db.tools["linearity"].grade_sensor = 1

# QE
azcam.db.tools["qe"].cal_scale = 1.277  # 14jul21 DESI
azcam.db.tools["qe"].global_scale = 0.933  # correction
azcam.db.tools["qe"].flush_before_exposure = 1
azcam.db.tools["qe"].use_edge_mask = 1
azcam.db.tools["qe"].pixel_area = 0.015 * 0.015
azcam.db.tools["qe"].flux_cal_folder = "/data/DESI"
azcam.db.tools["qe"].plot_title = "DESI Blue Quantum Efficiency"
azcam.db.tools["qe"].plot_limits = [[290.0, 700.0], [0.0, 100.0]]
azcam.db.tools["qe"].grade_sensor = 1
azcam.db.tools["qe"].qeroi = []

azcam.db.tools["qe"].wavelengths = [330, 350, 370, 400, 500, 600, 700]
azcam.db.tools["qe"].qe_specs = {
    330: 0,
    350: 0,
    370: 0.75,
    400: 0.75,
    500: 0.85,
    600: 0.85,
    700: 0,
}

azcam.db.tools["qe"].exposure_levels = {
    330: 10000,
    350: 10000,
    370: 10000,
    400: 10000,
    500: 10000,
    600: 10000,
    700: 10000,
}
azcam.db.tools["qe"].exposure_times = {}
azcam.db.tools["qe"].window_trans = {
    330: 0.92,
    350: 0.92,
    370: 0.92,
    400: 0.92,
    500: 0.92,
    600: 0.92,
    700: 0.92,
}

# prnu
azcam.db.tools["prnu"].allowable_deviation_from_mean = 0.1
azcam.db.tools["prnu"].root_name = "qe."
azcam.db.tools["prnu"].use_edge_mask = 1
azcam.db.tools["prnu"].overscan_correct = 1
azcam.db.tools["prnu"].wavelengths = [330, 350, 370, 400, 500, 600, 700]
azcam.db.tools["prnu"].grade_sensor = 0

# fe55
azcam.db.tools[
    "fe55"
].number_images_acquire = 1  # goal is 10,000 events per section in summed image
azcam.db.tools["fe55"].exposure_time = 120.0
azcam.db.tools["fe55"].neighborhood_size = 5  # odd value
azcam.db.tools["fe55"].fit_psf = 0
azcam.db.tools["fe55"].threshold = 300
azcam.db.tools["fe55"].spec_sigma = -1  # charge diffusion spec in microns
azcam.db.tools["fe55"].hcte_limit = 0.999_990
azcam.db.tools["fe55"].vcte_limit = 0.999_990
azcam.db.tools["fe55"].spec_by_cte = 1
azcam.db.tools["fe55"].overscan_correct = 1
azcam.db.tools["fe55"].zero_correct = 1
azcam.db.tools["fe55"].pause_each_channel = 0
azcam.db.tools["fe55"].report_include_plots = 1
azcam.db.tools["fe55"].gain_estimate = 4 * [1.1]
azcam.db.tools["fe55"].make_plots = ["histogram", "cte"]
azcam.db.tools["fe55"].dark_correct = 0
azcam.db.tools["fe55"].system_noise_correction = [
    0.94,
    0.93,
    1.01,
    1.16,
]  # im1-im4
azcam.db.tools["fe55"].plot_files = {
    "hcte": "hcte.png",
    "vcte": "vcte.png",
    "histogram": "histogram.png",
}
azcam.db.tools["fe55"].plot_titles = {
    "hcte": "HCTE Plot.",
    "vcte": "VCTE Plot.",
    "histogram": "X-Ray Histogram Plot.",
}
azcam.db.tools["fe55"].grade_sensor = 1

# defects
azcam.db.tools["defects"].use_edge_mask = 1
azcam.db.tools["defects"].edge_size = 13  # from Pat
azcam.db.tools["defects"].allowable_bad_fraction = 0.0001  # % allowed bad pixels
azcam.db.tools["defects"].bright_pixel_reject = 5.0  # e/pix/sec
azcam.db.tools["defects"].dark_pixel_reject = 0.50  # reject pixels below this value from mean
azcam.db.tools["defects"].grade_sensor = 1

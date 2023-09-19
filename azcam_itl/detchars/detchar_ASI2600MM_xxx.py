import datetime
import fnmatch
import ftplib
import glob
import os
import re
import shutil
import subprocess
import time

import keyring

import azcam
import azcam_console
from azcam_console.tools.testers.detchar import DetChar
from azcam_itl import itlutils


class ASI2600MMDetChar(DetChar):
    def __init__(self):
        super().__init__()

        self.imsnap_scale = 1.0

        self.filename2 = ""
        self.itl_id = ""

        self.system = ""
        self.customer = ""
        self.dewar = ""
        self.device_type = ""
        self.backside_bias = 0.0

        self.lot = "UNKNOWN"
        self.wafer = 0
        self.die = 0
        self.report_date = ""

        self.report_comment = ""

        self.start_delay = 10  # acquisition starting delay in seconds

        # report parameters
        self.report_file = ""
        self.summary_report_file = ""
        self.report_names = [
            "gain",
            "prnu",
            "ptc",
            "linearity",
            "qe",
            "dark",
        ]
        self.report_files = {
            "gain": "gain/gain",
            "prnu": "prnu/prnu",
            "dark": "dark/dark",
            "linearity": "ptc/linearity",
            "ptc": "ptc/ptc",
            "qe": "qe/qe",
        }

        self.start_temperature = -20.0

        self.timingfiles = []

    def acquire(self):
        """
        Acquire detector characterization data.
        """

        print("Starting acquisition sequence")
        print("")

        if not self.is_setup:
            self.setup()

        (
            gain,
            bias,
            detcal,
            superflat,
            ptc,
            qe,
            dark,
            defects,
            dark,
        ) = azcam_console.utils.get_tools(
            [
                "gain",
                "bias",
                "detcal",
                "superflat",
                "ptc",
                "qe",
                "dark",
                "dark",
            ]
        )
        exposure, tempcon = azcam_console.utils.get_tools(
            [
                "exposure",
                "tempcon",
            ]
        )

        # *************************************************************************
        # wait for temperature
        # *************************************************************************
        if self.start_temperature != -1000:
            while True:
                t = tempcon.get_temperatures()[0]
                print("Current temperature: %.1f" % t)
                if t <= self.start_temperature + 0.5:
                    break
                else:
                    time.sleep(10)

        print("Testing...")

        # *************************************************************************
        # save current image parameters
        # *************************************************************************
        impars = {}
        azcam.db.parameters.save_imagepars(impars)

        # *************************************************************************
        # read most recent detcal info
        # *************************************************************************
        if 0:
            detcal.read_datafile(detcal.data_file)
            detcal.mean_electrons = {int(k): v for k, v in detcal.mean_electrons.items()}
            detcal.mean_counts = {int(k): v for k, v in detcal.mean_counts.items()}

        # *************************************************************************
        # Create and move to a report folder
        # *************************************************************************
        currentfolder, reportfolder = azcam_console.utils.make_file_folder(
            "report", 1, 1
        )  # start with report1
        azcam.utils.curdir(reportfolder)

        # *************************************************************************
        # Acquire data
        # *************************************************************************
        azcam.db.parameters.set_par("imagesequencenumber", 1)  # uniform image sequence numbers

        # reset camera
        print("Reset and Flush detector")
        exposure.reset()
        exposure.roi_reset()
        exposure.test(0)  # flush

        # clear device after reset delay
        print("Delaying start for %.0f seconds (to settle)..." % self.start_delay)
        time.sleep(self.start_delay)
        exposure.test(0)  # flush

        # bias images
        bias.acquire()
        itlutils.imsnap(self.imsnap_scale, "last")

        # gain images
        # gain.find()
        gain.acquire()

        # PRNU images
        azcam.db.tools["prnu"].acquire()

        # superflat sequence
        superflat.acquire()

        # PTC and linearity
        ptc.acquire()

        # QE
        qe.acquire()

        # Dark signal
        exposure.test(0)
        dark.acquire()

        azcam.db.parameters.restore_imagepars(impars)
        azcam.utils.curdir(currentfolder)

        print("acquire sequence finished")

        return

    def analyze(self):
        """
        Analyze data.
        """

        print("Begin analysis of dataset")
        rootfolder = azcam.utils.curdir()

        (
            gain,
            bias,
            superflat,
            ptc,
            qe,
            dark,
            defects,
        ) = azcam_console.utils.get_tools(
            [
                "gain",
                "bias",
                "superflat",
                "ptc",
                "qe",
                "dark",
                "defects",
            ]
        )

        if not self.is_setup:
            self.setup()

        # analyze bias
        azcam.utils.curdir("bias")
        bias.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze gain
        azcam.utils.curdir("gain")
        gain.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze superflats
        azcam.utils.curdir("superflat1")
        try:
            superflat.analyze()
        except Exception:
            azcam.utils.curdir(rootfolder)
            azcam.utils.curdir("superflat1")
            superflat.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze PTC
        azcam.utils.curdir("ptc")
        ptc.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze linearity from PTC data
        azcam.utils.curdir("ptc")
        try:
            azcam.db.tools["linearity"].analyze()
        except Exception:
            azcam.utils.curdir(rootfolder)
            azcam.utils.curdir("ptc")
            azcam.db.tools["linearity"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze darks
        azcam.utils.curdir("dark")
        dark.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze defects
        azcam.db.tools["defects"].dark_filename = dark.dark_filename
        azcam.utils.curdir("dark")
        azcam.db.tools["defects"].analyze_bright_defects()
        azcam.db.tools["defects"].copy_data_files()
        azcam.utils.curdir(rootfolder)

        azcam.db.tools["defects"].flat_filename = superflat.superflat_filename
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
        try:
            qe.analyze()
        except Exception:
            azcam.utils.curdir(rootfolder)
            azcam.utils.curdir("qe")
            qe.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze prnu
        azcam.utils.curdir("qe")
        try:
            azcam.db.tools["prnu"].analyze()
        except Exception:
            azcam.utils.curdir(rootfolder)
            azcam.utils.curdir("qe")
            azcam.db.tools["prnu"].analyze()
        azcam.db.tools["prnu"].copy_data_files()
        azcam.utils.curdir(rootfolder)
        print("")

        # make report
        self.report_summary()
        self.report()

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
        report_name = f"ZWO_ASI2600MM_report_{self.itl_id}.pdf"

        print("")
        print("Generating %s Report" % self.itl_id)
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

        lines.append("# ITL Detector Characterization Report")
        lines.append("")
        lines.append("|    |    |")
        lines.append("|:---|:---|")
        lines.append("|**Identification**||")
        lines.append(f"|Customer       |UArizona|")
        lines.append(f"|ITL System     |ZWO ASI2600MM|")
        lines.append(f"|ITL ID         |{self.itl_id}|")
        lines.append(f"|Type           |ASI2600MM-Pro|")
        lines.append(f"|Report Date    |{self.report_date}|")
        lines.append(f"|Author         |{self.filename2}|")
        lines.append(f"|System         |ZWO ASI2600MM|")
        lines.append(f"|Comment        |{self.report_comment}|")
        lines.append("")

        # add superflat image
        f1 = os.path.abspath("./superflat1/superflatimage.png")
        s = f"<img src={f1} width=350>"
        lines.append(s)
        # lines.append(f"![Superflat Image]({os.path.abspath('./superflat1/superflatimage.png')})  ")
        lines.append("")
        lines.append("*Superflat Image.*")
        # lines.append("")

        # Make report files
        self.write_report(self.summary_report_file, lines)

        return

    def copy_files(self):
        """
        Copy both report and flats
        """

        # azcam.utils.curdir("..")
        itlutils.cleanup_files()
        self.copy_reports()
        self.copy_flats()

        return

    def copy_flats(self):
        """
        Find all qe.0004 flat field files from current folder tree and copy them to
        the folder two levels up (run from report) with new name.
        """

        folder = azcam.utils.curdir()
        dest_folder = azcam.utils.curdir()
        azcam.utils.curdir(folder)
        matches = []
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, "qe.0004.fits"):
                matches.append(os.path.join(root, filename))

        for t in matches:
            match = re.search("sn", t)
            if match is not None:
                start = match.start()
                sn = t[start : start + 7]
                print("Found: ", t)
                print("Press y or enter to copy this file...")
                key = azcam.utils.check_keyboard(1)
                if key == "y" or key == "\r":
                    print()
                    shutil.copy(t, os.path.join(dest_folder, "%s_flat.fits" % (sn)))
                else:
                    print("File not copied")

        return

    def copy_reports(self):
        """
        Find all qe.0004 flat field files from current folder tree and copy them to
        the folder two levels up (run from report) with new name.
        """

        folder = azcam.utils.curdir()
        dest_folder = azcam.utils.curdir()
        azcam.utils.curdir(folder)
        matches = []
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, "ZWO_Report_*.pdf"):
                matches.append(os.path.join(root, filename))

        for t in matches:
            print("Found: ", t)
            print("Press y or enter to copy this file...")
            key = azcam.utils.check_keyboard(1)
            if key == "y" or key == "\r":
                shutil.copy(t, dest_folder)
            else:
                print("File not copied")

        return

    def setup(self):
        s = azcam.utils.curdir()
        itlid = azcam.utils.prompt("Enter sensor ID")
        self.itl_id = itlid

        operator = azcam.utils.prompt("Enter you initals", "mpl")

        # ****************************************************************
        # Identification
        # ****************************************************************

        # sponsor/report info
        self.customer = "UArizona"
        self.system = "ZWO"
        qe.plot_title = "ASI2600MM Quantum Efficiency"
        self.summary_report_file = f"SummaryReport_{self.itl_id}"
        self.report_file = f"ZWO_Report_{self.itl_id}.pdf"

        # dewar info
        self.dewar = "ZWO"

        if operator.lower() == "mpl":
            self.filename2 = "Michael Lesser"
        else:
            print("")
            print("Intruder!  Unknown user.")
            self.filename2 = "UNKNOWN"
        print("")

        self.device_type = "ASI2600MM"

        self.is_setup = 1

        return


# create instance
detchar = ASI2600MMDetChar()

(
    exposure,
    gain,
    bias,
    detcal,
    superflat,
    ptc,
    qe,
    dark,
    defects,
    linearity,
    prnu,
) = azcam_console.utils.get_tools(
    [
        "exposure",
        "gain",
        "bias",
        "detcal",
        "superflat",
        "ptc",
        "qe",
        "dark",
        "defects",
        "linearity",
        "prnu",
    ]
)

# ***********************************************************************************
# parameters
# ***********************************************************************************
azcam_console.utils.set_image_roi([[500, 600, 500, 600]])

et = {
    350: 25.0,
    400: 5.0,
    450: 5.0,
    500: 5.0,
    550: 5.0,
    600: 5.0,
    650: 5.0,
    700: 5.0,
    750: 5.0,
    800: 5.0,
}


# detcal
detcal.wavelengths = [
    350,
    400,
    450,
    500,
    550,
    600,
    650,
    700,
    750,
    800,
]
detcal.exposure_times = {}
detcal.data_file = os.path.join(azcam.db.datafolder, "detcal_ASI2600MM.txt")
detcal.mean_count_goal = 35000
detcal.range_factor = 1.2

# bias
bias.number_images_acquire = 3
bias.number_flushes = 2

# gain
gain.number_pairs = 1
gain.exposure_time = 3.0
gain.wavelength = 600

# dark
dark.number_images_acquire = 5
dark.exposure_time = 60.0
dark.dark_fraction = -1  # no spec on individual pixels
dark.overscan_correct = 0  # flag to overscan correct images
dark.zero_correct = 1  # flag to correct with bias residuals
dark.fit_order = 0
dark.report_dark_per_hour = 0

# superflats
superflat.exposure_times = [10]
superflat.wavelength = 600
superflat.number_images_acquire = [10]
superflat.overscan_correct = 0
superflat.zero_correct = 1

# ptc
ptc.wavelength = 600
# ptc.gain_range = [0.75, 1.5]
ptc.overscan_correct = 0
ptc.fit_line = True
ptc.fit_min = 1000
ptc.fit_max = 60000
ptc.exposure_levels = []
ptc.exposure_times = []
ptc.max_exposures = 75
ptc.number_images_acquire = 75

# linearity
linearity.wavelength = 600
linearity.use_ptc_data = 1
linearity.linearity_fit_min = 1000.0
linearity.linearity_fit_max = 63000.0
linearity.max_residual_linearity = 0.01
linearity.plot_specifications = 1
linearity.plot_limits = [-4.0, +4.0]
linearity.overscan_correct = 0
linearity.zero_correct = 1
linearity.number_images_acquire = 5
linearity.max_exposure = 5
linearity.use_weights = 0

# QE
qe.cal_scale = 1.107
qe.global_scale = 1.0
qe.pixel_area = 0.00376**2
qe.flux_cal_folder = "/data/ASI2600MM"
qe.plot_limits = [[300.0, 800.0], [0.0, 100.0]]
qe.plot_title = "ZWO ASI2600MM Quantum Efficiency"
qe.qeroi = []
qe.overscan_correct = 0
qe.zero_correct = 1
qe.flush_before_exposure = 0
qe.grade_sensor = 0
qe.create_reports = 1
qe.use_exposure_levels = 1
el = 5000.0
qe.exposure_levels = {
    350: el,
    400: el,
    450: el,
    500: el,
    550: el,
    600: el,
    650: el,
    700: el,
    750: el,
    800: el,
}
qe.window_trans = {
    300: 1.0,
    1000: 1.0,
}
# from online plot
"""
qe.window_trans = {
    400: 0.95,
    450: 0.99,
    650: 0.99,
    700: 0.95,
    750: 0.93,
    850: 0.85,
    950: 0.78,
    1050: 0.75,
}
"""

# prnu
prnu.allowable_deviation_from_mean = 0.1
prnu.root_name = "qe."
prnu.use_edge_mask = 0
prnu.overscan_correct = 0
prnu.wavelengths = [
    350,
    400,
    450,
    500,
    550,
    600,
    650,
    700,
    750,
    800,
]
prnu.exposures = {
    350: qeet * 5,
    400: qeet,
    450: qeet,
    500: qeet,
    550: qeet,
    600: qeet * 2,
    650: qeet * 2,
    700: qeet * 5,
    750: qeet * 10,
    800: qeet * 10,
}

# defects
defects.use_edge_mask = 1
defects.edge_size = 0
defects.bright_pixel_reject = 0.5  # e/pix/sec
defects.dark_pixel_reject = 0.80  # below mean

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
from azcam.tools.testers.detchar import DetChar
from azcam_itl import itlutils


class QHY174DetChar(DetChar):
    def __init__(self):

        super().__init__()

        self.imsnap_scale = 1.0

        self.filename2 = ""
        self.itl_sn = -1
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

        self.start_temperature = -110.0

        self.timingfiles = []

    def acquire(self, SN="prompt"):
        """
        Acquire detector characterization data.
        """

        print("Starting ITL acquisition sequence")
        print("")

        if not self.is_setup:
            self.setup()
        sn = "sn" + str(self.itl_sn)

        (
            gain,
            bias,
            detcal,
            superflat,
            ptc,
            qe,
            dark,
            fe55,
            defects,
            dark,
        ) = azcam.utils.get_tools(
            [
                "gain",
                "bias",
                "detcal",
                "superflat",
                "ptc",
                "qe",
                "dark",
                "fe55",
                "defects",
                "dark",
            ]
        )
        exposure, tempcon = azcam.utils.get_tools(
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

        print("Testing device %s" % sn)

        # *************************************************************************
        # save current image parameters
        # *************************************************************************
        impars = {}
        azcam.utils.save_imagepars(impars)

        # *************************************************************************
        # read most recent detcal info
        # *************************************************************************
        detcal.read_datafile(detcal.data_file)
        detcal.mean_electrons = {int(k): v for k, v in detcal.mean_electrons.items()}
        detcal.mean_counts = {int(k): v for k, v in detcal.mean_counts.items()}

        for timefile in self.timingfiles:

            azcam.db.tools["parameters"].set_par("timingfile", timefile)

            # *************************************************************************
            # Create and move to a report folder
            # *************************************************************************
            currentfolder, reportfolder = azcam.utils.make_file_folder(
                "report", 1, 1
            )  # start with report1
            azcam.utils.curdir(reportfolder)

            # *************************************************************************
            # Acquire data
            # *************************************************************************
            azcam.db.tools["parameters"].set_par(
                "imagesequencenumber", 1
            )  # uniform image sequence numbers

            try:

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

                # Prnu images
                azcam.db.tools["prnu"].acquire()

                # superflat sequence
                superflat.acquire()

                # PTC and linearity
                ptc.acquire()

                # QE
                qe.acquire()

                # Fe55
                fe55.acquire()

                # Dark signal
                exposure.test(0)
                dark.acquire()

            finally:
                azcam.utils.restore_imagepars(impars, currentfolder)

        print("acquire sequence finished")

        return

    def analyze(self):
        """
        Analyze data.
        """

        print("Begin analysis of STA3600 dataset")
        rootfolder = azcam.utils.curdir()

        (
            exposure,
            gain,
            bias,
            detcal,
            superflat,
            ptc,
            qe,
            dark,
            fe55,
            defects,
        ) = azcam.utils.get_tools(
            [
                "exposure",
                "gain",
                "bias",
                "detcal",
                "superflat",
                "ptc",
                "qe",
                "dark",
                "fe55",
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

        # analyze Fe-55
        azcam.utils.curdir("fe55")
        fe55.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # use fe55 gain from now on
        gain.fe55_gain()

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
        report_name = f"QHY174_report_SN{self.itl_sn}.pdf"

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

        lines = []

        lines.append("# ITL Detector Characterization Report")
        lines.append("")
        lines.append("|    |    |")
        lines.append("|:---|:---|")
        lines.append("|**Identification**||")
        lines.append(f"|Customer       |UArizona|")
        lines.append(f"|ITL System     |QHY174|")
        lines.append(f"|ITL ID         |{self.itl_id}|")
        lines.append(f"|ITL SN         |{int(self.itl_sn)}|")
        lines.append(f"|Type           |QHY174|")
        lines.append(f"|Report Date    |{self.report_date}|")
        lines.append(f"|Author         |{self.filename2}|")
        lines.append(f"|**Operating Conditions**||")
        lines.append(f"|System         |QHY174|")
        lines.append(f"|**Results**||")
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
        self.copy_metrology()

        return

    def copy_flats(self):
        """
        Find all qe.0004 flat field files from current folder tree and copy them to
        the folder two levels up (run from report) with new name.
        Rather dumb, needs 5 digit SN for now...
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
        Rather dumb, needs 5 digit SN for now...
        """

        folder = azcam.utils.curdir()
        dest_folder = azcam.utils.curdir()
        azcam.utils.curdir(folder)
        matches = []
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, "QHY1`74_Report_*.pdf"):
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

    def copy_metrology(self):
        """
        Find all metrology files from current folder tree and copy them to
        the folder two levels up (run from report) with new name.
        """

        folder = azcam.utils.curdir()
        dest_folder = azcam.utils.curdir()
        azcam.utils.curdir(folder)
        matches = []
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, "metrology_*.pdf"):
                matches.append(os.path.join(root, filename))
            for filename in fnmatch.filter(filenames, "*_out.csv"):
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

        operator = azcam.utils.prompt("Enter you initals", "mpl")

        # ****************************************************************
        # Identification
        # ****************************************************************
        if self.itl_sn == 0 or self.itl_sn == -1:
            print("WARNING! Unspecified detector serial number")
            self.itl_sn = 0
            self.itl_id = "0"
        else:
            self.lot = azcam.utils.prompt("Enter lot")
            self.device_type = azcam.utils.prompt("Enter device type")
            self.wafer = azcam.utils.prompt("Enter wafer")
            self.die = azcam.utils.prompt("Enter die")
            self.itl_id = azcam.utils.prompt("Enter ITL ID")

        # device serial number
        self.itl_sn = int(itlsn)
        if self.itl_sn == 0 or self.itl_sn == -1:
            print("WARNING! Unspecified detector serial number")
            self.itl_sn = 0
            self.itl_id = "0"
        else:
            self.lot = azcam.utils.prompt("Enter lot")
            self.device_type = azcam.utils.prompt("Enter device type")
            self.wafer = azcam.utils.prompt("Enter wafer")
            self.die = azcam.utils.prompt("Enter die")
            self.itl_id = azcam.utils.prompt("Enter ITL ID")

        # sponsor/report info
        self.customer = "UArizona"
        self.system = "QHY174"
        qe.plot_title = "QHY174 Quantum Efficiency"
        self.summary_report_file = f"SummaryReport_SN{self.itl_sn}"
        self.report_file = f"QHY174_Report_{self.itl_sn}.pdf"

        # dewar info
        self.dewar = "QHY174"

        if operator.lower() == "mpl":
            self.filename2 = "Michael Lesser"
        else:
            print("")
            print("Intruder!  Unknown user.")
            self.filename2 = "UNKNOWN"
        print("")

        self.device_type = "QHY174"

        self.is_setup = 1

        return

    def upload_prep(self, shipdate: str):
        """
        Prepare a dataset for upload by creating an archive file.
        file.  Start in the _shipment folder.
        """

        startdir = azcam.utils.curdir()
        shipdate = os.path.basename(startdir)
        idstring = f"{shipdate}"

        # cleanup folder
        azcam.log("cleaning dataset folder")
        itlutils.cleanup_files()

        # move one folder above report folder
        # azcam.utils.curdir(reportfolder)
        # azcam.utils.curdir("..")

        self.copy_files()

        # copy files to new folder and archive
        azcam.log(f"copying dataset to {idstring}")
        currentfolder, newfolder = azcam.utils.make_file_folder(idstring)

        copy_files = glob.glob("*.pdf")
        for f in copy_files:
            shutil.move(f, newfolder)
        copy_files = glob.glob("*.fits")
        for f in copy_files:
            shutil.move(f, newfolder)
        copy_files = glob.glob("*.csv")
        for f in copy_files:
            shutil.move(f, newfolder)

        azcam.utils.curdir(newfolder)

        # make archive file
        azcam.utils.curdir(currentfolder)
        azcam.log("making archive file")
        archivefile = itlutils.archive(idstring, "zip")
        shutil.move(archivefile, newfolder)

        # delete data files from new folder
        azcam.utils.curdir(newfolder)
        [os.remove(x) for x in glob.glob("*.pdf")]
        [os.remove(x) for x in glob.glob("*.fits")]
        [os.remove(x) for x in glob.glob("*.csv")]

        azcam.utils.curdir(startdir)

        self.remote_upload_folder = idstring

        return archivefile


# create instance
detchar = QHY174DetChar()

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
) = azcam.utils.get_tools(
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
azcam.utils.set_image_roi([[500, 600, 500, 600]])

et = {
    300: 10.0,
    350: 5.0,
    400: 1.0,
    450: 1.0,
    500: 1.0,
    550: 5.0,
    600: 20.0,
    650: 20.0,
    700: 20.0,
    750: 20.0,
    800: 30.0,
    850: 30.0,
    900: 40.0,
    950: 100.0,
    1000: 200.0,
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
detcal.data_file = os.path.join(azcam.db.datafolder, "detcal_qhy174.txt")
detcal.mean_count_goal = 35000
detcal.range_factor = 1.2

# bias
bias.number_images_acquire = 3
bias.number_flushes = 2

# gain
gain.number_pairs = 1
gain.exposure_time = 3.0
gain.wavelength = 450
gain.video_processor_gain = []

# dark
dark.number_images_acquire = 10
dark.exposure_time = 60.0
dark.dark_fraction = -1  # no spec on individual pixels
# dark.mean_dark_spec = 3.0 / 600.0  # blue e/pixel/sec
# dark.mean_dark_spec = 6.0 / 600.0  # red
# dark.use_edge_mask = 1
# dark.bright_pixel_reject = 0.05  # e/pix/sec clip
dark.overscan_correct = 0  # flag to overscan correct images
dark.zero_correct = 1  # flag to correct with bias residuals
dark.fit_order = 0

# superflats
superflat.exposure_levels = [30000]  # electrons
superflat.wavelength = 450
superflat.number_images_acquire = [3]

# ptc
ptc.wavelength = 450
# ptc.gain_range = [0.75, 1.5]
ptc.overscan_correct = 0
ptc.fit_line = True
ptc.fit_min = 1000
ptc.fit_max = 60000
# ptc.exposure_levels = []
ptc.exposure_times = []
# ptc.max_exposures = 40
# ptc.number_images_acquire = 40
ptc.exposure_levels = [
    500,
    1000,
    1500,
    2000,
    2500,
    3000,
    3500,
    4000,
    4500,
    5000,
    5500,
    6000,
    6500,
    7000,
    8000,
    9000,
    10000,
    15000,
    20000,
    25000,
    30000,
    35000,
    40000,
    45000,
    50000,
    55000,
    60000,
    65000,
]

# linearity
linearity.wavelength = 450
linearity.use_ptc_data = 1
linearity.linearity_fit_min = 500.0
linearity.linearity_fit_max = 10000.0
linearity.max_residual_linearity = 0.01
linearity.plot_specifications = 1
linearity.plot_limits = [-4.0, +4.0]
linearity.overscan_correct = 0
linearity.zero_correct = 1
linearity.number_images_acquire = 5
linearity.max_exposure = 5
linearity.use_weights = 0

# QE
qe.cal_scale = 1.0
qe.global_scale = 1.0
qe.pixel_area = 0.00586 ** 2
qe.diode_cal_folder = "/data/QHY/QHY174"
qe.flux_cal_folder = "/data/QHY/QHY174"
qe.plot_limits = [[300.0, 1000.0], [0.0, 100.0]]
qe.plot_title = "QHY QHY174 Quantum Efficiency"
qe.qeroi = []
qe.overscan_correct = 0
qe.zero_correct = 1
qe.flush_before_exposure = 0
qe.grade_sensor = 0

qe.create_reports = 0
qe.plot_limits = []
qe.wavelengths = [450]
qe.exptime_offset = -0.03
""" qe.wavelengths = [
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
 """
# qe.exposure_times = et
""" qe.exposure_levels ={
    350: 5000,
    400: 5000,
    450: 5000,
    500: 5000,
    550: 5000,
    600: 5000,
    650: 5000,
    700: 5000,
    750: 5000,
    800: 5000,
}
 """
""" qeet = 20.0
qe.exposure_times = {
    350: qeet,
    360: qeet,
    370: qeet,
    380: qeet,
    390: qeet,
    400: qeet,
    420: qeet,
    450: qeet,
    470: qeet,
    500: qeet,
    520: qeet,
    550: qeet,
    570: qeet,
    600: qeet,
    620: qeet,
    650: qeet,
    700: qeet,
    750: qeet,
    800: qeet,
    850: qeet,
}
 """
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
prnu.root_name = "prnu."
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
]
prnu.exposures = et

# defects
defects.use_edge_mask = 0
defects.bright_pixel_reject = 0.5  # e/pix/sec
defects.dark_pixel_reject = 0.80  # below mean

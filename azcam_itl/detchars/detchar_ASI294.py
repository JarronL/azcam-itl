import datetime
import fnmatch
import ftplib
import glob
import os
import re
import shutil
import subprocess
import time

import azcam
import azcam_console.console
import azcam.utils
from azcam_console.testers.detchar import DetChar
from azcam_itl import itlutils


class ASI294DetChar(DetChar):
    def __init__(self):
        super().__init__()

        self.imsnap_scale = 1.0
        self.start_temperature = 10.0

        self.start_delay = 5

        # report parameters
        self.create_html = 1
        self.report_names = [
            "gain",
            "gainmap",
            "prnu",
            "ptc",
            "linearity",
            "qe",
            "dark",
            "bias",
            "defects",
        ]
        self.report_files = {
            "gain": "gain/gain",
            "gainmap": "gainmap/gainmap",
            "prnu": "prnu/prnu",
            "ptc": "ptc/ptc",
            "linearity": "ptc/linearity",
            "qe": "qe/qe",
            "dark": "dark/dark",
            "bias": "bias/bias",
            "defects": "defects/defects",
        }

    def setup(self, itl_id="1812911309020900"):
        """
        Setup
        """

        self.itl_id = azcam.utils.prompt("Enter camera ID", itl_id)

        # sponsor/report info
        self.customer = "UASAL"
        self.system = "ASI294MM-P"
        self.summary_report_name = f"SummaryReport_{self.itl_id}"
        self.report_name = f"CharacterizationReport__ASI292_{self.itl_id}.pdf"
        self.operator = "Michael Lesser"

        self.summary_lines = []
        self.summary_lines.append("# ITL Camera Characterization Report")

        self.summary_lines.append("|||")
        self.summary_lines.append("|:---|:---|")
        self.summary_lines.append(f"|Customer       |UASAL|")
        self.summary_lines.append(f"|System         |ZWO ASI294MM-P|")
        self.summary_lines.append(f"|ID             |{self.itl_id}|")
        self.summary_lines.append(f"|Operator       |{self.operator}|")

        self.is_setup = 1

        return

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
            gainmap,
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
                "gainmap",
                "bias",
                "detcal",
                "superflat",
                "ptc",
                "qe",
                "dark",
                "defects",
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

        print(f"Testing device {self.itl_id}")

        # *************************************************************************
        # save current image parameters
        # *************************************************************************
        impars = {}
        azcam.db.parameters.save_imagepars(impars)

        # *************************************************************************
        # read most recent detcal info
        # *************************************************************************
        detcal.read_datafile(detcal.data_file)

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
        azcam.db.parameters.set_par(
            "imagesequencenumber", 1
        )  # uniform image sequence numbers

        try:
            # reset camera
            print("Reset and Flush detector")
            exposure.reset()
            exposure.roi_reset()
            exposure.test(0)  # flush

            # bias images
            bias.acquire()
            itlutils.imsnap(self.imsnap_scale, "last")

            # gain images
            # gain.find()
            gain.acquire()

            # gainmap
            gainmap.acquire()

            # Prnu images
            azcam.db.tools["prnu"].acquire()

            # superflat sequence
            superflat.acquire()

            # PTC and linearity
            ptc.acquire()

            # QE
            qe.acquire()

            # Dark signal
            dark.acquire()

        finally:
            azcam.db.parameters.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        print("acquire sequence finished")

        return

    def analyze(self):
        """
        Analyze data.
        """

        print("Begin analysis of ASI294 dataset")
        rootfolder = azcam.utils.curdir()

        (
            exposure,
            gain,
            gainmap,
            bias,
            detcal,
            superflat,
            ptc,
            qe,
            dark,
            defects,
        ) = azcam_console.utils.get_tools(
            [
                "exposure",
                "gain",
                "gainmap",
                "bias",
                "detcal",
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

        # analyze gain map
        azcam.utils.curdir("gainmap")
        gainmap.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze superflats
        azcam.utils.curdir("superflat")
        try:
            superflat.analyze()
        except Exception:
            azcam.utils.curdir(rootfolder)
            azcam.utils.curdir("superflat")
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
        if defects.grade_dark_defects:
            defects.dark_filename = dark.dark_filename
            azcam.utils.curdir("dark")
            defects.analyze_bright_defects()
            defects.copy_data_files()
            azcam.utils.curdir(rootfolder)

        if defects.grade_bright_defects:
            defects.flat_filename = superflat.superflat_filename
            azcam.utils.curdir("superflat")
            defects.analyze_dark_defects()
            defects.copy_data_files()
            azcam.utils.curdir(rootfolder)

        if defects.grade_dark_defects or defects.grade_bright_defects:
            azcam.utils.curdir("defects")
            defects.analyze()
            azcam.utils.curdir(rootfolder)
            print("")

        # analyze qe
        azcam.utils.curdir("qe")
        azcam.db.tools["qe"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # analyze prnu
        azcam.utils.curdir("prnu")
        azcam.db.tools["prnu"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # make report
        self.make_summary_report()
        self.make_report()

        return

    def copy_files(self):
        """
        Copy both report and flats
        """

        itlutils.cleanup_files()
        self.copy_reports()
        self.copy_flats()

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
            for filename in fnmatch.filter(filenames, "ASI294_Report_*.pdf"):
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


# create instance
detchar = ASI294DetChar()

(
    exposure,
    gain,
    gainmap,
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
        "gainmap",
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

detchar.start_temperature = 20.0
# ***********************************************************************************
# parameters
# ***********************************************************************************
azcam_console.utils.set_image_roi([[500, 600, 500, 600], [500, 600, 500, 600]])

# values below for binned 2x2, ~1 e/DN, ~5,000 DN
detcal.exposures = {
    400: 10.0,
    425: 7.0,
    450: 6.0,
    475: 5.0,
    500: 5.0,
    525: 8.0,
    550: 10.0,
    575: 10.0,
    600: 10.0,
    625: 15.0,
    650: 18.0,
    675: 25.0,
    700: 30.0,
    725: 40.0,
    750: 60.0,
    775: 70.0,
    800: 100.0,
}
detcal.data_file = os.path.join(azcam.db.datafolder, "detcal_asi294.txt")
detcal.mean_count_goal = 5000
detcal.range_factor = 1.2

# bias
bias.number_images_acquire = 50

# gain
gain.number_pairs = 1
gain.exposure_time = 1.0
gain.wavelength = 500
gain.video_processor_gain = []

# gainmap
gainmap.number_bias_images = 20
gainmap.number_flat_images = 20
gainmap.exposure_time = 50
gainmap.wavelength = 500

# dark
dark.number_images_acquire = 5
dark.exposure_time = 600.0
dark.dark_fraction = -1  # no spec on individual pixels
# dark.mean_dark_spec = 3.0 / 600.0  # blue e/pixel/sec
# dark.mean_dark_spec = 6.0 / 600.0  # red
dark.use_edge_mask = 0
# dark.bright_pixel_reject = 0.05  # e/pix/sec clip
dark.overscan_correct = 0  # flag to overscan correct images
dark.zero_correct = 1  # flag to correct with bias residuals
dark.fit_order = 0
dark.report_dark_per_hour = 0  # report per hour

# superflats
superflat.exposure_level = 30000  # DN
superflat.wavelength = 500
superflat.number_images_acquire = 3

# ptc
ptc.wavelength = 500
ptc.gain_range = [0.5, 1.5]
ptc.overscan_correct = 0
ptc.fit_line = True
ptc.fit_min = 1000
ptc.fit_max = 60000
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
    63000,
]

# linearity
linearity.wavelength = 500
linearity.use_ptc_data = 1
linearity.fit_min = 0.10
linearity.fit_max = 0.90
linearity.fullwell_estimate = 55000.0  # DN
linearity.fit_all_data = 0
linearity.max_allowed_linearity = -1
linearity.plot_specifications = 1
linearity.plot_limits = [-3.0, +3.0]
linearity.overscan_correct = 0
linearity.zero_correct = 1
linearity.use_weights = 0

# QE
qe.cal_scale = 0.989  # 30Aug23 measured physically ARB
qe.global_scale = 0.95  # correction
qe.pixel_area = 0.002315**2
qe.flux_cal_folder = "/data/asi294"
qe.plot_limits = [[300.0, 800.0], [0.0, 100.0]]
qe.plot_title = "ZWO ASI294 Quantum Efficiency"
qe.qeroi = []
qe.overscan_correct = 0
qe.zero_correct = 1
qe.flush_before_exposure = 0
qe.grade_sensor = 0
qe.create_reports = 1
qe.use_exposure_levels = 1
qe.exptime_offset = 0.00
el = 5000  # DN
qe.exposure_levels = {
    400: el,
    425: el,
    450: el,
    475: el,
    500: el,
    525: el,
    550: el,
    575: el,
    600: el,
    625: el,
    650: el,
    675: el,
    700: el,
    725: el,
    750: el,
    775: el,
    800: el,
}

if 1:
    qe.window_trans = {
        300: 1.0,
        1000: 1.0,
    }
else:
    # from online plot
    qe.window_trans = {
        400: 0.95,
        450: 0.99,
        500: 0.99,
        550: 0.99,
        600: 0.99,
        650: 0.99,
        700: 0.95,
        750: 0.93,
        800: 0.90,
    }

# prnu
prnu.root_name = "prnu."
prnu.use_edge_mask = 0
prnu.overscan_correct = 0
prnu.zero_correct = 1
prnu.mean_count_goal = 3000  # DN
prnu.exposure_levels = {
    400: prnu.mean_count_goal,
    450: prnu.mean_count_goal,
    500: prnu.mean_count_goal,
    550: prnu.mean_count_goal,
    600: prnu.mean_count_goal,
    650: prnu.mean_count_goal,
    700: prnu.mean_count_goal,
    750: prnu.mean_count_goal,
    800: prnu.mean_count_goal,
}

# defects
defects.grade_bright_defects = 0
defects.grade_dark_defects = 0

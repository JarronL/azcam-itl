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
import azcam.exceptions
import azcam_console.console
import azcam.utils
from azcam_console.testers.detchar import DetChar
from azcam_itl import itlutils


class ASI183DetChar(DetChar):
    def __init__(self):
        super().__init__()

        self.imsnap_scale = 1.0
        self.start_temperature = None # -15.0

        self.start_delay = 0

        # reports
        self.report_names = [
            "gain",
            "bias",
            "superflat",
            "prnu",
            "ptc",
            "linearity",
            "qe",
            "darksignal",
            "brightdefects",
            "defects",
            "fe55",
        ]
        self.report_files = {
            "darksignal": "dark/dark",
            "brightdefects": "dark/brightdefects",
            "superflat": "superflat/darkdefects",
            "defects": "defects/defects",
            "fe55": "fe55/fe55",
            "gain": "gain/gain",
            "linearity": "ptc/linearity",
            "ptc": "ptc/ptc",
            "prnu": "qe/prnu",
            "qe": "qe/qe",
            "bias": "bias/bias",
        }

    def setup(self, camera_id="2f348f01230009000"):
        """
        Setup
        """

        # camera_id="1812911309020900"

        self.camera_id = azcam.utils.prompt("Enter camera ID", camera_id)

        # sponsor/report info
        self.customer = "UASAL"
        self.system = "ASI183MM-P"
        self.summary_report_name = f"SummaryReport_{self.camera_id}"
        self.report_name = f"CharacterizationReport__ASI183_{self.camera_id}.pdf"
        self.operator = azcam.utils.prompt("Enter operator", "lab user")

        self.summary_lines = []
        self.summary_lines.append("# ITL Camera Characterization Report")

        self.summary_lines.append(f"|Project        |STP|")
        self.summary_lines.append("|:---|:---|")
        self.summary_lines.append(f"|Customer       |UASAL|")
        self.summary_lines.append(f"|System         |ZWO ASI183MM-P|")
        self.summary_lines.append(f"|ID             |{self.camera_id}|")
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
        if self.start_temperature is not None:
            print(f"Waiting for temperature to get below {self.start_temperature:.1f} C")
            while True:
                t = tempcon.get_temperatures()[0]
                print(f"  Current temperature: {t:.1f}")
                if t <= self.start_temperature + 0.5:
                    break
                else:
                    time.sleep(10)

        print(f"Testing device {self.camera_id}")

        # *************************************************************************
        # save current image parameters
        # *************************************************************************
        impars = {}
        azcam.utils.save_imagepars(impars)

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
        azcam.db.parameters.set_par("imagefolder", reportfolder)

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
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        print("acquire sequence finished")

        return

    def analyze(self):
        """
        Analyze data.
        """

        print("Begin analysis of ASI183 dataset")
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
        if 0:
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
        if 0:
            azcam.utils.curdir("gainmap")
            gainmap.analyze()
            azcam.utils.curdir(rootfolder)
            print("")

        # analyze superflats
        azcam.utils.curdir("superflat1")
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

        # total defects
        if 1:
            fldr = os.path.abspath("./defects")
            if os.path.exists(fldr):
                pass
            else:
                os.mkdir(fldr)
            azcam.utils.curdir("defects")
            defects.analyze()
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
            for filename in fnmatch.filter(filenames, "ASI183_Report_*.pdf"):
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

# Try to initialize the temperature controller
tempcon = azcam.db.tools["tempcon"]
try:
    tempcon.initialize()
    ctemp_set = tempcon.get_control_temperature()
    ctemp_sensor = tempcon.get_temperatures()[0]
    print(f"Control sensor temperature: {ctemp_sensor:.2f} C")
    print(f"Control sensor setpoint: {ctemp_set:.1f} C")
except:
    azcam.exceptions.warning("WARNING: Temperature controller could not initialize!")

# create instance
detchar = ASI183DetChar()

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

# detchar.start_temperature = 20.0
# ***********************************************************************************
# parameters
# ***********************************************************************************
azcam_console.utils.set_image_roi([[500, 600, 500, 600], [500, 600, 500, 600]])

# values below for binned 1x1, Gain=0
# mult all by 3x
detcal.exposures = {
    400: 2.0,
    420: 1.4,
    440: 1.2,
    460: 1.5,
    480: 1.5,
    500: 1.5,
    520: 1.6,
    540: 2.0,
    560: 2.0,
    580: 2.0,
    600: 2.0,
    620: 3.0,
    640: 3.0,
    660: 4.0,
    680: 5.0,
    700: 6.0,
    720: 8.0,
    740: 10.0,
    760: 12.0,
    780: 14.0,
    800: 20.0,
}
detcal.data_file = os.path.join(azcam.db.datafolder, "detcal_asi183.txt")
detcal.mean_count_goal = 4500
detcal.range_factor = 1.3

# bias
bias.number_images_acquire = 50

# gain
gain.number_pairs = 1
gain.exposure_time = 1.0
gain.wavelength = 400
gain.video_processor_gain = []

# gainmap
gainmap.number_bias_images = 20
gainmap.number_flat_images = 20
gainmap.exposure_time = 1
gainmap.wavelength = 500

# dark signal and bright pixels
dark.number_images_acquire = 5
dark.exposure_time = 600.0
dark.mean_dark_spec = -1
dark.bright_pixel_reject = 0.05  # e/pix/sec clip
dark.allowable_bright_pixels = -1
dark.overscan_correct = 0  # flag to overscan correct images
dark.zero_correct = 1  # flag to correct with bias residuals
dark.report_plots = ["darkimage"]  # plots to include in report
dark.report_dark_per_hour = 0
dark.grade_dark_signal = 0
dark.grade_bright_defects = 0

# superflats and dark pixels
superflat.exposure_time = 5.0
superflat.wavelength = 500
superflat.number_images_acquire = 3  # number of images
superflat.grade_dark_defects = 0
superflat.dark_pixel_reject = 0.50  # reject pixels below this value from mean
superflat.allowable_dark_pixels = -1
superflat.grade_sensor = 0

# ptc
ptc.wavelength = 500
# ptc.gain_range = [0.1, 0.3]
ptc.overscan_correct = 0
ptc.fit_line = True
ptc.fit_min_percent = 0.10
ptc.fit_max_percent = 0.90
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
linearity.fit_min_percent = 0.10
linearity.fit_max_percent = 0.90
linearity.fullwell_estimate = 55000.0  # DN
linearity.fit_all_data = 0
linearity.max_allowed_linearity = -1
linearity.plot_specifications = 1
linearity.plot_limits = [-3.0, +3.0]
linearity.overscan_correct = 0
linearity.zero_correct = 1
linearity.use_weights = 0

# QE
qe.cal_scale = 1.011  # 01May24 measured physically ARB
qe.global_scale = 1.0  # correction
qe.pixel_area = 0.002315**2
qe.flux_cal_folder = "/data/asi183"
qe.plot_limits = [[400.0, 800.0], [0.0, 100.0]]
qe.plot_title = "ZWO ASI183 Quantum Efficiency"
qe.qeroi = []
qe.overscan_correct = 0
qe.zero_correct = 1
qe.grade_sensor = 0
qe.create_reports = 1
qe.use_exposure_levels = 1
qe.exptime_offset = 0.00
el = 5000  # DN
qe.exposure_levels = {
    400: el,
    420: el,
    440: el,
    460: el,
    480: el,
    500: el,
    520: el,
    540: el,
    560: el,
    580: el,
    600: el,
    620: el,
    640: el,
    660: el,
    680: el,
    700: el,
    720: el,
    740: el,
    760: el,
    780: el,
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
        440: 0.99,
        500: 0.99,
        700: 0.95,
        760: 0.93,
        800: 0.90,
    }

# prnu
prnu.root_name = "prnu."
prnu.overscan_correct = 0
prnu.zero_correct = 1
prnu.mean_count_goal = 3000  # DN
prnu.exposure_levels = {
    400: prnu.mean_count_goal,
    460: prnu.mean_count_goal,
    500: prnu.mean_count_goal,
    560: prnu.mean_count_goal,
    600: prnu.mean_count_goal,
    660: prnu.mean_count_goal,
    700: prnu.mean_count_goal,
    760: prnu.mean_count_goal,
    800: prnu.mean_count_goal,
}

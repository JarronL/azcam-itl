import datetime
import fnmatch
import glob
import os
import re
import shutil
import subprocess
import time

import azcam
import azcam.utils
import azcam_console.console
from azcam_console.testers.detchar import DetChar
from azcam_itl import itlutils


class IMX411DetChar(DetChar):
    def __init__(self):
        super().__init__()

        self.imsnap_scale = 1.0
        self.start_temperature = 0.0

        self.operator = ""
        self.camera_id = ""

        self.system = ""
        self.customer = ""

        self.report_date = ""
        self.report_id = ""
        self.report_comment = ""

        self.start_delay = 5

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

    def setup(self, camera_id=""):

        if camera_id == "":
            self.camera_id = azcam.utils.prompt("Enter camera ID", camera_id)

        # sponsor/report info
        self.customer = "UArizona"
        self.system = "IMX411"

        self.summary_report_name = f"SummaryReport_{self.camera_id}"
        self.report_name = f"IMX411_{self.camera_id}.pdf"

        self.summary_lines = []
        self.summary_lines.append("# ITL Sensor Characterization Report")

        self.summary_lines.append("|||")
        self.summary_lines.append("|:---|:---|")
        self.summary_lines.append(f"|Customer       |UArizona|")
        self.summary_lines.append(f"|Project        |Oracle Search Sensor-2|")
        self.summary_lines.append(f"|System         |Sony IMX411|")
        self.summary_lines.append(f"|Camera SN      |{self.camera_id}|")
        self.summary_lines.append(f"|Author         |{self.operator}|")

        self.is_setup = 1

        return

    def acquire(self, camera_id=""):
        """
        Acquire sensor characterization data.
        """

        print("Starting acquisition sequence")
        print("")

        if not self.is_setup:
            self.setup(camera_id)

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
            print(f"Waiting for start tempertare: {self.start_temperature:.01f}")
            while True:
                t = tempcon.get_temperatures()[0]
                print(f"Current temperature: {t:.01f}")
                if t <= self.start_temperature + 0.5:
                    break
                else:
                    time.sleep(10)

        print(f"Testing device {self.camera_id}")

        # *************************************************************************
        # save current image parameters
        # *************************************************************************
        impars = {}
        print(detcal.data_file)
        azcam.utils.save_imagepars(impars)
        print(detcal.data_file)

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
            print("Reset and Flush sensor")
            exposure.reset()
            exposure.roi_reset()
            exposure.test(0)  # flush

            # clear device after reset delay
            print(f"Delaying start for {self.start_delay:.0f} seconds (to settle)...")
            time.sleep(self.start_delay)
            exposure.test(0)  # flush

            # bias images
            bias.acquire()
            itlutils.imsnap(self.imsnap_scale, "last")

            # gain images
            gain.find()

            # Prnu images
            azcam.db.tools["prnu"].acquire()

            # superflat sequence
            superflat.acquire()

            # PTC and linearity
            ptc.acquire()

            # QE
            qe.acquire()

            if 1:
                # Dark signal
                exposure.test(0)
                dark.acquire()
            else:
                print("Close shutter and run dark.acquire()")

        finally:
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        print("acquire sequence finished")

        return

    def analyze(self, report_id="unknown"):
        """
        Analyze data.
        """

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
            defects,
            linearity,
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
            ]
        )

        if not self.is_setup:
            self.setup(report_id)

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
        linearity.analyze()
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


# create instance
detchar = IMX411DetChar()

# define tools
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

detchar.start_temperature = 10.0
detchar.operator = "Lesser"

# ***********************************************************************************
# parameters
# ***********************************************************************************
# azcam_console.utils.set_image_roi([[4000, 4100, 3000, 3100], [4000, 4100, 3000, 3100]])
azcam_console.utils.set_image_roi([[1000, 1100, 1000, 1100], [1000, 1100, 1000, 1100]])

# detcal
# values below estimates for unbinned values, 5000 DN, gain=1, 0.8 e/DN
scale = 1.0
detcal.exposures = {
    350: 220.0 * scale,
    400: 14.0 * scale,
    450: 10.0 * scale,
    500: 8.7 * scale,
    550: 12.2 * scale,
    600: 12.6 * scale,
    650: 23.2 * scale,
    700: 40.0 * scale,
    750: 72.3 * scale,
    800: 157.0 * scale,
    850: 103.0 * scale,
    900: 122.0 * scale,
    950: 243.0 * scale,
    1000: 453.0 * scale,
}
detcal.data_file = os.path.join(azcam.db.datafolder, "detcal_IMX411.txt")
detcal.mean_count_goal = 5000
detcal.range_factor = 1.3

# bias
bias.number_images_acquire = 10
bias.overscan_correct = 0

# gain
gain.number_pairs = 1
gain.exposure_time = 5.0
gain.wavelength = 500
gain.video_processor_gain = []


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
ptc.gain_range = [0.4, 1.2]
ptc.overscan_correct = 0
ptc.zero_correct = 1
ptc.fit_line = True
ptc.fullwell_estimate = 54000 / 0.8  # counts
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
linearity.fullwell_estimate = 65000  # counts
linearity.fit_all_data = 0
linearity.fit_min_percent = 0.05
linearity.fit_max_percent = 0.90  # .95 too close to ADC limit

linearity.max_allowed_linearity = -1
linearity.plot_specifications = 1
linearity.plot_limits = [-4.0, +4.0]
linearity.overscan_correct = 0
linearity.zero_correct = 1
linearity.use_weights = 1

# QE
qe.cal_scale = 1.178
qe.global_scale = 1.0
qe.pixel_area = 0.00376**2
qe.flux_cal_folder = "/data/IMX411"
qe.plot_limits = [[300.0, 1000.0], [0.0, 100.0]]
qe.plot_title = "IMX411 Quantum Efficiency"
qe.qeroi = []
qe.overscan_correct = 0
qe.zero_correct = 1
qe.grade_sensor = 0
qe.create_reports = 1
qe.use_exposure_levels = 1
qe.exptime_offset = 0.00
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
    850: el,
    900: el,
    950: el,
    1000: el,
}
if 1:
    qe.window_trans = {
        300: 1.0,
        1000: 1.0,
    }
else:
    # from online plot
    qe.window_trans = {
        350: 0.25,
        400: 0.95,
        450: 0.99,
        500: 0.99,
        550: 0.99,
        600: 0.99,
        650: 0.99,
        700: 0.95,
        750: 0.93,
        800: 0.90,
        850: 0.85,
        950: 0.78,
        1000: 0.75,
    }

# prnu
prnu.root_name = "prnu."
prnu.overscan_correct = 0
prnu.zero_correct = 1
el = 5000.0
prnu.exposure_levels = {
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
    850: el,
    900: el,
    950: el,
    1000: el,
}
prnu.mean_count_goal = 5000.0

# defects
defects.bright_pixel_reject = 20.0 / 3600 * 10  # 10x mean dark current [e/pix/sec]
defects.dark_pixel_reject = 0.80  # below mean

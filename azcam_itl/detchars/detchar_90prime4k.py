import datetime
import fnmatch
import os
import shutil
import time

import azcam
import azcam.utils
import azcam.exceptions
import azcam_console.console
from azcam_console.testers.detchar import DetChar
from azcam_itl import itlutils


class PrimeFocus4kDetChar(DetChar):
    """
    The DetChar class for acquistion and analysis of STA4850 CCDs for 90prime.
    """

    def __init__(self):
        super().__init__()

        self.start_delay = 0
        self.start_temperature = -999.99

        self.device_type = ""
        self.lot = "UNKNOWN"
        self.wafer = "UNKNOWN"
        self.die = "UNKNOWN"

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

        s = azcam.utils.curdir()
        try:
            x = s.index("DIEID-")
            if x > 0:
                id = s[x + 6 : x + 9]
            else:
                id = 0
        except ValueError:
            id = 0
        self.camera_id = azcam.utils.prompt("Enter sensor ID", f"DIEID-{id}")

        # ****************************************************************
        # Identification
        # ****************************************************************
        if self.camera_id == "":
            azcam.exceptions.warning("Unspecified sensor ID")
            self.camera_id = ""
            self.package_id = ""
        else:
            self.wafer = azcam.utils.prompt("Enter wafer")
            self.lot = azcam.utils.prompt("Enter lot")
            self.device_type = "STA4850"
            self.package_id = azcam.utils.prompt("Enter package ID")
        self.report_name = f"CharacterizationReport_{self.camera_id}"

        # sponsor/report info
        self.customer = "University of Arizona"
        self.system = "ITL3"

        if self.operator.lower() == "mpl":
            self.operator = "Michael Lesser"
        else:
            self.operator = ""

        self.summary_lines = []
        self.summary_lines.append("# 90Prime4k Sensor Characterization Report")

        self.summary_lines.append("|||")
        self.summary_lines.append("|:---|:---|")
        self.summary_lines.append(f"|Customer       |{self.customer}|")
        self.summary_lines.append(f"|ITL Package    |{self.package_id}|")
        self.summary_lines.append(f"|ITL ID         |{self.camera_id}|")
        self.summary_lines.append(f"|Type           |STA4850|")
        self.summary_lines.append(f"|System         |{self.system}|")
        self.summary_lines.append(f"|Operator       |{self.operator}|")

        self.summary_report_name = f"SummaryReport_{self.camera_id}"

        self.is_setup = True

        return

    def acquire(self, SN="prompt"):
        """
        Acquire detector characterization data.
        """

        if not self.is_setup:
            self.setup()
        id = self.camera_id

        # define  tools
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
            fe55,
            exposure,
            tempcon,
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
                "fe55",
                "exposure",
                "tempcon",
            ]
        )

        print(f"Testing device {id}")

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

        # *************************************************************************
        # save current image parameters
        # *************************************************************************
        impars = {}
        azcam.utils.save_imagepars(impars)

        # *************************************************************************
        # Create and move to a report folder
        # *************************************************************************
        currentfolder, reportfolder = azcam_console.utils.make_file_folder(
            "report", 1, 1
        )
        azcam.utils.curdir(reportfolder)
        azcam.db.parameters.set_par("imagefolder", reportfolder)

        # define  tools
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
            fe55,
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
                "fe55",
            ]
        )
        exposure = azcam.db.tools["exposure"]

        # *************************************************************************
        # Acquire
        # *************************************************************************

        # bias sequenece
        try:
            bias.acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)
        # gain acquire and analyze
        try:
            gain.find()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # superflat sequence
        try:
            superflat.acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # QE sequence
        try:
            qe.acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # PTC sequence
        try:
            ptc.acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # Dark sequence
        try:
            dark.acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # Fe55 sequence
        try:
            fe55.acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # finish
        azcam.utils.restore_imagepars(impars)
        azcam.utils.curdir(currentfolder)

        # send email notice
        finishedtime = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
        message = f"Script finished for SN{self.itl_id} today at {finishedtime}"
        itlutils.mailto("mlesser@arizona.edu", "LVM acquire script finished", message)

        print("Acquisition sequence finished")

        return

    def prepare(self):
        """
        Prepare for data sequences with calibrations.
        """

        # setup for headers but should already be done by .acquire()
        if not self.is_setup:
            self.setup()

        # save pars to be changed
        impars = {}
        azcam.utils.save_imagepars(impars)
        currentfolder = azcam.utils.curdir()

        # uniform image sequence numbers
        azcam.db.parameters.set_par("imagesequencenumber", 1)

        # clear device after reset delay
        print("Delaying start for %.0f seconds (to settle)..." % self.start_delay)
        time.sleep(self.start_delay)
        print("Flush detector")
        exposure.test(0)

        # gain sequence - do this before detcal
        if 0:
            try:
                gain.find()
            except Exception:
                azcam.utils.restore_imagepars(impars)
                azcam.utils.curdir(currentfolder)
                return

        # detcal sequence - multiple NDs used
        if 0:
            try:
                detcal.calibrate()
            except Exception:
                azcam.utils.restore_imagepars(impars)
                azcam.utils.curdir(currentfolder)
                return

        return

    def analyze(self):
        """
        Analyze data.
        """

        rootfolder = azcam.utils.curdir()

        if not self.is_setup:
            self.setup()

        # define  tools
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
            fe55,
            prnu,
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
                "fe55",
                "prnu",
            ]
        )

        # bias
        azcam.utils.curdir("bias")
        bias.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # gain
        azcam.utils.curdir("gain")
        gain.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # superflats
        azcam.utils.curdir("superflat")
        superflat.analyze()
        azcam.utils.curdir(rootfolder)

        # PTC
        azcam.utils.curdir("ptc")
        ptc.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # linearity from PTC data
        azcam.utils.curdir("ptc")
        azcam.db.tools["linearity"].analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # Fe-55
        azcam.utils.curdir("fe55")
        fe55.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # darks
        azcam.utils.curdir("dark")
        dark.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # qe
        azcam.utils.curdir("qe")
        qe.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # prnu
        azcam.utils.curdir("qe")
        prnu.analyze()
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

        # report
        self.make_summary_report()
        self.make_report()

        return


# create instance
detchar = PrimeFocus4kDetChar()

azcam_console.utils.set_image_roi([[1800, 1900, 1800, 1900], [2042, 2058, 1500, 1800]])
detchar.start_temperature = -115.0

# define  tools
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
    fe55,
    exposure,
    tempcon,
    linearity,
    prnu,
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
        "fe55",
        "exposure",
        "tempcon",
        "linearity",
        "prnu",
    ]
)

# total defects
defects.edge_size = 10
defects.allowable_bad_pixels = -1
defects.grade_sensor = 0

# bias
bias.number_images_acquire = 3
bias.fit_order = 3

# gain
gain.number_pairs = 1
gain.exposure_time = 1.0
gain.wavelength = 500
gain.grade_sensor = 0

# fe55
fe55.number_images_acquire = 1
fe55.system_noise_correction = []
fe55.gain_estimate = 4 * [2.6]
fe55.exposure_time = 30.0
fe55.neighborhood_size = 5
fe55.fit_psf = 0
fe55.threshold = 500
fe55.spec_sigma = -1
fe55.hcte_limit = 0.999_990
fe55.vcte_limit = 0.999_990
fe55.spec_by_cte = 1
fe55.overscan_correct = 1
fe55.pause_each_channel = 0
fe55.report_include_plots = 1
fe55.make_plots = ["histogram", "cte"]
fe55.plot_files = {
    "histogram": "histogram.png",
    "hcte": "hcte.png",
    "vcte": "vcte.png",
}
fe55.plot_titles = {
    "histogram": "X-Ray Histogram Plot.",
    "hcte": "HCTE Plot.",
    "vcte": "VCTE Plot.",
}
fe55.plot_order = ["histogram", "hcte", "vcte"]

# superflats and dark pixels
superflat.exposure_time = 5.0
superflat.wavelength = 500
superflat.number_images_acquire = 3  # number of images
superflat.grade_dark_defects = 1
superflat.dark_pixel_reject = 0.50  # reject pixels below this value from mean
superflat.allowable_dark_pixels = -1
superflat.grade_sensor = 0

# ptc
ptc.wavelength = 550
ptc.exposure_times = [
    1,
    2,
    3,
    5,
    10,
    15,
    20,
    25,
    30,
    35,
    40,
    45,
    50,
    55,
    60,
]
ptc.gain_range = [1.0, 4.0]
ptc.fit_max = 60000
ptc.fit_line = 1
ptc.overscan_correct = 1
ptc.exposure_levels = []

# linearity
linearity.use_ptc_data = 1
linearity.fit_min_percent = 0.10
linearity.fit_max_percent = 0.90
linearity.fit_all_data = 0
linearity.max_allowed_linearity = 0.02  # max residual spec
linearity.plot_specifications = 1
linearity.plot_limits = [-3, 3]
linearity.overscan_correct = 0  # normally 1, but ptc already analyzed
linearity.zero_correct = 0

# dark signal and bright pixels
dark.number_images_acquire = 3
dark.exposure_time = 500.0
dark.mean_dark_spec = 10.0 / 3600
dark.bright_pixel_reject = 0.05  # e/pix/sec clip
dark.allowable_bright_pixels = 0.0001 * 4096 * 4096  # 1678
dark.overscan_correct = 1  # flag to overscan correct images
dark.zero_correct = 1  # flag to correct with bias residuals
dark.report_plots = ["darkimage"]  # plots to include in report
dark.report_dark_per_hour = 1
dark.grade_dark_signal = 1
dark.grade_bright_defects = 1

# prnu
prnu.allowable_deviation_from_mean = 0.1
prnu.root_name = "qe."
prnu.overscan_correct = 1
prnu.wavelengths = [350, 400, 500, 600, 700, 800]
prnu.grade_sensor = 0

# qe
qe = qe
qe.cal_scale = 1.00
qe.global_scale = 1.24
qe.flux_cal_folder = "/data/90prime4k"
qe.pixel_area = 0.015 * 0.015
qe.plot_limits = [[300.0, 1000.0], [0.0, 100.0]]
qe.overscan_correct = 1
qe.plot_title = "90Prime QE"
qe.qeroi = []
qe.qe_specs = {}
qe.window_trans = {
    300: 1.0,
    1000: 1.0,
}
qe.exposure_times = {
    300: 10.0,
    350: 10.0,
    400: 5.0,
    450: 5.0,
    500: 5.0,
    550: 5.0,
    600: 5.0,
    650: 5.0,
    700: 5.0,
    750: 5.0,
    800: 10.0,
    850: 10.0,
    900: 20.0,
    950: 20.0,
    1000: 30.0,
}

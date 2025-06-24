import datetime
import os
import time
import shutil

import azcam
import azcam.utils
import azcam.exceptions
import azcam_console.console
import azcam_console.plot
from azcam_console.testers.detchar import DetChar
from azcam_itl import itlutils


class DesiDetCharClass(DetChar):
    """
    Detchar class for DESI sensors.
    """

    def __init__(self):
        super().__init__()

        self.device_type = ""
        self.lot = "UNKNOWN"
        self.wafer = "UNKNOWN"
        self.die = "UNKNOWN"
        self.coating = "UNKNOWN"

        self.start_delay = 0
        self.start_temperature = -1000

        self.use_fe55_gain = 1

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
            self.camera_id = "UNKNOWN"
            self.package_id = "UNKNOWN"
        else:
            self.device_type = "STA4150"
            self.lot = azcam.utils.prompt("Enter lot", "232139")
            self.wafer = azcam.utils.prompt("Enter wafer")
            self.package_id = azcam.utils.prompt("Enter package ID")
        self.coating = azcam.utils.prompt("Enter AR coating (RED or BLUE)", "UNKNOWN").upper()
        self.report_name = f"CharacterizationReport_{self.camera_id}"

        self.operator = azcam.utils.prompt("Enter operator", "lab user")

        # fixed info
        self.die = 1

        self.summary_lines = []
        self.summary_lines.append("# ITL Sensor Characterization Report")

        self.summary_lines.append(f"|Project        |DESI|")
        self.summary_lines.append("|:---|:---|")
        self.summary_lines.append(f"|Customer       |LBNL|")
        self.summary_lines.append(f"|ITL System     |ITL2|")
        self.summary_lines.append(f"|ITL Package    |{self.package_id}|")
        self.summary_lines.append(f"|ITL ID         |{self.camera_id}|")
        self.summary_lines.append(f"|Type           |STA4150|")
        self.summary_lines.append(f"|Lot            |{self.lot}|")
        self.summary_lines.append(f"|Wafer          |{self.wafer}|")
        self.summary_lines.append(f"|Die            |{self.die}|")
        self.summary_lines.append(f"|AR Coating     |{self.coating}|")
        self.summary_lines.append(f"|Operator       |{self.operator}|")

        self.summary_report_name = f"SummaryReport_{self.camera_id}"

        self.is_setup = 1

        return

    def acquire(self, SN="prompt"):
        """
        Acquire detector characterization data.
        """

        if not self.is_setup:
            self.setup()
        id = self.camera_id

        print(f"Testing device {id}")

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

        # wait for temperature
        if self.start_temperature != -1000:
            while True:
                t = tempcon.get_temperatures()[0]
                print("Current temperature: %.1f" % t)
                if t <= self.start_temperature + 0.5:
                    break
                else:
                    time.sleep(10)

        # clear sensor
        print("Clear sensor")
        exposure.roi_reset()
        exposure.test(0)

        try:
            # *************************************************************************
            # gain images (acquire and analyze gain)
            # *************************************************************************
            gain.find()

            # *************************************************************************
            # calibrate detcal
            # *************************************************************************
            detcal.read_datafile(detcal.data_file)
            # detcal.calibrate()

            # *************************************************************************
            # Acquire data
            # *************************************************************************
            azcam.db.parameters.set_par(
                "imagesequencenumber", 1
            )  # uniform image sequence numbers

            # clear device after reset delay
            if self.start_delay > 0:
                print(
                    "Delaying start for %.0f seconds (to settle)..." % self.start_delay
                )
                time.sleep(self.start_delay)
            exposure.test(0)  # flush

            # bias images
            bias.acquire()

            # superflat sequence
            if self.coating.upper() == "BLUE":
                superflat.wavelength = 400  # blue - dark defects
            elif self.coating.upper() == "RED":
                superflat.wavelength = 650  # red - dark defects
            else:
                superflat.wavelength = 500
            superflat.acquire()

            # PTC and linearity
            ptc.acquire()

            # QE and Prnu
            qe.acquire()

            # Dark signal
            exposure.test(0)
            dark.acquire()

            # Fe55
            fe55.acquire()

        except Exception:
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)
            return

        # finish
        azcam.utils.restore_imagepars(impars)
        azcam.utils.curdir(currentfolder)

        # send email notice
        finishedtime = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
        # message = "Script finished today at: %s" % (finishedtime)
        # itlutils.mailto("mlesser@arizona.edu", "DESI acquire script finished", message)

        print(f"Script finished at {finishedtime}")

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

        # Fe-55
        azcam.utils.curdir("fe55")
        fe55.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # use fe55 gain from now on
        if self.use_fe55_gain:
            gain.fe55_gain()

        # darks
        azcam.utils.curdir("dark")
        dark.analyze()
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
        linearity.analyze()
        azcam.utils.curdir(rootfolder)
        print("")

        # qe
        azcam.utils.curdir("qe")
        # spec for DESI Blue: 360-400 > 75%, 400-600 > 85%
        # spec for DESI Red: 600-750 > 85%
        if self.coating.upper() == "BLUE":
            for key in qe.qe_specs.keys():
                if key>=360 and key<=400:
                    qe.qe_specs[key] = 0.75
                elif key>400 and key<=600:
                    qe.qe_specs[key] = 0.85
                else:
                    qe.qe_specs[key] = 0
        elif self.coating.upper() == "RED":
            for key in qe.qe_specs.keys():
                if key>=600 and key<=750:
                    qe.qe_specs[key] = 0.85
                else:
                    qe.qe_specs[key] = 0
        else:
            azcam.log("Unknown AR coating, QE specs set to 0")
            qe.qe_specs = {w:0 for w in qe.wavelengths}
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

        # Close plot windows
        print("Finished analysis. Closing all plot windows.\n")
        azcam_console.plot.close_figure("all")

        # report
        self.make_summary_report()
        self.make_report()

        return

    def make_upload(self):
        """
        Prepare a dataset for upload by creating a compressed tar file.
        """

        cd = azcam.utils.curdir()
        pathname = cd
        foldername = os.path.basename(pathname)

        try:
            x = pathname.index("DIEID-")
            if x > 0:
                id = pathname[x + 6 : x + 9]
            else:
                raise ValueError

            idstring = f"DIEID{id}_{foldername}"
        except ValueError:
            id = 0
            idstring = azcam.utils.prompt("Enter desired archive name")

        # cleanup folder
        azcam.log("cleaning dataset folder")
        itlutils.cleanup_files(pathname)

        # copy folder to new name
        azcam.log(f"copying dataset to {idstring}")
        # shutil.copytree(os.path.basename(pathname), idstring)
        shutil.copytree(pathname, idstring)

        # make tar file
        azcam.log(f"making tar file: {idstring}.tar")
        tarfile = itlutils.archive(idstring, "tar")

        azcam.utils.curdir(cd)

        # Remove the copied folder
        azcam.log(f"Removing copied folder {idstring}")
        shutil.rmtree(idstring)

        return tarfile


# Try to initialize the temperature controller
tempcon = azcam.db.tools['tempcon']
try:
    tempcon.initialize()
    ctemp_sensor = tempcon.get_temperatures()[0]
    print(f"Control sensor temperature: {ctemp_sensor:.2f} C")
    ctemp_set = tempcon.get_control_temperature()
    print(f"Control sensor setpoint: {ctemp_set:.1f} C")
except:
    azcam.exceptions.warning("WARNING: Temperature controller could not initialize!")

# create instance
detchar = DesiDetCharClass()

# ROI
azcam_console.utils.set_image_roi([[1950, 2000, 400, 450], [2051, 2055, 400, 450]])

# define  tools
(
    gain,
    bias,
    detcal,
    superflat,
    ptc,
    linearity,
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
        "linearity",
        "qe",
        "dark",
        "defects",
        "dark",
        "fe55",
        "prnu",
    ]
)

# detcal
detcal.data_file = f"{azcam.db.datafolder}/detcal_desi.txt"
# detcal.exposures = {
#     350: 4.5,
#     400: 2.5,
#     500: 1.5,
#     550: 1.5,
#     600: 1.5,
#     600: 2.0,
#     700: 3.0,
#     750: 4.0,
#     800: 6,
# }
# blue, 06jun24
detcal.exposures = {
    350: 3.5,
    400: 1.5,
    450: 1.0,
    500: 1.0,
    550: 1.0,
    600: 1.0,
    650: 1.5,
    700: 2.0,
    750: 2.5,
    800: 3.5,
}

# total defects
defects.edge_size = 30  # 13 from Pat but serial clocking glow
defects.allowable_bad_pixels = 0.0001 * 4096 * 4096  # allowed total bad pixels
defects.grade_sensor = 1

# bias
bias.number_images_acquire = 3
bias.grade_sensor = 0

# gain
gain.number_pairs = 1
gain.exposure_time = 1
gain.wavelength = 500
gain.grade_sensor = 0

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

# superflats and dark pixels
superflat.exposure_time = 5.0
# Correct wavelength is selected during acquisition
# superflat.wavelength = 400  # blue - dark defects
# superflat.wavelength = 600  # red - dark defects
superflat.number_images_acquire = 3  # number of images
superflat.grade_dark_defects = 1
superflat.dark_pixel_reject = 0.50  # reject pixels below this value from mean
superflat.allowable_dark_pixels = 0.0001 * 4096 * 4096
superflat.grade_sensor = 1

# ptc
ptc.wavelength = 500
ptc.gain_range = [0.0, 2.0]
ptc.overscan_correct = 1
ptc.flush_before_exposure = 0
ptc.use_exposure_levels = 1
ptc.exposure_levels = [
    1000,
    2000,
    5000,
    10000,
    20000,
    30000,
    40000,
    45000,
    50000,
    55000,
    60000,
    65000,
]  # DN
ptc.grade_sensor = 0

# linearity
linearity.wavelength = 500
linearity.use_ptc_data = 1
linearity.fit_min_percent = 0.20
linearity.fit_max_percent = 0.90
linearity.fit_all_data = 0
linearity.max_allowed_linearity = 0.01  # max residual for linearity
linearity.plot_specifications = 1
linearity.plot_limits = [-3.0, +3.0]
linearity.overscan_correct = 1
linearity.zero_correct = 0
linearity.grade_sensor = 1

# QE
qe.cal_scale = 0.95  # ?
qe.global_scale = 1.31  # 17Jun24 from dewar case
qe.flush_before_exposure = 0
qe.pixel_area = 0.015 * 0.015
qe.flux_cal_folder = "/data/DESI"
qe.plot_title = "DESI Quantum Efficiency"
qe.plot_limits = [[300.0, 900.0], [0.0, 100.0]]
qe.qeroi = []
qe.use_exposure_levels = 1
qe.grade_sensor = 1
qe.wavelengths = [350, 400, 450, 500, 550, 600, 650, 700, 750, 800]
# Create dictionary of zeros for all wavelengths
# The QE specs will get updated during analysis
qe.qe_specs = {w:0 for w in qe.wavelengths}
qe.exposure_levels = {
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
qe.exposure_times = {}
qe.window_trans = {
    300: 0.92,
    1000: 0.92,
}

# prnu
prnu.allowable_deviation_from_mean = 0.1
prnu.root_name = "qe."
prnu.overscan_correct = 1
prnu.zero_correct = 0
prnu.wavelengths = [350, 400, 500, 600, 700, 800]
prnu.grade_sensor = 1

# fe55
fe55.overscan_correct = 0
fe55.zero_correct = 0
# fe55.dark_correct = 0 # NOTE: Appears to not be implemented (JML 2025-05-13)
# fe55.first_col_fit = 200

fe55.number_images_acquire = 1
fe55.exposure_time = 60.0
fe55.neighborhood_size = 5
fe55.fit_psf = 0
fe55.threshold = 400
fe55.spec_sigma = -1
fe55.hcte_limit = 0.999_990
fe55.vcte_limit = 0.999_990
fe55.spec_by_cte = 1
fe55.pause_each_channel = 0
fe55.report_include_plots = 1
fe55.gain_estimate = []
fe55.make_plots = ["histogram", "cte"]
fe55.system_noise_correction = 4 * [0.7]
fe55.plot_files = {
    "hcte": "hcte.png",
    "vcte": "vcte.png",
    "histogram": "histogram.png",
}
fe55.plot_titles = {
    "hcte": "HCTE Plot.",
    "vcte": "VCTE Plot.",
    "histogram": "X-Ray Histogram Plot.",
}
fe55.grade_sensor = 1

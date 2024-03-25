import datetime
import os
import subprocess
import time
import shutil

import azcam
import azcam.utils
import azcam.exceptions
import azcam.console
from azcam.testers.detchar import DetChar
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

        self.start_delay = 5  # acuisition starting delay in seconds

        # report parameters
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

    def setup(self, itl_id=""):

        s = azcam.utils.curdir()
        try:
            x = s.index("DIEID-")
            if x > 0:
                id = s[x + 6 : x + 9]
            else:
                id = 0
        except ValueError:
            id = 0
        self.itl_id = azcam.utils.prompt("Enter sensor ID", f"DIEID-{id}")

        # ****************************************************************
        # Identification
        # ****************************************************************
        if self.itl_id == "":
            azcam.exceptions.warning("Unspecified sensor ID")
            self.itl_id = ""
            self.package_id = ""
        else:
            self.wafer = azcam.utils.prompt("Enter wafer")
            self.lot = azcam.utils.prompt("Enter lot", "227599")
            self.device_type = "STA4150"
            self.package_id = azcam.utils.prompt("Enter package ID")

        # fixed info
        self.customer = "LBNL"
        self.system = "ITL2"
        self.die = 1

        self.summary_lines = []
        self.summary_lines.append("# DESI Sensor Characterization Report")

        self.summary_lines.append("|||")
        self.summary_lines.append("|:---|:---|")
        self.summary_lines.append(f"|Customer       |LBNL|")
        self.summary_lines.append(f"|ITL System     |DESI|")
        self.summary_lines.append(f"|ITL Package    |{self.package_id}|")
        self.summary_lines.append(f"|ITL ID         |{self.itl_id}|")
        self.summary_lines.append(f"|Type           |STA4150|")
        self.summary_lines.append(f"|Lot            |{self.lot}|")
        self.summary_lines.append(f"|Wafer          |{self.wafer}|")
        self.summary_lines.append(f"|Die            |{self.die}|")
        self.summary_lines.append(f"|Operator       |M. Lesser|")
        self.summary_lines.append(f"|System         |ITL2|")

        self.summary_report_name = f"SummaryReport_{self.itl_id}"

        self.is_setup = 1

        return

    def acquire(self, SN="prompt"):
        """
        Acquire detector characterization data.
        """

        if not self.is_setup:
            self.setup()
        id = self.itl_id

        print(f"Testing device {id}")

        # *************************************************************************
        # save current image parameters
        # *************************************************************************
        impars = {}
        azcam.db.parameters.save_imagepars(impars)

        # *************************************************************************
        # Create and move to a report folder
        # *************************************************************************
        currentfolder, reportfolder = azcam.console.utils.make_file_folder(
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
        ) = azcam.console.utils.get_tools(
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

        # clear sensor
        print("Clear sensor")
        exposure.roi_reset()
        exposure.test(0)

        try:
            # *************************************************************************
            # gain images
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
            print("Delaying start for %.0f seconds (to settle)..." % self.start_delay)
            time.sleep(self.start_delay)
            exposure.test(0)  # flush

            # bias images
            bias.acquire()

            # superflat sequence
            superflat.acquire()

            # PTC and linearity
            ptc.acquire()

            # QE and Prnu
            qe.acquire()

            # Dark signal
            exposure.test(0)
            dark.acquire()

            # Fe55
            # fe55.acquire()

        except Exception:
            azcam.db.parameters.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)
            return

        # finish
        azcam.db.parameters.restore_imagepars(impars)
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

        print("Begin analysis of DESI dataset")
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
        ) = azcam.console.utils.get_tools(
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

        # defects
        defects.dark_filename = dark.dark_filename
        azcam.utils.curdir("dark")
        defects.analyze_bright_defects()
        defects.copy_data_files()
        azcam.utils.curdir(rootfolder)

        defects.flat_filename = azcam.db.tools["superflat"].superflat_filename
        azcam.utils.curdir("superflat")
        defects.analyze_dark_defects()
        defects.copy_data_files()
        azcam.utils.curdir(rootfolder)

        azcam.utils.curdir("defects")
        defects.analyze()
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
        prnu.copy_data_files()
        azcam.utils.curdir(rootfolder)
        print("")

        # report
        self.make_summary_report()
        self.make_report()

        return

    def make_upload(self):
        """
        Prepare a dataset for upload by creating a compressed tar file.
        """

        idstring = f"{self.itl_id}"

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


# create instance
detchar = DesiDetCharClass()

# ROI
azcam.console.utils.set_image_roi([[1950, 2000, 400, 450], [2051, 2055, 400, 450]])

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
) = azcam.console.utils.get_tools(
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

# detcal
detcal.bias_goal = 1000
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
detcal.exposure_times = {
    350: 4.5,
    400: 2.5,
    400: 2.0,
    500: 1.5,
    550: 1.5,
    600: 1.5,
    600: 2.0,
    700: 3.0,
    750: 4.0,
    800: 6,
}
detcal.data_file = f"{azcam.db.datafolder}/detcal_desi.txt"

# bias
bias.number_images_acquire = 3
bias.grade_sensor = 0

# gain
gain.number_pairs = 1
gain.exposure_time = 1
gain.wavelength = 500
gain.grade_sensor = 0

# dark
dark.number_images_acquire = 3
dark.exposure_time = 500.0
dark.dark_fraction = -1  # no spec on individual pixels
dark.mean_dark_spec = 10.0 / 3600
dark.use_edge_mask = 1  #
dark.bright_pixel_reject = 5.0  # e/pix/sec clip
dark.overscan_correct = 1  # flag to overscan correct images
dark.zero_correct = 1  # flag to correct with bias residuals
dark.report_plots = ["darkimage"]  # plots to include in report
dark.report_dark_per_hour = 1
dark.grade_sensor = 1

# superflats
superflat.exposure_times = [5.0]  # xxx electrons
superflat.wavelength = 500  # used for dark defects
superflat.number_images_acquire = [3]  # number of images
superflat.grade_sensor = 0

# ptc
ptc.wavelength = 500
ptc.gain_range = [0.0, 2.0]
ptc.overscan_correct = 1
ptc.flush_before_exposure = 0
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
]  # in DN
ptc.grade_sensor = 0

# linearity
azcam.db.tools["linearity"].wavelength = 500
azcam.db.tools["linearity"].use_ptc_data = 1
azcam.db.tools["linearity"].fit_min = 1000.0
azcam.db.tools["linearity"].fit_max = 55000.0
azcam.db.tools["linearity"].max_allowed_linearity = 0.01  # max residual for linearity
azcam.db.tools["linearity"].plot_specifications = 1
azcam.db.tools["linearity"].plot_limits = [-3.0, +3.0]
azcam.db.tools["linearity"].overscan_correct = 1
azcam.db.tools["linearity"].zero_correct = 0
azcam.db.tools["linearity"].grade_sensor = 1

# QE
# qe.cal_scale = 0.955
# calibrated with dewar window and cal fixture
qe.cal_scale = 1.0
qe.global_scale = 1.0
qe.flush_before_exposure = 1
qe.use_edge_mask = 1
qe.pixel_area = 0.015 * 0.015
qe.flux_cal_folder = "/data/DESI"
qe.plot_title = "DESI Quantum Efficiency"
qe.plot_limits = [[300.0, 900.0], [0.0, 100.0]]
qe.qeroi = []
qe.use_exposure_levels = 1
qe.grade_sensor = 0
qe.wavelengths = [350, 400, 450, 500, 550, 600, 650, 700, 750, 800]
qe.qe_specs = {
    350: 0,
    400: 0,
    450: 0,
    500: 0,
    550: 0,
    600: 0,
    650: 0,
    700: 0,
    750: 0,
    800: 0,
}
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
    300: 1.0,
    1000: 1.0,
}
# qe.window_trans = {
#     300: 0.92,
#     1000: 0.92,
# }

# prnu
prnu.allowable_deviation_from_mean = 0.1
prnu.root_name = "qe."
prnu.use_edge_mask = 1
prnu.overscan_correct = 1
prnu.wavelengths = [350, 400, 500, 600, 700, 800]
prnu.grade_sensor = 0

# fe55
fe55.number_images_acquire = 1
fe55.exposure_time = 120.0
fe55.neighborhood_size = 5
fe55.fit_psf = 0
fe55.threshold = 400
fe55.spec_sigma = -1
fe55.hcte_limit = 0.999_990
fe55.vcte_limit = 0.999_990
fe55.spec_by_cte = 1
fe55.overscan_correct = 1
fe55.zero_correct = 0
fe55.pause_each_channel = 0
fe55.report_include_plots = 1
fe55.gain_estimate = []
fe55.make_plots = ["histogram", "cte"]
fe55.dark_correct = 0
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

# defects
defects.use_edge_mask = 1
defects.edge_size = 13  # from Pat
defects.allowable_bad_fraction = 0.0001  # % allowed bad pixels
defects.bright_pixel_reject = 5.0  # e/pix/sec
defects.dark_pixel_reject = 0.50  # reject pixels below this value from mean
defects.grade_sensor = 1

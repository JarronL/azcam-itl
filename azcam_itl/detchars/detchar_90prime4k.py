import datetime
import fnmatch
import os
import shutil
import subprocess
import time

import azcam
import azcam.utils
import azcam.console
from azcam.testers.detchar import DetChar
from azcam_itl import itlutils


class PrimeFocus4kDetChar(DetChar):
    """
    The DetChar class for acquistion and analysis of STA4850 CCDs for 90prime.
    """

    def __init__(self):
        super().__init__()

        self.SummaryPdfFile = None

        self.report_folder = ""  # top of report folder tree
        self.start_delay = 5  # aquisition starting delay in seconds

        self.device_type = ""
        self.backside_bias = 0.0
        self.lot = "UNKNOWN"
        self.wafer = "UNKNOWN"
        self.die = "UNKNOWN"

        self.is_prepared = 0

        self.upload_files = {
            "qe.0003.fits": "qe_400nm.fits",
            "qe.0005.fits": "qe_500nm.fits",
            "qe.0007.fits": "qe_600nm.fits",
            "qe.0009.fits": "qe_700nm.fits",
            "qe.0011.fits": "qe_800nm.fits",
            "qe.0013.fits": "qe_900nm.fits",
            "qe.0015.fits": "qe_980nm.fits",
            "fe55.0051.fits": "fe55.fits",
            "bias.0001.fits": "bias.fits",
            "superflat.fits": "superflat.fits",
            "dark.0045.fits": "dark.fits",
            "DefectsMask.fits": "defect_mask.fits",
            "LVM_EO_Report*.pdf": "LVM_EO_Report.pdf",
        }

        self.use_fe55_gain = 1

        self.start_temperature = -1000

        self.report_comment = ""

        # report
        self.report_name = ""  # final report base filename
        # names in proper order
        self.report_names = [
            "qe",
            "fe55",
            "linearity",
            "ptc",
            "prnu",
            "gain",
            "defects",
            "dark",
            "bias",
        ]
        # filenames, no extension
        self.report_files = {
            "bias": "bias/bias",
            "gain": "gain/gain",
            "dark": "dark/dark",
            "brightdefects": "dark/brightdefects",
            "darkdefects": "superflat/darkdefects",
            "defects": "defects/defects",
            "fe55": "fe55/fe55",
            "linearity": "linearity/linearity",
            "ptc": "ptc/ptc",
            "prnu": "prnu/prnu",
            "qe": "qe/qe",
        }

    def setup(self, itl_id=""):

        self.itl_id = azcam.utils.prompt("Enter cameras ID", itl_sn)
        self.operator = azcam.utils.prompt("Enter you initals", "mpl")

        # sponsor/report info
        self.customer = "UArizona"
        self.system = "ITL3"

        self.summary_report_name = f"SummaryReport_{self.itl_id}"
        self.report_name = f"90prime4k_{self.itl_id}.pdf"

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
        self.summary_lines.append(f"|ITL ID         |{self.itl_id}|")
        self.summary_lines.append(f"|Type           |STA4850|")
        self.summary_lines.append(f"|System         |{self.system}|")
        self.summary_lines.append(f"|Operator       |{self.operator}|")

        self.is_setup = True

        return

    def acquire(self, SN="prompt"):
        """
        Acquire detector characterization data.
        """

        print("LVM DetChar acquisition sequence")
        print("")

        self.setup_acquire()

        # *************************************************************************
        # wait for temperature
        # *************************************************************************
        if self.start_temperature != -1000:
            while True:
                t = azcam.db.tools["tempcon"].get_temperatures()[0]
                print("Current temperature: %.1f" % t)
                if t <= self.start_temperature + 0.5:
                    break
                else:
                    time.sleep(10)

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

        # *************************************************************************
        # Acquire
        # *************************************************************************

        # prepare for data sequences
        if not self.is_prepared:
            self.prepare()

        # bias sequenece
        try:
            azcam.db.tools["bias"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.db.parameters.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)
        # gain acquire and analyze
        try:
            azcam.db.tools["gain"].find()
        except Exception as e:
            azcam.log(e)
            azcam.db.parameters.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # superflat sequence
        try:
            azcam.db.tools["superflat"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.db.parameters.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # QE sequence
        try:
            azcam.db.tools["qe"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.db.parameters.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # PTC sequence
        try:
            azcam.db.tools["ptc"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.db.parameters.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # Dark sequence
        try:
            azcam.db.tools["dark"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.db.parameters.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # Fe55 sequence
        try:
            azcam.db.tools["fe55"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.db.parameters.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # finish
        azcam.db.parameters.restore_imagepars(impars)
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
            self.setup_acquire()

        # save pars to be changed
        impars = {}
        azcam.db.parameters.save_imagepars(impars)
        currentfolder = azcam.utils.curdir()

        # uniform image sequence numbers
        azcam.db.parameters.set_par("imagesequencenumber", 1)

        # clear device after reset delay
        print("Delaying start for %.0f seconds (to settle)..." % self.start_delay)
        time.sleep(self.start_delay)
        print("Flush detector")
        azcam.db.tools["exposure"].test(0)

        # gain sequence - do this before detcal
        if 0:
            try:
                azcam.db.tools["gain"].find()
            except Exception:
                azcam.db.parameters.restore_imagepars(impars)
                azcam.utils.curdir(currentfolder)
                return

        # detcal sequence - multiple NDs used
        if 0:
            try:
                azcam.db.tools["detcal"].calibrate()
            except Exception:
                azcam.db.parameters.restore_imagepars(impars)
                azcam.utils.curdir(currentfolder)
                return

        self.is_prepared = 1

        return

    def analyze(self):
        """
        Analyze entire sequence of data for LVM.
        """

        self.setup_analyze()

        rootfolder = azcam.utils.curdir()

        # raw bias
        azcam.utils.curdir("bias")
        azcam.db.tools["bias"].analyze()
        azcam.utils.curdir(rootfolder)

        # gain (no masks)
        azcam.utils.curdir("gain")
        azcam.db.tools["gain"].analyze()
        azcam.utils.curdir(rootfolder)

        # Fe-55 (used for gain below) (no masks)
        azcam.utils.curdir("fe55")
        # azcam.db.tools["fe55"].gain_estimate = azcam.db.tools["gain"].system_gain
        azcam.db.tools["fe55"].analyze()
        azcam.utils.curdir(rootfolder)

        # use fe55 gain from now on
        if self.use_fe55_gain:
            azcam.db.tools["gain"].fe55_gain()

        # superflat (no masks)
        azcam.utils.curdir("superflat")
        azcam.db.tools["superflat"].analyze()
        azcam.utils.curdir(rootfolder)

        # PTC (no masks)
        azcam.utils.curdir("ptc")
        azcam.db.tools["ptc"].analyze()
        azcam.utils.curdir(rootfolder)

        # linearity from ptc data (no masks)
        azcam.utils.curdir(azcam.db.tools["ptc"].analysis_folder)
        azcam.db.tools["linearity"].analyze()
        azcam.db.tools["linearity"].copy_data_files()
        azcam.utils.curdir(rootfolder)

        # darks (only edge mask used)
        azcam.utils.curdir("dark")
        azcam.db.tools["dark"].analyze()
        azcam.utils.curdir(rootfolder)

        # defects, defect mask valid after this
        azcam.utils.curdir("dark")
        azcam.db.tools["defects"].analyze_bright_defects()
        azcam.db.tools["defects"].copy_data_files()
        azcam.utils.curdir(rootfolder)

        azcam.utils.curdir("superflat")
        azcam.db.tools["defects"].analyze_dark_defects()
        azcam.db.tools["defects"].copy_data_files()
        azcam.utils.curdir(rootfolder)

        azcam.utils.curdir("defects")
        azcam.db.tools["defects"].analyze()
        azcam.utils.curdir(rootfolder)

        # prnu (full mask used)
        azcam.utils.curdir("qe")
        azcam.db.tools["prnu"].analyze()
        azcam.db.tools["prnu"].copy_data_files()
        azcam.utils.curdir(rootfolder)

        # qe (full mask used)
        azcam.utils.curdir("qe")
        azcam.db.tools["qe"].analyze()
        azcam.utils.curdir(rootfolder)

        # make report
        self.make_summary_report()
        self.make_report()

        print("Analysis sequence finished")

        return

    def read_datafiles(self):
        """
        Read all data files.
        """

        # load tools and read their datafiles if not valid
        for name in self.report_names:
            try:
                datafile = os.path.join(
                    self.report_folder, self.report_files[name] + ".txt"
                )
                print("Reading datafile for tool %s: %s" % (name, datafile))
                azcam.db.tools(name).read_datafile(datafile)
            except Exception as message:
                print("ERROR", name, message)
                continue

        return

    def copy_files(self):
        """
        Find files from self.upload_files and copy them to
        the upload folder with new name.
        Start in report folder.
        """

        itlutils.cleanup_files()

        report_folder = azcam.utils.curdir()
        self.upload_folder = os.path.join(report_folder, "upload")
        if not os.path.exists(self.upload_folder):
            os.mkdir(self.upload_folder)
        azcam.utils.curdir(self.upload_folder)

        for fname in self.upload_files:
            matches = []
            for root, dirnames, filenames in os.walk(report_folder):
                for filename in fnmatch.filter(filenames, fname):
                    matches.append(os.path.join(root, filename))

            for match in matches:
                if match is not None:
                    print("Found: ", match)
                    shutil.copy(
                        match,
                        os.path.join(self.upload_folder, self.upload_files[fname]),
                    )

        azcam.utils.curdir(report_folder)

        return

    def make_upload(self):
        """
        Prepare a dataset for upload by creating a compressed tar file.
        Start in report folder.
        """

        self.copy_files()

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
detchar = PrimeFocus4kDetChar()

# detchar
azcam.console.utils.set_image_roi([[1800, 1900, 1800, 1900], [2042, 2058, 1500, 1800]])

azcam.db.start_temperature = -115.0

system_noise_correction = 4 * [0.7]

# bias
azcam.db.tools["bias"].number_images_acquire = 3
azcam.db.tools["bias"].fit_order = 3

# gain
azcam.db.tools["gain"].number_pairs = 1
azcam.db.tools["gain"].exposure_time = 1.0
azcam.db.tools["gain"].wavelength = 450
azcam.db.tools["gain"].video_processor_gain = 4 * [12.0]
azcam.db.tools["gain"].readnoise_spec = 4.0
azcam.db.tools["gain"].system_noise_correction = []

# fe55
azcam.db.tools["fe55"].number_images_acquire = 1
azcam.db.tools["fe55"].system_noise_correction = []
azcam.db.tools["fe55"].gain_estimate = 4 * [2.6]
azcam.db.tools["fe55"].exposure_time = 30.0
azcam.db.tools["fe55"].neighborhood_size = 5
azcam.db.tools["fe55"].fit_psf = 0
azcam.db.tools["fe55"].threshold = 500
azcam.db.tools["fe55"].spec_sigma = -1
azcam.db.tools["fe55"].hcte_limit = 0.999_990
azcam.db.tools["fe55"].vcte_limit = 0.999_990
azcam.db.tools["fe55"].spec_by_cte = 1
azcam.db.tools["fe55"].overscan_correct = 1
azcam.db.tools["fe55"].pause_each_channel = 0
azcam.db.tools["fe55"].report_include_plots = 1
azcam.db.tools["fe55"].make_plots = ["histogram", "cte"]
azcam.db.tools["fe55"].plot_files = {
    "histogram": "histogram.png",
    "hcte": "hcte.png",
    "vcte": "vcte.png",
}
azcam.db.tools["fe55"].plot_titles = {
    "histogram": "X-Ray Histogram Plot.",
    "hcte": "HCTE Plot.",
    "vcte": "VCTE Plot.",
}
azcam.db.tools["fe55"].plot_order = ["histogram", "hcte", "vcte"]

# superflats
azcam.db.tools["superflat"].exposure_levels = [10000]
azcam.db.tools["superflat"].exposure_times = [
    5.0,
]
azcam.db.tools["superflat"].wavelength = 550
azcam.db.tools["superflat"].number_images_acquire = [
    5,
]
azcam.db.tools["superflat"].overscan_correct = 1  # correct with overscan region
azcam.db.tools["superflat"].zero_correct = 1  # correct including debiased residuals
azcam.db.tools["superflat"].fit_order = 3

# ptc
azcam.db.tools["ptc"].wavelength = 550
azcam.db.tools["ptc"].exposure_times = [
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
azcam.db.tools["ptc"].gain_range = [1.0, 4.0]
azcam.db.tools["ptc"].fit_max = 60000
azcam.db.tools["ptc"].fit_line = 1
azcam.db.tools["ptc"].overscan_correct = 1
azcam.db.tools["ptc"].exposure_levels = []

# linearity
azcam.db.tools["linearity"].use_ptc_data = 1
azcam.db.tools["linearity"].fit_min = 1000.0  # fit (e-) for linearity fit
azcam.db.tools["linearity"].fit_max = 60000.0  # DN
azcam.db.tools["linearity"].fit_all_data = 0
azcam.db.tools["linearity"].max_allowed_linearity = 0.02  # max residual spec
azcam.db.tools["linearity"].plot_specifications = 1
azcam.db.tools["linearity"].plot_limits = [-3, 3]
azcam.db.tools["linearity"].overscan_correct = 0  # normally 1, but ptc already analyzed
azcam.db.tools["linearity"].zero_correct = 0

# dark
azcam.db.tools["dark"].number_images_acquire = 3
azcam.db.tools["dark"].exposure_time = 600.0
azcam.db.tools["dark"].resolution = 0.01  # resolution of histogram
azcam.db.tools["dark"].use_edge_mask = True  # exclude edges in dark calcs
azcam.db.tools["dark"].overscan_correct = 1  # correct with overscan region
azcam.db.tools["dark"].zero_correct = 1  # correct including debiased residuals
azcam.db.tools["dark"].fit_order = 3
azcam.db.tools["dark"].mean_dark_spec = 20.0 / 3600.0  # e/pix/sec
azcam.db.tools["dark"].bright_pixel_reject = (
    10.0 * azcam.db.tools["dark"].mean_dark_spec
)
azcam.db.tools["dark"].dark_fraction = -1  # fraction of pixel less than dark_limit
azcam.db.tools["dark"].dark_limit = -1  # e/pix/hr
azcam.db.tools["dark"].report_dark_per_hour = True  # report DC per hour

# defects
azcam.db.tools["defects"].use_edge_mask = True
azcam.db.tools["defects"].edge_size = 20
azcam.db.tools["defects"].allowable_bad_fraction = 0.002  # % allowed bad pixels
azcam.db.tools["defects"].report_include_plots = 1
azcam.db.tools["defects"].bright_pixel_reject = 5.0  # e/pix/sec
azcam.db.tools["defects"].allowable_bright_pixels = -1
azcam.db.tools["defects"].dark_pixel_reject = 0.80  # from mean
azcam.db.tools["defects"].allowable_dark_pixels = -1

# prnu
azcam.db.tools["prnu"].root_name = "qe."
azcam.db.tools["prnu"].wavelengths = [360, 400, 500, 550, 650, 750]
azcam.db.tools["prnu"].allowable_deviation_from_mean = 0.10
azcam.db.tools["prnu"].use_edge_mask = True  # use mask from defects tool
azcam.db.tools["prnu"].overscan_correct = 1  # flag to overscan correct images
azcam.db.tools["prnu"].zero_correct = 0  # flag to correct with bias residuals

# qe
qe = azcam.db.tools["qe"]
qe.cal_scale = 1.00
qe.global_scale = 1.24
qe.flux_cal_folder = "/data/90prime4k"
qe.use_edge_mask = False
qe.pixel_area = 0.015 * 0.015
qe.plot_limits = [[300.0, 1000.0], [0.0, 100.0]]
qe.overscan_correct = 1
qe.plot_title = "90Prime QE"
qe.qeroi = []
qe.qe_specs = {}
qe.exposure_levels = {}
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

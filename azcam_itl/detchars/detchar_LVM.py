import datetime
import fnmatch
import os
import shutil
import subprocess
import time

from astropy.io import fits as pyfits

import azcam
from azcam_console.tools.testers.detchar import DetChar
from azcam_itl import itlutils


class LVMDetChar(DetChar):
    """
    The DetChar class for acquistion and analysis of STA4850 CCDs for LVM.
    """

    def __init__(self):
        super().__init__()

        self.LVM_2amps = 0
        self.LVM_nearir = 0

        self.SummaryPdfFile = None

        self.report_folder = ""  # top of report folder tree
        self.start_delay = 5  # aquisition starting delay in seconds

        self.author = ""
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
            "darkdefects": "superflat1/darkdefects",
            "defects": "defects/defects",
            "fe55": "fe55/fe55",
            "linearity": "linearity/linearity",
            "ptc": "ptc/ptc",
            "prnu": "prnu/prnu",
            "qe": "qe/qe",
        }

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
        azcam.utils.save_imagepars(impars)

        # *************************************************************************
        # Create and move to a report folder
        # *************************************************************************
        currentfolder, reportfolder = azcam.utils.make_file_folder("report", 1, 1)
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
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # gain acquire and analyze
        try:
            azcam.db.tools["gain"].find()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # superflat sequence
        try:
            azcam.db.tools["superflat"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # QE sequence
        try:
            azcam.db.tools["qe"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # PTC sequence
        try:
            azcam.db.tools["ptc"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # Dark sequence
        try:
            azcam.db.tools["dark"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # Fe55 sequence
        try:
            azcam.db.tools["fe55"].acquire()
        except Exception as e:
            azcam.log(e)
            azcam.utils.restore_imagepars(impars)
            azcam.utils.curdir(currentfolder)

        # finish
        azcam.utils.restore_imagepars(impars)
        azcam.utils.curdir(currentfolder)

        # send email notice
        finishedtime = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
        message = f"Script finished for SN{self.itl_sn} today at {finishedtime}"
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
        azcam.utils.save_imagepars(impars)
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
                azcam.utils.restore_imagepars(impars)
                azcam.utils.curdir(currentfolder)
                return

        # detcal sequence - multiple NDs used
        if 0:
            try:
                azcam.db.tools["detcal"].calibrate()
            except Exception:
                azcam.utils.restore_imagepars(impars)
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

        # superflat1 (no masks)
        azcam.utils.curdir("superflat1")
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

        azcam.utils.curdir("superflat1")
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
        self.report_summary()
        self.report()

        print("Analysis sequence finished")

        return

    def report(self):
        """
        Make detector characterization report.
        Run setup() first.
        """

        if not self.is_setup:
            self.setup_analyze()

        folder = azcam.utils.curdir()
        self.report_folder = folder
        report_name = "%s_ID%s_SN%d.pdf" % (self.report_name, self.itl_id, self.itl_sn)

        print("")
        print("Generating SN%s Report" % self.itl_sn)
        print("")

        # *********************************************
        # Combine PDF report files for each tool
        # *********************************************
        if self.SummaryPdfFile is None:
            rfiles = []
        else:
            rfiles = [self.SummaryPdfFile]
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
            s = report_name
            subprocess.Popen(s, shell=True, cwd=folder, stdout=fnull, stderr=fnull)
            fnull.close()

        return

    def report_summary(self):
        """
        Create a ID and summary report.
        """

        if not self.is_setup:
            self.setup_analyze()

        if len(self.report_comment) == 0:
            self.report_comment = azcam.utils.prompt("Enter report comment")

        # get current date
        self.report_date = datetime.datetime.now().strftime("%b-%d-%Y")

        lines = []

        lines.append("# LVM Detector Characterization Report")
        lines.append("")
        lines.append("|    |    |")
        lines.append("|:---|:---|")
        lines.append("|**Identification**||")
        lines.append(f"|Customer       |{self.customer}|")
        lines.append(f"|ITL System     |LVM|")
        lines.append(f"|ITL ID         |{self.itl_id}|")
        lines.append(f"|ITL SN         |{int(self.itl_sn)}|")
        lines.append(f"|Type           |{self.device_type}|")
        lines.append(f"|Lot            |{self.lot}|")
        lines.append(f"|Wafer          |{self.wafer}|")
        lines.append(f"|Die            |{self.die}|")
        lines.append(f"|Report Date    |{self.report_date}|")
        lines.append(f"|Author         |{self.author}|")
        lines.append(f"|System         |{self.dewar}|")
        lines.append(f"|Comment        |{self.report_comment}|")
        lines.append("")

        # add superflat image
        f1 = os.path.abspath("./superflat1/superflatimage.png")
        s = f"<img src={f1} width=350>"
        lines.append(s)
        lines.append("")
        lines.append("*Superflat Image.*")

        # Make report files
        self.write_report(self.summary_report_file, lines)

        return

    def read_datafiles(self):
        """
        Read all data files.
        """

        # load tools and read their datafiles if not valid
        for name in self.report_names:
            try:
                datafile = os.path.join(self.report_folder, self.report_files[name] + ".txt")
                print("Reading datafile for tool %s: %s" % (name, datafile))
                azcam.db.tools(name).read_datafile(datafile)
            except Exception as message:
                print("ERROR", name, message)
                continue

        return

    def setup_analyze(self, EO=1):
        """
        Set up configuration for analysis.
        Start in the report folder.
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

        itlsn = azcam.utils.prompt("Enter sensor serial number (integer)", sn)
        self.itl_sn = itlsn

        self.summary_report_file = f"SummaryReport_SN{self.itl_sn}"
        self.SummaryPdfFile = f"{self.summary_report_file}.pdf"

        # find first bias image for header info
        azcam.utils.curdir("bias")
        filename = azcam.utils.find_file_in_sequence("bias")[0]
        azcam.utils.curdir("..")

        try:
            bb = pyfits.getheader(filename)["BACKBIAS"]
        except KeyError:
            bb = 0
        self.backside_bias = float(bb)

        # system info
        self.customer = "ARC"
        self.report_name = "LVM_EO_Report"
        self.system = "LVM"
        self.dewar = "ITL2"
        self.author = "Michael Lesser"

        # ****************************************************************
        # Identification
        # ****************************************************************
        self.itl_sn = int(itlsn)
        if self.itl_sn == 0 or self.itl_sn == -1:
            print("WARNING - Unspecified detector serial number")
            self.itl_sn = 0
            self.itl_id = "0"
        else:
            self.lot = azcam.utils.prompt("Enter lot")
            self.device_type = azcam.utils.prompt("Enter device type")
            self.wafer = azcam.utils.prompt("Enter wafer")
            self.die = azcam.utils.prompt("Enter die")
            self.itl_id = azcam.utils.prompt("Enter ITL ID")

        self.is_setup = 1

        return

    def setup_acquire(self):
        """
        Set up configuration for acquisition.
        Used for console and also tries to set server configuration.
        """

        self.backside_bias = 0  # get from header

        # system info
        self.customer = "ARC"
        self.report_name = "LVM_EO_Report"
        self.system = "LVM"
        azcam.db.tools["qe"].plot_title = "STA4850 Quantum Efficiency"
        self.dewar = "ITL2"
        self.author = "Michael Lesser"

        # ****************************************************************
        # Identification
        # ****************************************************************
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
        # self.itl_sn = int(azcam.utils.prompt("Enter ITL serial number"))
        if self.itl_sn in [0, -1]:
            print("WARNING - Unspecified detector serial number")
            self.itl_sn = 0
            self.itl_id = "0"
        else:
            self.lot = azcam.utils.prompt("Enter lot")
            self.device_type = azcam.utils.prompt("Enter device type")
            self.wafer = azcam.utils.prompt("Enter wafer")
            self.die = azcam.utils.prompt("Enter die")
            self.itl_id = azcam.utils.prompt("Enter ITL ID")

        self.is_setup = 1

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
detchar = LVMDetChar()

# optional configuration options
detchar.LVM_2amps = azcam.db.get("LVM_2amps")
detchar.LVM_nearir = azcam.db.get("LVM_nearir")

# detchar
azcam.utils.set_image_roi([[1800, 1900, 1800, 1900], [2042, 2058, 1500, 1800]])

azcam.db.start_temperature = -108.0

test_waves = [360, 400, 500, 550, 650, 750, 850, 950, 980]
system_noise_correction = 4 * [0.7]

# bias
azcam.db.tools["bias"].number_images_acquire = 3
azcam.db.tools["bias"].fit_order = 3

# gain
azcam.db.tools["gain"].number_pairs = 1
azcam.db.tools["gain"].exposure_time = 1.0
if detchar.LVM_nearir:
    azcam.db.tools["gain"].wavelength = 750
else:
    azcam.db.tools["gain"].wavelength = 450
azcam.db.tools["gain"].video_processor_gain = 4 * [12.0]
azcam.db.tools["gain"].readnoise_spec = 4.0
azcam.db.tools["gain"].system_noise_correction = system_noise_correction

# fe55
azcam.db.tools["fe55"].number_images_acquire = 1
azcam.db.tools["fe55"].system_noise_correction = system_noise_correction
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
if detchar.LVM_nearir:
    azcam.db.tools["superflat"].wavelength = 750
else:
    azcam.db.tools["superflat"].wavelength = 550
azcam.db.tools["superflat"].number_images_acquire = [
    5,
]
azcam.db.tools["superflat"].overscan_correct = 1  # correct with overscan region
azcam.db.tools["superflat"].zero_correct = 1  # correct including debiased residuals
azcam.db.tools["superflat"].fit_order = 3

# ptc
if detchar.LVM_nearir:
    azcam.db.tools["ptc"].wavelength = 750
    azcam.db.tools["ptc"].exposure_times = [1, 3, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
else:
    azcam.db.tools["ptc"].wavelength = 550
    azcam.db.tools["ptc"].exposure_times = [1, 2, 3, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
azcam.db.tools["ptc"].gain_range = [1.0, 4.0]
azcam.db.tools["ptc"].fit_max = 60000
azcam.db.tools["ptc"].fit_line = 1
azcam.db.tools["ptc"].overscan_correct = 1
azcam.db.tools["ptc"].exposure_levels = []
# linearity
azcam.db.tools["linearity"].use_ptc_data = 1
azcam.db.tools["linearity"].linearity_fit_min = 1000.0  # fit (e-) for linearity fit
azcam.db.tools["linearity"].linearity_fit_max = 60000.0  # DN
azcam.db.tools["linearity"].fit_all_data = 0
azcam.db.tools["linearity"].max_residual_linearity = 0.02  # max residual spec
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
azcam.db.tools["dark"].bright_pixel_reject = 10.0 * azcam.db.tools["dark"].mean_dark_spec
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
if detchar.LVM_nearir:
    azcam.db.tools["prnu"].wavelengths = [550, 650, 750, 850, 950]
else:
    azcam.db.tools["prnu"].wavelengths = [360, 400, 500, 550, 650, 750]
azcam.db.tools["prnu"].allowable_deviation_from_mean = 0.10
azcam.db.tools["prnu"].use_edge_mask = True  # use mask from defects tool
azcam.db.tools["prnu"].overscan_correct = 1  # flag to overscan correct images
azcam.db.tools["prnu"].zero_correct = 0  # flag to correct with bias residuals

# qe
if detchar.LVM_nearir:
    azcam.db.tools["qe"].cal_scale = 0.96  # 04feb22
else:
    azcam.db.tools["qe"].cal_scale = 1.04

# recalibrate in dewar 08Nov21
azcam.db.tools["qe"].global_scale = 1.0

azcam.db.tools["qe"].diode_cal_folder = "/data/LVM"
azcam.db.tools["qe"].flux_cal_folder = "/data/LVM"
azcam.db.tools["qe"].use_edge_mask = True  # use defects mask
azcam.db.tools["qe"].pixel_area = 0.015 * 0.015
azcam.db.tools["qe"].plot_limits = [[300.0, 1000.0], [0.0, 100.0]]
azcam.db.tools["qe"].overscan_correct = 1
azcam.db.tools["qe"].plot_title = "LVM Blue/Red Sensor QE"
azcam.db.tools["qe"].qeroi = []  # about the area of reference diode
azcam.db.tools["qe"].wavelengths = [
    360,
    400,
    450,
    500,
    550,
    600,
    650,
    700,
    750,
    800,
    850,
    900,
    950,
    980,
    1000,
]
if detchar.LVM_nearir:
    azcam.db.tools["qe"].qe_specs = {
        500: 0.80,
        550: 0.85,
        650: 0.90,
        750: 0.90,
        850: 0.90,
        950: 0.50,
        980: 0.30,
    }
else:
    azcam.db.tools["qe"].qe_specs = {
        360: 0.75,
        400: 0.80,
        500: 0.80,
        550: 0.85,
        650: 0.90,
        750: 0.90,
    }

# exposure times are for 20k electrons (req. is >10,000)
# want high values for Prnu test
azcam.db.tools["qe"].exposure_levels = {}
azcam.db.tools["qe"].window_trans = {
    300: 1.0,
    1000: 1.0,
}
# if no exposure_levels
azcam.db.tools["qe"].exposure_times = {
    360: 10.0,
    400: 5.0,
    450: 5.0,
    500: 5.0,
    550: 4.0,
    600: 5.0,
    650: 8.0,
    700: 8.0,
    750: 20.0,
    800: 20.0,
    850: 30.0,
    900: 20.0,
    950: 25.0,
    980: 30.0,
    1000: 40.0,
}

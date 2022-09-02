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
from azcam_testers.detchar import DetChar
from azcam_itl import itlutils


class VirusDetChar(DetChar):
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

        self.start_temperature = -105.0

        self.timingfiles = [
            os.path.join(azcam.db.datafolder, "VIRUS", "dspcode", "dsptiming", "VIRUS_config0.lod"),
            # os.path.join(azcam.db.datafolder, "VIRUS", "dspcode", "dsptiming", "VIRUS_config1.lod"),
            # os.path.join(azcam.db.datafolder, "VIRUS", "dspcode", "dsptiming_virus2", "VIRUS_config1.lod"),
        ]

    def acquire(self, SN="prompt"):
        """
        Acquire detector characterization data.
        """

        print("Starting VIRUS acquisition sequence")
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

        # send email notice
        finishedtime = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
        message = "Script finished today at: %s" % (finishedtime)
        itlutils.mailto("mlesser@email.arizona.edu", "VIRUS acquire script finished", message)

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
        report_name = f"VIRUS_report_SN{self.itl_sn}.pdf"

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

        lines.append("# VIRUS Detector Characterization Report")
        lines.append("")
        lines.append("|    |    |")
        lines.append("|:---|:---|")
        lines.append("|**Identification**||")
        lines.append(f"|Customer       |Univ. of Texas|")
        lines.append(f"|ITL System     |VIRUS|")
        lines.append(f"|ITL ID         |{self.itl_id}|")
        lines.append(f"|ITL SN         |{int(self.itl_sn)}|")
        lines.append(f"|Type           |STA3600B|")
        lines.append(f"|Lot            |{self.lot}|")
        lines.append(f"|Wafer          |{int(self.wafer):02d}|")
        lines.append(f"|Die            |{int(self.die)}|")
        lines.append(f"|Report Date    |{self.report_date}|")
        lines.append(f"|Author         |{self.filename2}|")
        lines.append(f"|**Operating Conditions**||")
        lines.append(f"|System         |ITL5|")
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
            for filename in fnmatch.filter(filenames, "VIRUS_Report_*.pdf"):
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
            # get ID number in format NNN (package ID)
            try:
                dbinfo = itlutils.get_itldb_info(self.itl_sn)
                self.lot = dbinfo[1]
                self.device_type = dbinfo[2]
                self.wafer = dbinfo[3]
                self.die = dbinfo[4]
                self.itl_id = dbinfo[5]
            except Exception as e:
                azcam.log(e)
                self.lot = 0
                self.device_type = "unknown"
                self.wafer = 0
                self.die = 0
                self.itl_id = "unknown"

        # device serial number
        self.itl_sn = int(itlsn)
        if self.itl_sn == 0 or self.itl_sn == -1:
            print("WARNING! Unspecified detector serial number")
            self.itl_sn = 0
            self.itl_id = "0"
        else:
            # get ID number in format NNN (package ID)
            try:
                dbinfo = itlutils.get_itldb_info(self.itl_sn)
                self.itl_id = "%s".strip() % dbinfo[5]
            except Exception:
                azcam.log("did not get database info")
                self.itl_sn = 0
                self.itl_id = "000"

        # sponsor/report info
        self.customer = "Univ. Texas"
        self.system = "VIRUS"
        qe.plot_title = "STA3600 Quantum Efficiency"
        self.summary_report_file = f"SummaryReport_SN{self.itl_sn}"
        self.report_file = f"VIRUS_Report_SN{self.itl_sn}.pdf"

        # dewar info
        self.dewar = "ITL5"  # VIRUS dewar

        if operator.lower() == "mpl":
            self.filename2 = "Michael Lesser"
        else:
            print("")
            print("Intruder!  Unknown user.")
            self.filename2 = "UNKNOWN"
        print("")

        self.device_type = "STA3600"

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

    def upload(self):
        """
        Upload a file to VIRUS cloud.
        """

        host = "corral.tacc.utexas.edu"
        port = 22

        ftp = ftplib.FTP_TLS()
        ftp.connect(host, port)
        print(ftp.getwelcome())
        print("Logging in using keyring")
        pw = keyring.get_password("corral.tacc.utexas.edu", "mplesser")
        ftp.login("ITL", pw)
        print("FTP login OK")

        # move to remote folder
        ftp.cwd("VIRUS2")
        s = ftp.pwd()
        print("Current FTP folder is", s)
        ftp.cwd(self.remote_upload_folder)
        s = ftp.pwd()
        print("Current FTP folder is", s)
        s = ftp.nlst()
        print("Current FTP folder contents:", s)

        file1_name = os.path.join(self.remote_upload_folder, f"{self.remote_upload_folder}.zip")

        print("Transfering %s" % file1_name)
        with open(file1_name, "rb") as file1:
            ftp.storbinary("STOR %s" % os.path.basename(file1_name), file1)
        print("Finished")

        ftp.quit()

        return


# create instance
detchar = VirusDetChar()

exposure, gain, bias, detcal, superflat, ptc, qe, dark, fe55, defects = azcam.utils.get_tools(
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

# ***********************************************************************************
# parameters
# ***********************************************************************************
azcam.utils.set_image_roi([[500, 1500, 200, 900], [2069, 2078, 100, 500]])

et = {
    350: 1.1,
    370: 1.1,
    400: 0.41,
    500: 0.15,
    600: 0.06,
    700: 0.07,
    800: 0.11,
    900: 0.03,
    1000: 0.03,
}


# detcal
detcal.wavelengths = [
    350,
    370,
    400,
    500,
    600,
    700,
    800,
    900,
    1000,
]
detcal.exposure_times = et
detcal.data_file = os.path.join(azcam.db.datafolder, "detcal_virus_itl5.txt")

# bias
bias.number_images_acquire = 3
bias.number_flushes = 2

# gain
gain.number_pairs = 1  #
gain.exposure_time = 0.05  #
gain.wavelength = 400  #
gain.video_processor_gain = 4 * [7.19 * 0.9]  # uV/DN inc. preamp (6.5 usec, VG=1)

# dark
dark.number_images_acquire = 3
dark.exposure_time = 600.0
dark.dark_fraction = -1  # no spec on individual pixels
# dark.mean_dark_spec = 3.0 / 600.0  # blue e/pixel/sec
dark.mean_dark_spec = 6.0 / 600.0  # red
dark.use_edge_mask = 1
# dark.bright_pixel_reject = 0.05  # e/pix/sec clip
dark.overscan_correct = 1  # flag to overscan correct images
dark.zero_correct = 1  # flag to correct with bias residuals
dark.fit_order = 0

# superflats
superflat.exposure_levels = [30000]  # electrons
superflat.wavelength = 400
superflat.number_images_acquire = [3]

# ptc
ptc.wavelength = 400
ptc.gain_range = [0.75, 1.5]
ptc.overscan_correct = 1
ptc.fit_line = True
ptc.fit_min = 5000
ptc.fit_max = 40000
ptc.exposure_levels = [
    1000,
    2000,
    5000,
    10000,
    15000,
    20000,
    30000,
    40000,
    50000,
    60000,
    70000,
    80000,
    90000,
]
ptc.exposure_times = []

# linearity
azcam.db.tools["linearity"].wavelength = 600
azcam.db.tools["linearity"].use_ptc_data = 1
azcam.db.tools["linearity"].linearity_fit_min = 2000.0
azcam.db.tools["linearity"].linearity_fit_max = 55000.0
azcam.db.tools["linearity"].max_residual_linearity = 0.01
azcam.db.tools["linearity"].plot_specifications = 1
azcam.db.tools["linearity"].plot_limits = [-4.0, +4.0]
azcam.db.tools["linearity"].overscan_correct = 1
azcam.db.tools["linearity"].zero_correct = 0

# QE
qe.cal_scale = 1.337  # VIRUS ITL5
qe.global_scale = 0.9215  # 26mar21
qe.pixel_area = 0.015 * 0.015
qe.diode_area = 613.0  # mm^2
qe.diode_cal_folder = "/data/VIRUS"
qe.flux_cal_folder = "/data/VIRUS"
qe.plot_limits = [[300.0, 1000.0], 0.0, 1.0]
qe.plot_title = "STA3600 Quantum Efficiency"
# qe.qeroi=[100,1900,100,1900]
qe.qeroi = []
qe.wavelengths = [
    350,
    370,
    400,
    500,
    600,
    700,
    800,
    900,
    1000,
]
"""
VIRUS2:
> 75% at 375nm, > 80% at 400 nm, > 85% at 500 nm,
> 80% at 650 nm, > 65% at 850 nm, > 35% at 960nm
"""
qe.qe_specs = {
    350: 0.50,
    375: 0.75,
    400: 0.80,
    500: 0.85,
    650: 0.80,
    850: 0.65,
    960: 0.35,
}
qe.exposure_levels = {
    350: 20000.0,
    370: 20000.0,
    400: 20000.0,
    500: 20000.0,
    600: 20000.0,
    700: 20000.0,
    800: 20000.0,
    900: 20000.0,
    1000: 20000.0,
}
qe.exposure_times = et
qe.window_trans = {
    350: 0.92,
    370: 0.92,
    400: 0.92,
    500: 0.92,
    600: 0.92,
    700: 0.92,
    800: 0.92,
    900: 0.92,
    1000: 0.92,
}

# prnu
azcam.db.tools["prnu"].allowable_deviation_from_mean = 0.1
azcam.db.tools["prnu"].root_name = "qe."
azcam.db.tools["prnu"].use_edge_mask = 1
azcam.db.tools["prnu"].overscan_correct = 1
azcam.db.tools["prnu"].wavelengths = [350, 370, 400, 500, 600, 700, 800, 900, 1000]
azcam.db.tools["prnu"].exposures = et

# fe55
fe55.number_images_acquire = 1
fe55.gain_estimate = [1.0, 1.0]
fe55.system_noise_correction = [1.0, 1.0]
fe55.exposure_time = 60.0
fe55.neighborhood_size = 5
fe55.fit_psf = 0
fe55.threshold = 500
fe55.spec_sigma = -1
fe55.hcte_limit = 0.999_990
fe55.vcte_limit = 0.999_990
fe55.spec_by_cte = 1
fe55.overscan_correct = 1
fe55.zero_correct = 1
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

# defects
azcam.db.tools["defects"].use_edge_mask = 1
azcam.db.tools["defects"].edge_size = 10
azcam.db.tools["defects"].allowable_bad_fraction = 0.002  # % allowed bad pixels
azcam.db.tools["defects"].bright_pixel_reject = 0.5  # e/pix/sec
azcam.db.tools["defects"].dark_pixel_reject = 0.80  # reject pixels below this value from mean

# metrology
#  spec: min >= 11.485, max <= 11.585
azcam.db.tools["metrology"].height_half_band_spec = 0.050
azcam.db.tools["metrology"].height_fraction_limit = 1.0
azcam.db.tools["metrology"].flatness_half_band_spec = 0.010
azcam.db.tools["metrology"].flatness_fraction_limit = 1.0
azcam.db.tools["metrology"].z_nom = 11.535
azcam.db.tools["metrology"].z_spec = []
azcam.db.tools["metrology"].qfh0 = 0  # 100%
azcam.db.tools["metrology"].qfh1 = 10
azcam.db.tools["metrology"].standard_zheight = 13.000
azcam.db.tools["metrology"].create_plots = 1  # debug

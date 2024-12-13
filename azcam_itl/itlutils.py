"""
General purpose code for ITL.
"""

import os
import fnmatch
import shutil
import hashlib
import tarfile
import time

import numpy
import cv2
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import keyring

import azcam
import azcam.utils
import azcam.exceptions
import azcam.image
import azcam_console.console


def cleanup_files(folder=None):
    """
    Cleanup folders after data analysis.
    """

    if folder is None:
        folder = azcam.utils.curdir()

    matches = []
    for root, dirnames, filenames in os.walk(folder):
        for dirname in fnmatch.filter(dirnames, "analysis*"):
            matches.append(os.path.join(root, dirname))

    for t in matches:
        azcam.log(f"Deleting folder {t}")
        shutil.rmtree(t)

    # remove test and temp .FITS files and server/console .log files
    matches = []
    for root, dirnames, filenames in os.walk(folder):
        for filename in fnmatch.filter(filenames, "test.fits"):
            matches.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, "TempDisplayFile.fits"):
            matches.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, "console_*.log"):
            matches.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, "server_*.log"):
            matches.append(os.path.join(root, filename))

    for t in matches:
        azcam.log(f"Deleting file {t}")
        os.remove(t)

    return


def archive(foldername="", filetype="tar"):
    """
    Make a tarfile from a folder or file.
    Type can be "tar", "tar.gz", or "zip".
    Return tarfile filename.
    """

    if foldername == "":
        reply = azcam_console.utils.file_browser(
            "", "folder", "Select folder to archive"
        )
        if reply == []:
            raise azcam.exceptions.AzcamError("no folder or file selected")
        else:
            foldername = reply[0]

    if filetype == "tar.gz":
        filename = foldername + ".tar.gz"
        tar = tarfile.open(filename, "w:gz")
        tar.add(foldername)
        tar.close()

    elif filetype == "tar":
        filename = foldername + ".tar"
        tar = tarfile.open(filename, "w:")
        tar.add(foldername)
        tar.close()

    elif filetype == "zip":
        filename = foldername
        shutil.make_archive(filename, "zip", foldername)
        filename = filename + ".zip"

    else:
        raise azcam.exceptions.AzcamError("unsupported archive file type")

    return filename


def checksum(filename):
    """
    Make a checksum file in the working folder.
    Return filename and checksum value.
    """

    filechecksum = os.path.basename(filename) + ".sha256"

    # make checksum
    hasher = hashlib.sha256()
    with open(filename, "rb") as afile:
        buf = afile.read()
        hasher.update(buf)
    hashstring = hasher.hexdigest()

    with open(filechecksum, "w") as f:
        f.write(hashstring + "\n")

    return filechecksum, hashstring


def count_files(path=""):
    """
    Return the number of files in path (default is current folder).
    Folders are not included.
    """

    # move to path if required
    if path != "":
        cd = azcam.utils.curdir()
        azcam.utils.curdir(path)

    nfiles = len([name for name in os.listdir(".") if os.path.isfile(name)])

    # move back
    if path != "":
        azcam.utils.curdir(cd)

    return nfiles


"""
def _example():
    TO = eval(input("To: "))
    SUBJECT = eval(input("Subject: "))
    BODY = eval(input("Message: "))
    # TO = 'xxx @ xxx.xxx.xxx'
    # SUBJECT = 'test message'
    # BODY = 'This is a test message - is that script done yet?!'

    login()
    mailto(TO, SUBJECT, BODY)

    return
"""


def mailto(to, subject, text, attachments=None):
    gmail_service = "gmail.com"
    gmail_user = "arizona.itl"

    # set pw with keyring.set_password(gmail_service, gmail_user, "my_password")
    gmail_pwd = keyring.get_password(gmail_service, gmail_user)

    msg = MIMEMultipart()

    msg["From"] = f"{gmail_user}"
    msg["To"] = to
    msg["Subject"] = subject

    msg.attach(MIMEText(text))

    if attachments:
        for attach in attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(open(attach, "rb").read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                'attachment; filename="%s"' % os.path.basename(attach),
            )
            msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmail_user, gmail_pwd)
    mailServer.sendmail(gmail_user, to, msg.as_string())
    mailServer.close()

    return


def imsnap(scale: float = 1.0, fits_file: str = "last", snap_file: str = None) -> None:
    """
    Converts FITS image to snapshot file with simple median scaling.

    Args:
        scale (float, optional): sdev scale factor above and below median.
        fits_file (str, optional): name of fits file. "last" means last exposure image.
        snap_file (str, optional): name of snapshot file to write. None means same name as fits_file.
    Globals:
        db.imsnap_interactive (bool): if defined as True then display snapshot interactively
        db.imsnap_resize (float): if defined down image size by this factor

    """

    if fits_file == "last":
        fits_file = azcam.db.parameters.get_par("lastfilename")

    folder = os.path.dirname(fits_file)
    fname = os.path.basename(fits_file)
    if fname.endswith(".fits"):
        fname = fname[:-5]

    if snap_file is None:
        snap_file = f"{fname}"

    if not snap_file.endswith(".png"):
        snap_file = f"{snap_file}.png"

    if not os.path.isabs(snap_file):
        snap_file = os.path.normpath(os.path.join(folder, snap_file))

    loop = 0
    while loop < 50:
        if not os.path.exists(fits_file):
            time.sleep(0.01)
            loop += 1
        else:
            break

    im1 = azcam.image.Image(fits_file)
    im1.assemble(1)  # buffer float32 by default

    data = im1.buffer
    median = numpy.median(data)
    std = data.std()
    z1 = median - std * scale
    z2 = median + std * scale
    z1 = max(0.0, z1)
    z2 = min(z2, 2**16 - 1)

    print(f"Image median scaling: [{z1:.0f}, {z2:.0f}]")

    data = data - z1
    data = numpy.clip(data, 0, (z2 - z1))

    # data = numpy.clip(data, z1, z2)
    # data = (data - median) / std
    # print(median, std)

    data = data * 255.0 / data.max()
    data = data.astype("uint8")

    # open-cv
    resize = azcam.db.get("imsnap_resize")
    if resize:
        newsize = [int(x / float(resize)) for x in data.shape]
        data = cv2.resize(data, (newsize[1], newsize[0]), interpolation=cv2.INTER_AREA)

    data = cv2.flip(data, 0)

    if azcam.db.get("imsnap_interactive"):
        print("Press s to save image snap, c to continue, other close window")
        cv2.imshow("image", data)
        key = cv2.waitKey(0)
        if chr(key) == "s":
            cv2.imwrite(snap_file, data)
            cv2.destroyAllWindows()
        elif chr(key) == "c":
            pass
    else:
        cv2.imwrite(snap_file, data)

    return data

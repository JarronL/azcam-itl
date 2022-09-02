# Adapted from: https://www.pyimagesearch.com/2014/09/15/python-compare-two-images/

# import the necessary packages
# scikit-image package
# from skimage.measure import structural_similarity as ssim

import os
from skimage.measure import compare_ssim as ssim

import azcam
from azcam.tools.image import Image

INTERACTIVE = 0

# STA3600
DIENAME = {
    "X0Y2": "1",
    "X1Y2": "2",
    "X2Y2": "3",
    "X0Y1": "4",
    "X1Y1": "5",
    "X2Y1": "6",
    "X0Y0": "7",
    "X1Y0": "8",
    "X2Y0": "9",
}


def find_id(filename):
    """
    Return wafer, die from filename parsing.
    """

    for position in DIENAME.keys():
        if position in filename:
            diename = DIENAME[position]
            break

    # mod this as needed
    wafer = filename.split("-")[2]
    wafer = int(wafer.split("_")[0])

    return diename, position, wafer


def make_plot(imagename, template1, image1, template2, image2, score, grade):
    """
    Make plots for two configuration devices.
    Currently for VIRUS.
    """

    global INTERACTIVE

    plotfolder = os.path.join(azcam.utils.curdir(), "plots")

    if grade == "PASS":
        color = "green"
    else:
        color = "red"

    # mod this parsing for wafer and die as needed
    name = imagename.split("-")[2]
    name = name.split("\\")[0]
    wafer, die = name.split("_")
    wafer = int(wafer)

    # setup the figure
    fig = azcam.plot.plt.figure(f"W{wafer:02d}-{die}", figsize=(4, 4), dpi=120)
    axes = azcam.plot.plt.gca()
    axes.get_xaxis().set_visible(False)
    axes.get_yaxis().set_visible(False)
    fignum = fig.number
    fig.subplots_adjust(
        left=0.02, bottom=0.02, right=0.98, top=0.92, wspace=0.01, hspace=0.01
    )
    fig.patch.set_facecolor(color)

    diename, position, wafer = find_id(imagename)
    azcam.plot.plt.title(
        f"Die {diename}: {position}: {score[0]:0.02f}: {score[1]:0.02f}"
    )

    # template image on left, targets on right
    # config0 top row, config1 bottom row
    ax = fig.add_subplot(2, 2, 1)
    azcam.plot.plt.imshow(template1, aspect="equal", cmap=azcam.plot.plt.cm.gray)
    ax.axis("off")

    ax = fig.add_subplot(2, 2, 2)
    azcam.plot.plt.imshow(image1, aspect="equal", cmap=azcam.plot.plt.cm.gray)
    ax.axis("off")

    ax = fig.add_subplot(2, 2, 3)
    azcam.plot.plt.imshow(template2, aspect="equal", cmap=azcam.plot.plt.cm.gray)
    ax.axis("off")

    ax = fig.add_subplot(2, 2, 4)
    azcam.plot.plt.imshow(image2, aspect="equal", cmap=azcam.plot.plt.cm.gray)
    ax.axis("off")

    ax.text(
        0.05,
        0.05,
        f"AC {grade}",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=fig.transFigure,
        color=color,
        fontsize=12,
    )

    azcam.plot.plt.savefig(
        os.path.join(plotfolder, f"W{wafer:02d}-{die}" + ".jpg"),
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    if INTERACTIVE:
        azcam.plot.plt.show()

    return


def grade_ac_prober_template(lot):
    """
    Grade AC prober files based on a good tempalte image.
    """

    # **************************************************************************
    # change as needed
    pass_score = 0.43

    # two templates for VIRUS
    basename1 = "itl.OBJECT.0003.fits"
    basename2 = "itl.OBJECT.0103.fits"
    templatename1 = os.path.join(
        r"C:\data\VIRUS\prober\VIRUS\VIRUS_STA3600A-192478-1_X0Y0\report", basename1
    )
    templatename2 = os.path.join(
        r"C:\data\VIRUS\prober\VIRUS\VIRUS_STA3600A-192478-1_X0Y0\report", basename2
    )
    # **************************************************************************

    template1 = Image(templatename1)
    template1.assemble(1)
    template2 = Image(templatename2)
    template2.assemble(1)

    filenames = []
    acdata = []

    # get pairs of images
    for root, directories, files in os.walk("./"):
        for dirname in directories:
            dirname = os.path.abspath(os.path.join(root, dirname))
            f1 = os.path.join(dirname, basename1)
            f2 = os.path.join(dirname, basename2)
            if os.path.exists(f1) and os.path.exists(f2):
                f1 = os.path.normpath(os.path.abspath(f1))
                f2 = os.path.normpath(os.path.abspath(f2))
                filenames.append([f1, f2])

    # make grades
    score = 2 * [0]
    numpass = 0
    numfail = 0
    numfiles = 0

    for image1, image2 in filenames:
        if (basename1 in image1) and (basename2 in image2):
            im1 = Image(image1)
            im1.assemble(1)
            ssim_grade1 = ssim(template1.buffer, im1.buffer)
            score[0] = ssim_grade1

            im2 = Image(image2)
            im2.assemble(1)
            ssim_grade2 = ssim(template2.buffer, im2.buffer)
            score[1] = ssim_grade2
        else:
            raise azcam.AzcamError(f"ERROR bad imagename: {image1}")

        if ssim_grade1 > pass_score and ssim_grade2 > pass_score:
            grade = "PASS"
            numpass += 1
        else:
            grade = "FAIL"
            numfail += 1
        numfiles += 1

        # save data for output file
        diename, position, wafer = find_id(image1)
        acdata.append([int(wafer), int(diename), grade, int(lot), position])

        print(
            f"Image:{image1}, Score:{ssim_grade1:0.3f}-{ssim_grade2:0.3f}, ==>{grade}"
        )

        title = image1
        make_plot(
            title,
            template1.buffer,
            im1.buffer,
            template2.buffer,
            im2.buffer,
            score,
            grade,
        )

        # break

    # sort and write to report file
    acdata.sort()

    # output file header
    ofile = f"Lot{lot}_ac_prober_report"
    with open(ofile + ".txt", "w") as fout:

        # stats
        s = "# Number pass: %d [%4.01f%%]" % (numpass, 100.0 * numpass / numfiles)
        print(s)
        fout.write(s + "\n")
        s = "# Number fail: %d [%4.01f%%]" % (numfail, 100.0 * numfail / numfiles)
        print(s)
        fout.write(s + "\n")
        s = "# Number total: %d" % numfiles
        print(s)
        fout.write(s + "\n")
        fout.write("\n")

        s = "# Wafer  Die    Lot      Position  Grade"
        fout.write(s + "\n")
        for d in acdata:
            if d[2] == "PASS":
                s = "%-5d    %02d %10d %6s %9s <==" % (d[0], d[1], d[3], d[4], d[2])
            else:
                s = "%-5d    %02d %10d %6s %9s" % (d[0], d[1], d[3], d[4], d[2])
            fout.write(s + "\n")

    # write a datafile, use from xxx import acdata to restore
    with open(ofile + ".py", "w") as datafile:
        datafile.write(f"acdata={repr(acdata)}\n")

    # finish
    print("Finished! Variable acdata contains results")

    return acdata


if __name__ == "__main__":
    azcam.utils.curdir("/data/VIRUS/prober/VIRUS")
    acdata = grade_ac_prober_template("192478")

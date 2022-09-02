# script to make prober report from AC and DC report files

import os
import sys

import azcam


def make_prober_report(lot=""):

    if lot == "":
        azcam.AzcamWarning("lot name required")

    dc_data = []
    dc_filename = f"Lot{lot}_dc_prober_report.txt"
    ac_data = []
    ac_filename = f"Lot{lot}_ac_prober_report.txt"

    # open and read DC report file
    with open(dc_filename, "r") as fin:
        if not fin:
            return "ERROR could not open file %s" % dc_filename
        dc_lines = fin.readlines()

    # open and read AC report file
    with open(ac_filename, "r") as fin:
        if not fin:
            return "ERROR could not open file %s" % ac_filename
        ac_lines = fin.readlines()

    # parse data
    dc_tokens = []
    ac_tokens = []
    for line in dc_lines:
        line = line.strip()
        if len(line) == 0:
            continue
        dc_tokens.append(azcam.utils.parse(line))
    for line in ac_lines:
        if len(line) == 0:
            continue
        line = line.strip()
        ac_tokens.append(azcam.utils.parse(line))

    # write output prober file
    with os.path.join(f"./Lot{lot}_prober_report.txt") as ofile:
        outfile = open(ofile, "w")

        s = "%s" % ("# w  w  d  d  position   DC   AC   Final")
        outfile.write(s + "\n")

        # loop through DC tokens
        pcount = 0
        fcount = 0
        count = 0
        for d in dc_tokens:
            if len(d) == 0:
                continue
            if d[0].startswith("#"):
                continue
            try:
                dc_wafer = int(d[0])
                dc_die = int(d[1])
                dc_grade = d[4]
                position = d[3]
            except ValueError:
                continue

            # find match in AC tokens
            for a in ac_tokens:
                # compare DC to AC
                if len(a) == 0:
                    continue
                if a[0].startswith("#"):
                    continue
                try:
                    ac_wafer = int(a[0])
                    ac_die = int(a[1])
                    ac_grade = a[4]
                except ValueError:
                    continue

                if dc_wafer == ac_wafer and dc_die == ac_die:
                    count += 1
                    if dc_grade == "PASS" and ac_grade == "PASS":
                        final_grade = "PASS"
                        pcount += 1
                    elif dc_grade == "FAIL" and ac_grade == "FAIL":
                        final_grade = "FAIL"
                        fcount += 1
                    else:
                        final_grade = ""
                    if final_grade == "FAIL":
                        s = " %02d %02d %02d %02d %9s %s %s => %s" % (
                            dc_wafer,
                            ac_wafer,
                            dc_die,
                            ac_die,
                            position,
                            dc_grade,
                            ac_grade,
                            final_grade,
                        )
                    elif final_grade == "PASS":
                        s = " %02d %02d %02d %02d %9s %s %s ======> %s" % (
                            dc_wafer,
                            ac_wafer,
                            dc_die,
                            ac_die,
                            position,
                            dc_grade,
                            ac_grade,
                            final_grade,
                        )
                    else:
                        s = " %02d %02d %02d %02d %9s %s %s" % (
                            dc_wafer,
                            ac_wafer,
                            dc_die,
                            ac_die,
                            position,
                            dc_grade,
                            ac_grade,
                        )
                    outfile.write(s + "\n")
                    break

        outfile.write("\n")
        s = "PASS: %03d/%03d [%.01f%%], FAIL: %03d/%03d [%.01f%%]" % (
            pcount,
            count,
            (100.0 * pcount / count),
            fcount,
            count,
            (100.0 * fcount / count),
        )
        outfile.write(s + "\n")

    # finished
    return


if __name__ == "__main__":
    args = sys.argv[1:]
    make_prober_report(*args)

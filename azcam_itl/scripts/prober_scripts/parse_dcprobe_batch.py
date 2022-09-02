"""
Run dcprobe parser on a batch of files
"""

import os
import shutil
import sys

from azcam_itl.scripts.prober_scripts.parse_dcprobe_file import parse_dcprobe_file

import azcam


def parse_dcprobe_batch(current_limit=2500.0, short_limit=2.0e6, Verbose=1):
    """
    Parse a batch of ITL prober .dcprobe data files.
    """

    root = azcam.utils.curdir()

    # flag for subfolders
    UseCurrentFolderOnly = 1

    print("Running parse_dcprobe_batch on folder: %s" % root)
    if UseCurrentFolderOnly:
        print("Processing root folder only")

    print()
    key = azcam.utils.prompt("Press q to quit or any other key to continue")
    if key.lower() == "q":
        return

    # make a list of filenames
    filenames = []
    if UseCurrentFolderOnly:
        filenames = [f for f in os.listdir(".") if os.path.isfile(f)]
    else:

        for root, directories, files in os.walk("./"):
            # for directory in directories:
            #    print os.path.join(root, directory)
            for filename in files:
                if not filename.endswith(".dcprobe"):
                    continue
                filename = os.path.join(root, filename)
                filename = os.path.abspath(filename)
                filename = os.path.normpath(filename)
                filenames.append(filename)

    if len(filenames) == 0:
        return "No .dcprobe files found"
    else:
        print("Number .dcprobe files found: %d" % len(filenames))

    for f in filenames:

        if f.endswith(".dcprobe"):
            print(
                "========================================================================="
            )
            reply = parse_dcprobe_file(f, current_limit, short_limit)
            print(f"Parsed {f}")
            if reply.startswith("ERROR"):
                print(f"ERROR parsing {f}: {reply}")
                key = azcam.utils.prompt("Press Enter to continue or q to quit", "")
                if key == "q":
                    return "ERROR parsing %s" % f
            else:
                pass

    # create output folder and move dcparse files
    currentfolder, subfolder = azcam.utils.make_file_folder("dcparsed")
    print("moving .dcparsed files to subfolder: %s" % subfolder)
    parsed_files = os.listdir(currentfolder)
    for f in parsed_files:
        if f.endswith(".dcparsed"):
            shutil.move(f, subfolder)

    return


if __name__ == "__main__":
    args = sys.argv[1:]
    parse_dcprobe_batch(*args)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
PROG_VERSION = "Time-stamp: <2018-04-25 12:26:12 karl.voit>"

import sys
import os
import platform
import subprocess
import codecs

if platform.system() != 'Windows':
    print('This routine is only meant for registering "filetags" to the Send-To-folder in Microsoft Windows.')
    sys.exit(1)

from importlib import import_module


def save_import(library):
    try:
        globals()[library] = import_module(library)
    except ImportError:
        print("Could not find Python module \"" + library +
              "\".\nPlease install it, e.g., with \"sudo pip install " + library + "\".")
        sys.exit(2)


save_import('logging')
save_import('argparse')   # for handling command line arguments

try:
    import win32com.client
except ImportError:
    print("Could not find Python module \"win32com.client\".\nPlease install it, e.g., " +
          "with \"sudo pip install pypiwin32\".")
    sys.exit(3)

PROG_VERSION_DATE = PROG_VERSION[13:23]

DESCRIPTION = "This tool adds \"filetags\" to the Send To folder of the context menu of the Windows File explorer.\n\n"

EPILOG = u"\n\
:copyright: (c) by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:URL: https://github.com/novoid/filetag\n\
:bugreports: via github or <tools@Karl-Voit.at>\n\
:version: " + PROG_VERSION_DATE + "\n·\n"

parser = argparse.ArgumentParser(prog=sys.argv[0],
                                 # keep line breaks in EPILOG and such
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=EPILOG,
                                 description=DESCRIPTION)

parser.add_argument("-a", "--ask",
                    dest="ask_before_close_window", action="store_true",
                    help="Ask the user to press RETURN/ENTER before closing the tagging dialog window")

parser.add_argument("--overwrite",
                    dest="overwrite", action="store_true",
                    help="Do not warn when a previous batch- or lnk-file gets overwritten")

parser.add_argument("-v", "--verbose",
                    dest="verbose", action="store_true",
                    help="enable verbose mode")

parser.add_argument("-q", "--quiet",
                    dest="quiet", action="store_true",
                    help="enable quiet mode")

options = parser.parse_args()


def handle_logging():
    """Log handling and configuration"""

    if options.verbose:
        FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    elif options.quiet:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.ERROR, format=FORMAT)
    else:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.INFO, format=FORMAT)


def error_exit(errorcode, text):
    """exits with return value of errorcode and prints to stderr"""

    sys.stdout.flush()
    logging.error(text)

    sys.exit(errorcode)


def check_for_file_existence_and_warn(filename):
    if os.path.isfile(filename):
        if options.overwrite:
            logging.warn('I am deleting  "' + filename + '" before it gets re-generated.')
            os.remove(filename)
        else:
            error_exit(4, 'The bat file "' + filename +
                       '" already exists (from a prior run?). Please remove file manually and re-run this script.')
    else:
        logging.debug('File ' + filename +
                      ' is not found -> I can continue generating it.')


def main():
    """Main function"""

    handle_logging()

    result = subprocess.run(["where", "filetags"], stdout=subprocess.PIPE)
    # e.g.: b'C:\\Python36\\Scripts\\filetags.exe'
    filetags = result.stdout[:-2]
    filetags_str = result.stdout.decode('ascii').strip()
    logging.debug('filetags was found at: ' + filetags_str)

    home = os.path.expanduser("~")
    batchfile = os.path.join(home, "AppData", "Roaming", "filetags.bat")
    lnkfile = os.path.join(home, "AppData", "Roaming",
                           "Microsoft", "Windows", "SendTo", "filetags.lnk")

    check_for_file_existence_and_warn(batchfile)
    check_for_file_existence_and_warn(lnkfile)

    # create ~\AppData\Roaming\filetags.bat
    logging.debug('writing file ' + batchfile + ' ...')
    with codecs.open(batchfile, 'w', encoding='utf-8') as outputhandle:
        outputhandle.write(filetags_str + " -i %*\n\n")
        if options.ask_before_close_window:
            logging.debug('options.ask_before_close_window is active: let\'s ask the user before closing cmd.exe window')
            outputhandle.write("set /p DUMMY=Hit ENTER to continue...\n\n")
        else:
            logging.debug('options.ask_before_close_window is NOT active: do not ask the user before closing cmd.exe window')
            outputhandle.write("REM set /p DUMMY=Hit ENTER to continue...\n\n")
    logging.debug('file ' + batchfile + ' written')

    # create lnk file to the bat file at: ~\AppData\Roaming\Microsoft\Windows\SendTo
    logging.debug('writing file ' + lnkfile + ' ...')
    shell = win32com.client.Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(lnkfile)
    shortcut.Targetpath = batchfile
    shortcut.WorkingDirectory = os.path.dirname(lnkfile)
    shortcut.save()
    logging.debug('file ' + lnkfile + ' written')

    logging.info('Everything went fine, you can now tag files in Windows Explorer by using the context menu "Send to" with "filetags"')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

# END OF FILE #################################################################

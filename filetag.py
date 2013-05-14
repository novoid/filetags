#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2013-05-14 18:20:58 vk>

## TODO:
## * fix parts marked with «FIXXME»



## ===================================================================== ##
##  You might not want to modify anything below this line if you do not  ##
##  know, what you are doing :-)                                         ##
## ===================================================================== ##

## NOTE: in case of issues, check iCalendar files using: http://icalvalid.cloudapp.net/

import re
import sys
import os
import time
import logging
from optparse import OptionParser

## debugging:   for setting a breakpoint:  pdb.set_trace()
import pdb

PROG_VERSION_NUMBER = u"0.1"
PROG_VERSION_DATE = u"2013-05-09"
INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
FILENAME_TAG_SEPARATOR = u' -- '
BETWEEN_TAG_SEPARATOR = u' '

USAGE = u"\n\
    " + sys.argv[0] + u"\n\
\n\
FIXXME\n\
https://github.com/novoid/FIXXME\n\
\n\
:copyright: (c) 2013 by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:bugreports: <tools@Karl-Voit.at>\n\
:version: " + PROG_VERSION_NUMBER + " from " + PROG_VERSION_DATE + "\n"


## file names containing tags matches following regular expression
FILE_WITH_TAGS_REGEX = re.compile("(.*)" + FILENAME_TAG_SEPARATOR + "(.*)\.(.*)$")
FILE_WITH_TAGS_REGEX_FILENAME_INDEX = 1 ## component.group(1)
FILE_WITH_TAGS_REGEX_TAGLIST_INDEX = 2
FILE_WITH_TAGS_REGEX_EXTENSION_INDEX = 3

FILE_WITH_EXTENSION_REGEX = re.compile("(.*)\.(.*)$")




parser = OptionParser(usage=USAGE)

parser.add_option("-t", "--tag", "--tags", dest="tags",
                  help="one or more tags (separated by spaces) to add/remove")

parser.add_option("-r", "--remove", "-d", "--delete", action="store_true",
                  help="remove tags from (instead of adding to) file name(s)")

parser.add_option("-i", "--interactive", action="store_true",
                  help="interactive mode: ask for (a)dding or (r)emoving and name of tag(s)")

parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="enable verbose mode")

parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  help="enable quiet mode")

parser.add_option("--version", dest="version", action="store_true",
                  help="display version and exit")

(options, args) = parser.parse_args()


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


def contains_tag(filename, tagname=False):
    """
    Returns true if tagname is a tag within filename. If tagname is
    empty, return if filename contains any tag at all.

    @param filename: an unicode string containing a file name
    @param tagname: (optional) an unicode string containing a tag name
    @param return: True|False
    """

    assert filename.__class__ == str or \
        filename.__class__ == unicode
    if tagname:
        assert tagname.__class__ == str or \
            tagname.__class__ == unicode

    components = re.match(FILE_WITH_TAGS_REGEX, filename)

    if not tagname:
        return components!=None
    elif not components:
        logging.debug("file [%s] does not match FILE_WITH_TAGS_REGEX" % filename)
        return False
    else:
        tags = components.group(FILE_WITH_TAGS_REGEX_TAGLIST_INDEX).split(BETWEEN_TAG_SEPARATOR)
        return tagname in tags


def adding_tag_to_filename(filename, tagname):
    """
    Returns string of file name with tagname as additional tag.

    @param filename: an unicode string containing a file name
    @param tagname: an unicode string containing a tag name
    @param return: an unicode string of filename containing tagname
    """

    assert filename.__class__ == str or \
        filename.__class__ == unicode
    assert tagname.__class__ == str or \
        tagname.__class__ == unicode

    if contains_tag(filename) == False:
        logging.debug("adding_tag_to_filename(%s, %s): no tag found so far" % (filename, tagname))

        components = re.match(FILE_WITH_EXTENSION_REGEX, filename)
        old_filename = components.group(1)
        extension = components.group(2)

        return old_filename + FILENAME_TAG_SEPARATOR + tagname + u'.' + extension

    elif contains_tag(filename, tagname):
        logging.debug("adding_tag_to_filename(%s, %s): tag already found in filename" % (filename, tagname))

        return filename

    else:
        logging.debug("adding_tag_to_filename(%s, %s): add as additional tag to existing list of tags" % \
                          (filename, tagname))

        components = re.match(FILE_WITH_EXTENSION_REGEX, filename)
        old_filename = components.group(1)
        extension = components.group(2)

        return old_filename + BETWEEN_TAG_SEPARATOR + tagname + u'.' + extension


def removing_tag_from_filename(filename, tagname):
    """
    Returns string of file name with tagname removed as tag.

    @param filename: an unicode string containing a file name
    @param tagname: an unicode string containing a tag name
    @param return: an unicode string of filename without tagname
    """

    if not contains_tag(filename, tagname):
        return filename

    components = re.match(FILE_WITH_TAGS_REGEX, filename)

    if not components:
        logging.debug("file [%s] does not match FILE_WITH_TAGS_REGEX" % filename)
        return filename
    else:
        tags = components.group(FILE_WITH_TAGS_REGEX_TAGLIST_INDEX).split(BETWEEN_TAG_SEPARATOR)
        old_filename = components.group(FILE_WITH_TAGS_REGEX_FILENAME_INDEX)
        extension = components.group(FILE_WITH_TAGS_REGEX_EXTENSION_INDEX)

        if len(tags) < 2:
            logging.debug("given tagname is the only tag -> remove all tags and FILENAME_TAG_SEPARATOR as well")
            return old_filename + u'.' + extension

        else:
            ## still tags left
            return old_filename + FILENAME_TAG_SEPARATOR + \
                BETWEEN_TAG_SEPARATOR.join([tag for tag in tags if tag != tagname]) + \
                u'.' + extension
    

def query_folder(folder, list_of_files_found):
    """Walk the folder and its sub-folders and collect files matching
    INCLUDE_FILES_REGEX whose folder do not match
    EXCLUDE_FOLDERS_REGEX."""

    ## http://stackoverflow.com/questions/5141437/filtering-os-walk-dirs-and-files

    for root, dirs, files in os.walk(folder):

        # exclude dirs
        dirs[:] = [os.path.join(root, d) for d in dirs]
        dirs[:] = [d for d in dirs if not re.match(EXCLUDE_FOLDERS_REGEX, d)]

        # exclude/include files
        files = [f for f in files if re.match(INCLUDE_FILES_REGEX, f)]
        files = [os.path.join(root, f) for f in files]

        for fname in files:
            list_of_files_found.append(fname)

    return list_of_files_found




def main():
    """Main function"""

    if options.version:
        print os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_NUMBER + \
            " from " + PROG_VERSION_DATE
        sys.exit(0)

    handle_logging()

    if options.verbose and options.quiet:
        error_exit(1, "Options \"--verbose\" and \"--quiet\" found. " +
                   "This does not make any sense, you silly fool :-)")

    if not options.interactive and not options.tags:
        error_exit(2, "No tags are given with option \"--tag\" nor option \"--interactive\" could be found. \n" +
                   "Please specify, at least tag(s) to add/remove or specify interactive mode.")


    ## interactive mode and tags are given
    if options.interactive and options.tags:
        error_exit(3, "I found option \"--tag\" and option \"--interactive\". \n" +
                   "Please choose either tag option OR interactive mode.")

    
    ## interactive mode and remove flag is given (FIXXME: make it possible in future versions)
    if options.interactive and options.remove:
        error_exit(4, "I found option \"--interactive\" and option \"--remove\". \n" +
                   "Please choose either interactive mode OR specify tag(s) to remove together with the \"--tag\" option.")


    ## extract list of tags
    ## FIXXME

    ## extract list of files
    ## FIXXME

    ## iterate over files
    ## FIXXME



    logging.info("successfully finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################

#end

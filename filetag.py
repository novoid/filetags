#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2013-05-16 15:48:33 vk>

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
PROG_VERSION_DATE = u"2013-05-16"
INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
FILENAME_TAG_SEPARATOR = u' -- '
BETWEEN_TAG_SEPARATOR = u' '

USAGE = u"\n\
    " + sys.argv[0] + u" [<options>] <list of files>\n\
\n\
This tool adds or removes simple tags to/from file names.\n\
\n\
Tags within file names are placed between the actual file name and\n\
the file extension, separated with \"" + FILENAME_TAG_SEPARATOR + "\". Multiple tags are\n\
separated with \"" + BETWEEN_TAG_SEPARATOR + "\":\n\
  Update for the Boss" + FILENAME_TAG_SEPARATOR + "projectA" + BETWEEN_TAG_SEPARATOR + "presentation.pptx\n\
  2013-05-16T15.31.42 Error message" + FILENAME_TAG_SEPARATOR + "screenshot" + BETWEEN_TAG_SEPARATOR + "projectB.png\n\
\n\
This easy to use tag system has a drawback: for tagging a larger\n\
set of files with the same tag, you have to rename each file\n\
separately. With this tool, this only requires one step.\n\
\n\
Example usages:\n\
  " + sys.argv[0] + u" --tags=\"presentation projectA\" *.pptx\n\
      ... adds the tags \"presentation\" and \"projectA\" to all PPTX-files\n\
  " + sys.argv[0] + u" -i *\n\
      ... ask for tag(s) and add them to all files in current folder\n\
  " + sys.argv[0] + u" -r draft *report*\n\
      ... removes the tag \"draft\" from all files containing the word \"report\"\n\
\n\
\n\
:copyright: (c) 2013 by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:URL: https://github.com/novoid/filetag\n\
:bugreports: via github or <tools@Karl-Voit.at>\n\
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

parser.add_option("-s", "--dryrun", dest="dryrun", action="store_true",
        help="enable dryrun mode: just simulate what would happen, do not modify files")

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
    

def extract_tags_from_argument(argument):
    """
    @param argument: string containing one or more tags
    @param return: a list of unicode tags
    """

    return argument.split(unicode(BETWEEN_TAG_SEPARATOR))


def extract_filenames_from_argument(argument):
    """
    @param argument: string containing one or more file names
    @param return: a list of unicode file names
    """

    return argument
    

def handle_file(filename, tags, do_remove, dryrun):
    """
    @param filename: list containing one or more file names
    @param tags: list containing one or more tags
    @param do_remove: boolean which defines if tags should be added (False) or removed (True)
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value
    """

    if os.path.isdir(filename):
        logging.warning("Skipping directory \"%s\" because this tool only renames file names." % filename)
        return
    elif not os.path.isfile(filename):
        logging.error("Skipping \"%s\" because this tool only renames existing file names." % filename)
        return

    new_filename = filename
    for tagname in tags:
        if do_remove:
            new_filename = removing_tag_from_filename(new_filename, tagname)
        else:
            new_filename = adding_tag_to_filename(new_filename, tagname)

    if dryrun:
        logging.info("renaming: \"%s\"  >  \"%s\"" % (filename, new_filename))
    else:
        logging.debug("renaming \"%s\"  >  \"%s\" ..." % (filename, new_filename))
        os.rename(filename, new_filename)


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

    tags = []

    if options.interactive:

        if options.remove:
            logging.info("Interactive mode: tags get REMOVED from file names ...")
        else:
            logging.info("Interactive mode: tags get ADDED to file names ...")

        ## interactive: ask for list of tags
        logging.debug("interactive mode: asking for tags ...")

        print "Please enter one or more tags (separated by \"" + BETWEEN_TAG_SEPARATOR + "\"):     (abort with Ctrl-C)"
        entered_tags = sys.stdin.readline().strip()

        tags = extract_tags_from_argument(entered_tags)

        if options.remove:
            logging.info("removing tags \"%s\" ..." % str(BETWEEN_TAG_SEPARATOR.join(tags)))
        else:
            logging.info("adding tags \"%s\" ..." % str(BETWEEN_TAG_SEPARATOR.join(tags)))
            
    else:
        ## non-interactive: extract list of tags
        logging.debug("non-interactive mode: extracting tags from argument ...")

        tags = extract_tags_from_argument(options.tags)

    logging.debug("tags found: [%s]" % '], ['.join(tags))

    logging.debug("extracting list of files ...")
    logging.debug("len(args) [%s]" % str(len(args)))
    if len(args)<1:
        error_exit(5, "Please add at least one file name as argument")
    files = extract_filenames_from_argument(args)
    logging.debug("filenames found: [%s]" % '], ['.join(files))

    logging.debug("iterate over files ...")
    for filename in files:
        handle_file(filename, tags, options.remove, options.dryrun)

    logging.debug("successfully finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################

#end

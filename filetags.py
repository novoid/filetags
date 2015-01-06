#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2015-01-06 13:15:55 vk>

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
import os.path   # for directory traversal to look for .tagfiles
import time
import logging
import operator  # for sorting dicts
import difflib   # for good enough matching words
from sets import Set  # to find out union/intersection of tag sets
import readline  # for raw_input() reading from stdin
import codecs    # for handling Unicode content in .tagfiles
from optparse import OptionParser

PROG_VERSION_NUMBER = u"0.3"
PROG_VERSION_DATE = u"2015-01-02"
INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
FILENAME_TAG_SEPARATOR = u' -- '
BETWEEN_TAG_SEPARATOR = u' '
CONTROLLED_VOCABULARY_FILENAME = ".filetags"

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
This tools is looking for (the first) text file named \".filetags\" in\n\
current and parent directories. Each line of it is interpreted as a tag\n\
for tag completion.\n\
\n\
Verbose description: http://Karl-Voit.at/managing-digital-photographs/\n\
\n\
:copyright: (c) by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:URL: https://github.com/novoid/filetag\n\
:bugreports: via github or <tools@Karl-Voit.at>\n\
:version: " + PROG_VERSION_NUMBER + " from " + PROG_VERSION_DATE + "\n"


## file names containing tags matches following regular expression
FILE_WITH_TAGS_REGEX = re.compile("(.+?)" + FILENAME_TAG_SEPARATOR + "(.+?)(\.(\w+))??$")
FILE_WITH_TAGS_REGEX_FILENAME_INDEX = 1  # component.group(1)
FILE_WITH_TAGS_REGEX_TAGLIST_INDEX = 2
FILE_WITH_TAGS_REGEX_EXTENSION_INDEX = 4

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

parser.add_option("--ln", "--list-tags-by-number", dest="list_tags_by_number", action="store_true",
                  help="list all file-tags sorted by their number of use")

parser.add_option("--la", "--list-tags-by-alphabet", dest="list_tags_by_alphabet", action="store_true",
                  help="list all file-tags sorted by their name")

parser.add_option("--tag-gardening", dest="tag_gardening", action="store_true",
                  help="This is for getting an overview on tags that might require to be renamed (typos, " +
                  "singular/plural, ...). See also http://www.webology.org/2008/v5n3/a58.html")

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


class SimpleCompleter(object):
    ## happily stolen from http://pymotw.com/2/readline/

    def __init__(self, options):
        self.options = sorted(options)
        return

    def complete(self, text, state):
        response = None
        if state == 0:
            # This is the first time for this text, so build a match list.
            if text:
                self.matches = [s
                                for s in self.options
                                if s and s.startswith(text)]
                logging.debug('%s matches: %s', repr(text), self.matches)
            else:
                self.matches = self.options[:]
                logging.debug('(empty input) matches: %s', self.matches)

        # Return the state'th item from the match list,
        # if we have that many.
        try:
            response = self.matches[state]
        except IndexError:
            response = None
        logging.debug('complete(%s, %s) => %s',
                      repr(text), state, repr(response))
        return response


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
        return components is not None
    elif not components:
        logging.debug("file [%s] does not match FILE_WITH_TAGS_REGEX" % filename)
        return False
    else:
        tags = components.group(FILE_WITH_TAGS_REGEX_TAGLIST_INDEX).split(BETWEEN_TAG_SEPARATOR)
        return tagname in tags


def extract_tags_from_filename(filename):
    """
    Returns list of tags contained within filename. If no tag is
    found, return False.

    @param filename: an unicode string containing a file name
    @param return: list of tags
    """

    assert filename.__class__ == str or \
        filename.__class__ == unicode

    components = re.match(FILE_WITH_TAGS_REGEX, filename)

    if not components:
        return []
    else:
        return components.group(FILE_WITH_TAGS_REGEX_TAGLIST_INDEX).split(BETWEEN_TAG_SEPARATOR)


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

    if contains_tag(filename) is False:
        logging.debug("adding_tag_to_filename(%s, %s): no tag found so far" % (filename, tagname))

        components = re.match(FILE_WITH_EXTENSION_REGEX, filename)
        if components:
            old_filename = components.group(1)
            extension = components.group(2)
            return old_filename + FILENAME_TAG_SEPARATOR + tagname + u'.' + extension
        else:
            return filename + FILENAME_TAG_SEPARATOR + tagname

    elif contains_tag(filename, tagname):
        logging.debug("adding_tag_to_filename(%s, %s): tag already found in filename" % (filename, tagname))

        return filename

    else:
        logging.debug("adding_tag_to_filename(%s, %s): add as additional tag to existing list of tags" %
                      (filename, tagname))

        components = re.match(FILE_WITH_EXTENSION_REGEX, filename)
        if components:
            old_filename = components.group(1)
            extension = components.group(2)
            return old_filename + BETWEEN_TAG_SEPARATOR + tagname + u'.' + extension
        else:
            return filename + BETWEEN_TAG_SEPARATOR + tagname


def removing_tag_from_filename(filename, tagname):
    """
    Returns string of file name with tagname removed as tag.

    @param filename: an unicode string containing a file name
    @param tagname: an unicode string containing a tag name
    @param return: an unicode string of filename without tagname
    """

    assert filename.__class__ == str or \
        filename.__class__ == unicode
    assert tagname.__class__ == str or \
        tagname.__class__ == unicode

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

    assert argument.__class__ == str or \
        argument.__class__ == unicode

    if len(argument) > 0:
        return argument.split(unicode(BETWEEN_TAG_SEPARATOR))
    else:
        return False


def extract_filenames_from_argument(argument):
    """
    @param argument: string containing one or more file names
    @param return: a list of unicode file names
    """

    ## FIXXME: works at my computer without need to convertion but add check later on
    return argument


def handle_file(filename, tags, do_remove, dryrun):
    """
    @param filename: string containing one file name
    @param tags: list containing one or more tags
    @param do_remove: boolean which defines if tags should be added (False) or removed (True)
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value
    """

    assert filename.__class__ == str or \
        filename.__class__ == unicode
    assert tags.__class__ == list
    if do_remove:
        assert do_remove.__class__ == bool
    if dryrun:
        assert dryrun.__class__ == bool

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
        logging.info(u" ")
        logging.info(u" renaming \"%s\"" % filename)
        logging.info(u"      ⤷   \"%s\"" % (new_filename))
    else:
        logging.debug(u" renaming \"%s\"" % filename)
        logging.debug(u"      ⤷   \"%s\"" % (new_filename))
        os.rename(filename, new_filename)


def add_tag_to_countdict(tag, tags):
    """
    Takes a tag (string) and a dict. Returns the dict with count value increased by one

    @param tag: a (unicode) string
    @param tags: dict of tags
    @param return: dict of tags with incremented counter of tag (or 0 if new)
    """

    assert tag.__class__ == str or \
        tag.__class__ == unicode
    assert tags.__class__ == dict

    if tag in tags.keys():
        tags[tag] = tags[tag] + 1
    else:
        tags[tag] = 1

    return tags


def get_tags_from_files_and_subfolders():
    """
    Traverses the file system starting with current working directory,
    returns dict of all tags with their number of usage.

    @param return: dict of tags and their number of occurrence
    """

    tags = {}

    cwd = os.getcwdu()
    for root, dirs, files in os.walk(cwd):
        for filename in files:
            for tag in extract_tags_from_filename(filename):
                tags = add_tag_to_countdict(tag, tags)
        for dirname in dirs:
            for tag in extract_tags_from_filename(dirname):
                tags = add_tag_to_countdict(tag, tags)

    return tags


def find_similar_tags(tag, tags):
    """
    Returns a list of entries of tags that are similar to tag (but not same as tag)

    @param tag: a (unicode) string that represents a tag
    @param tags: a list of (unicode) strings
    @param return: list of tags that are similar to tag
    """

    assert tag.__class__ == str or \
        tag.__class__ == unicode
    assert tags.__class__ == list

    similar_tags = difflib.get_close_matches(tag, tags, n=999, cutoff=0.7)
    close_but_not_exact_matches = []

    ## omit exact matches
    for match in similar_tags:
        if match != tag:
            close_but_not_exact_matches.append(match)

    return close_but_not_exact_matches


def list_tags_by_alphabet(only_with_similar_tags=False):
    """
    Traverses the file system, extracts all tags, prints them sorted by alphabet

    @param only_with_similar_tags: if true, print out only tags with similarity to others
    @param return: dict of tags (if only_with_similar_tags, tags without similar ones are omitted)
    """

    tag_dict = get_tags_from_files_and_subfolders()
    if not tag_dict:
        print "\nNo file containing tags found in this folder hierarchy.\n"
        return {}

    ## determine maximum length of strings for formatting:
    maxlength_tags = max(len(s) for s in tag_dict.keys())
    maxlength_count = len(str(abs(max(tag_dict.values()))))
    if maxlength_count < 5:
        maxlength_count = 5

    print("\n  {0:{1}s} : count".format(u'tag', maxlength_tags))
    print "  " + "-" * (maxlength_tags + maxlength_count + 3)

    ## sort dict of (tag, count) according to tag name
    for tuple in sorted(tag_dict.items(), key=operator.itemgetter(0)):

        close_matches = find_similar_tags(tuple[0], tag_dict.keys())
        see_also = u''

        ## if similar names found, format them accordingly for output:
        if len(close_matches) > 0:
            see_also = u'      (similar to:  ' + ', '.join(close_matches) + u')'

        if (only_with_similar_tags and len(close_matches) > 0) or not only_with_similar_tags:
            print "  {0:{1}s} : {2:{3}}{4}".format(tuple[0], maxlength_tags, tuple[1], maxlength_count, see_also)

        if only_with_similar_tags and len(close_matches) == 0:
            ## remove entries from dict for returning only tags with similar tag entries:
            del tag_dict[tuple[0]]

    print ''

    return tag_dict


def list_tags_by_number(max_tag_count=0):
    """
    Traverses the file system, extracts all tags, prints them sorted by tag usage count

    @param max_tag_count: print only tags which occur less or equal to this number (disabled if 0)
    @param return: dict of tags (if max_tag_count is set, returned entries are set accordingly)
    """

    tag_dict = get_tags_from_files_and_subfolders()
    if not tag_dict:
        print "\nNo file containing tags found in this folder hierarchy.\n"
        return {}

    ## determine maximum length of strings for formatting:
    maxlength_tags = max(len(s) for s in tag_dict.keys())
    maxlength_count = len(str(abs(max(tag_dict.values()))))
    if maxlength_count < 5:
        maxlength_count = 5

    print "\n {0:{1}} : {2:{3}}".format(u'count', maxlength_count, u'tag', maxlength_tags)
    print " " + '-' * (maxlength_tags + maxlength_count + 7)
    for tuple in sorted(tag_dict.items(), key=operator.itemgetter(1)):
        ## sort dict of (tag, count) according to count
        if (max_tag_count > 0 and tuple[1] <= max_tag_count) or max_tag_count == 0:
            print " {0:{1}} : {2:{3}}".format(tuple[1], maxlength_count, tuple[0], maxlength_tags)

        if max_tag_count > 0 and tuple[1] > max_tag_count:
            ## remove entries that exceed max_tag_count limit:
            del tag_dict[tuple[0]]
    print ''

    return tag_dict


def handle_tag_gardening():
    """
    This method is quite handy to find tags that might contain typos or do not
    differ much from other tags. You might want to rename them accordinly.

    FIXXME: this is *not* performance optimized since it traverses the file
    system multiple times!

    @param return: -
    """

    tag_dict = get_tags_from_files_and_subfolders()
    if not tag_dict:
        print "\nNo file containing tags found in this folder hierarchy.\n"
        return

    print "\nTags that appear only once are most probably typos or you have forgotten them:"
    tags_by_number = list_tags_by_number(max_tag_count=1)

    print "Tags which have similar other tags are probably typos or plural/singular forms of others:"
    tags_by_alphabet = list_tags_by_alphabet(only_with_similar_tags=True)

    set_by_number = Set(tags_by_number.keys())
    set_by_alphabet = Set(tags_by_alphabet.keys())
    tags_in_both_outputs = set_by_number & set_by_alphabet  # intersection of sets

    if tags_in_both_outputs != Set([]):
        print "If tags appear in both lists from above, they most likely require your attention:"

        ## determine maximum length of strings for formatting:
        maxlength_tags = max(len(s) for s in tags_in_both_outputs)
        maxlength_count = len(str(abs(max(tag_dict.values()))))
        if maxlength_count < 5:
            maxlength_count = 5

        print("\n  {0:{1}s} : count".format(u'tag', maxlength_tags))
        print "  " + "-" * (maxlength_tags + maxlength_count + 3)
        for tag in sorted(tags_in_both_outputs):
            similar_tags = u'      (similar to:  ' + ', '.join(find_similar_tags(tag, tag_dict.keys())) + u')'
            print "  {0:{1}s} : {2:{3}}  {4}".format(tag, maxlength_tags, tags_by_number[tag], maxlength_count, similar_tags)
        print


def locate_file_in_cwd_and_parent_directories(filename):
    """This method looks for the filename in the current folder and its
    parent folders. It returns the file name of the first file name found.

    @param filename: string of file name to look for
    @param return: file name found
    """

    if os.path.isfile(filename):
        logging.debug('found \"%s\" in current working directory' % filename)
        return filename
    else:
        starting_dir = os.getcwdu()
        parent_dir = os.path.abspath(os.path.join(starting_dir, os.pardir))
        logging.debug('looking for \"%s\" in directory \"%s\" ...' % (filename, parent_dir))
        while parent_dir != os.getcwdu():
            os.chdir(parent_dir)
            filename_to_look_for = os.path.abspath(os.path.join(os.getcwdu(), filename))
            if os.path.isfile(filename_to_look_for):
                logging.debug('found \"%s\" in directory \"%s\"' % (filename, parent_dir))
                os.chdir(starting_dir)
                return filename_to_look_for
            parent_dir = os.path.abspath(os.path.join(os.getcwdu(), os.pardir))
        os.chdir(starting_dir)
        logging.debug('did NOT find \"%s\" in current directory or any parent directory')
        return False


def locate_and_parse_controlled_vocabulary():

    """This method is looking for files named
    CONTROLLED_VOCABULARY_FILENAME in the current directory and parses
    it. Each line contains a tag which gets read in for tab
    completion.

    @param return: either False or a list of found tag strings

    """

    filename = locate_file_in_cwd_and_parent_directories(CONTROLLED_VOCABULARY_FILENAME)

    if filename:
      if os.path.isfile(filename):
          tags = []
          with codecs.open(filename, encoding='utf-8') as filehandle:
              for line in filehandle:
                  tags.append(line.strip())
          return tags
      else:
          return False
    else:
        return False


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

    ## interactive mode and tags are given
    if options.interactive and options.tags:
        error_exit(3, "I found option \"--tag\" and option \"--interactive\". \n" +
                   "Please choose either tag option OR interactive mode.")

    if options.list_tags_by_number and options.list_tags_by_alphabet:
        error_exit(6, "Please use only one list-by-option at once.")

    if options.tag_gardening and (options.list_tags_by_number or options.list_tags_by_alphabet or options.tags or options.remove):
        error_exit(7, "Please don't use that gardening option together with any other option.")

    if (options.list_tags_by_alphabet or options.list_tags_by_number) and (options.tags or options.interactive or options.remove):
        error_exit(8, "Please don't use list any option together with add/remove tag options.")

    tags = []

    if options.list_tags_by_alphabet:
        logging.debug("handling option list_tags_by_alphabet")
        list_tags_by_alphabet()

    elif options.list_tags_by_number:
        logging.debug("handling option list_tags_by_number")
        list_tags_by_number()

    elif options.tag_gardening:
        logging.debug("handling option for tag gardening")
        handle_tag_gardening()

    elif options.interactive or not options.tags:

        completionhint = u''

        ## look out for .filetags file and add readline support for tag completion if found with content
        vocabulary = locate_and_parse_controlled_vocabulary()
        if vocabulary:

            assert(vocabulary.__class__ == list)

            # Register our completer function
            readline.set_completer(SimpleCompleter(vocabulary).complete)

            # Use the tab key for completion
            readline.parse_and_bind('tab: complete')

            completionhint = u'; complete %s tags with TAB' % str(len(vocabulary))

        print "                 "
        print "Please enter tags, separated by \"" + BETWEEN_TAG_SEPARATOR + "\"; abort with Ctrl-C" + \
            completionhint
        print "                     "
        print "        ,---------.  "
        print "        |  ?     o | "
        print "        `---------'  "
        print "                     "

        if options.remove:
            logging.info("Interactive mode: tags get REMOVED from file names ...")
        else:
            logging.debug("Interactive mode: tags get ADDED to file names ...")

        ## interactive: ask for list of tags
        logging.debug("interactive mode: asking for tags ...")

        entered_tags = raw_input('Tags: ').strip()

        tags = extract_tags_from_argument(entered_tags)

        if not tags:
            logging.info("no tags given, exiting.")
            sys.stdout.flush()
            sys.exit(0)

        if options.remove:
            logging.info("removing tags \"%s\" ..." % str(BETWEEN_TAG_SEPARATOR.join(tags)))
        else:
            logging.info("adding tags \"%s\" ..." % str(BETWEEN_TAG_SEPARATOR.join(tags)))

    else:
        ## non-interactive: extract list of tags
        logging.debug("non-interactive mode: extracting tags from argument ...")

        tags = extract_tags_from_argument(options.tags)

        if not tags:
            ## FIXXME: check: can this be the case?
            logging.info("no tags given, exiting.")
            sys.stdout.flush()
            sys.exit(0)

    logging.debug("tags found: [%s]" % '], ['.join(tags))

    logging.debug("extracting list of files ...")
    logging.debug("len(args) [%s]" % str(len(args)))
    if len(args) < 1 and not (options.list_tags_by_alphabet or options.list_tags_by_number or options.tag_gardening):
        error_exit(5, "Please add at least one file name as argument")
    else:

        files = extract_filenames_from_argument(args)

        logging.debug("%s filenames found: [%s]" % (str(len(files)), '], ['.join(files)))

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

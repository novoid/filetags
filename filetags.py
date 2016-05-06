#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2016-05-06 10:24:08 vk>

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

PROG_VERSION_NUMBER = u"0.6beta"
PROG_VERSION_DATE = u"2016-01-08"
INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
FILENAME_TAG_SEPARATOR = u' -- '
BETWEEN_TAG_SEPARATOR = u' '
CONTROLLED_VOCABULARY_FILENAME = ".filetags"
HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE = ' *'
UNIQUE_LABELS = [u'labelgray', u'labelgreen', u'labelyellow', u'labelred', u'labelblue']


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
                  help="one or more tags (in quotes, separated by spaces) to add/remove")

parser.add_option("-r", "--remove", "-d", "--delete", action="store_true",
                  help="remove tags from (instead of adding to) file name(s)")

parser.add_option("-i", "--interactive", action="store_true", dest="interactive",
                  help="interactive mode: ask for (a)dding or (r)emoving and name of tag(s)")

parser.add_option("-s", "--dryrun", dest="dryrun", action="store_true",
                  help="enable dryrun mode: just simulate what would happen, do not modify files")

parser.add_option("--ln", "--list-tags-by-number", dest="list_tags_by_number", action="store_true",
                  help="list all file-tags sorted by their number of use")

parser.add_option("--la", "--list-tags-by-alphabet", dest="list_tags_by_alphabet", action="store_true",
                  help="list all file-tags sorted by their name")

parser.add_option("--lu", "--list-tags-unknown-to-vocabulary", dest="list_unknown_tags", action="store_true",
                  help="list all file-tags which are found in file names but are not part of .filetags")

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

    components = re.match(FILE_WITH_TAGS_REGEX, os.path.basename(filename))

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
        logging.debug(u"adding_tag_to_filename(%s, %s): no tag found so far" % (filename, tagname))

        components = re.match(FILE_WITH_EXTENSION_REGEX, os.path.basename(filename))
        if components:
            old_filename = components.group(1)
            extension = components.group(2)
            return os.path.join(os.path.dirname(filename), old_filename + FILENAME_TAG_SEPARATOR + tagname + u'.' + extension)
        else:
            return os.path.join(os.path.dirname(filename), os.path.basename(filename) + FILENAME_TAG_SEPARATOR + tagname)

    elif contains_tag(filename, tagname):
        logging.debug("adding_tag_to_filename(%s, %s): tag already found in filename" % (filename, tagname))

        return filename

    else:
        logging.debug("adding_tag_to_filename(%s, %s): add as additional tag to existing list of tags" %
                      (filename, tagname))

        components = re.match(FILE_WITH_EXTENSION_REGEX, os.path.basename(filename))
        if components:
            old_filename = components.group(1)
            extension = components.group(2)
            return os.path.join(os.path.dirname(filename), old_filename + BETWEEN_TAG_SEPARATOR + tagname + u'.' + extension)
        else:
            return os.path.join(os.path.dirname(filename), filename + BETWEEN_TAG_SEPARATOR + tagname)


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
    @param return: error value or new filename
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
        logging.debug("file type error in folder [%s]: file type: is file? %s  -  is dir? %s  -  is mount? %s" % (os.getcwdu(), str(os.path.isfile(filename)), str(os.path.isdir(filename)), str(os.path.islink(filename))))
        logging.error("Skipping \"%s\" because this tool only renames existing file names." % filename)
        return

    new_filename = filename

    ## if tag within UNIQUE_LABELS found, and new UNIQUE_LABEL is given, remove old label:
    ## e.g.: UNIQUE_LABELS = (u'yes', u'no') -> if 'no' should be added, remove existing label 'yes' (and vice versa)
    ## FIXXME: this is an undocumented feature -> please add proper documentation
    if not do_remove:
        unique_labels_in_old_filename = set(extract_tags_from_filename(filename)).intersection(UNIQUE_LABELS)
        unique_label_to_add = set(tags).intersection(UNIQUE_LABELS)
        if unique_label_to_add and unique_labels_in_old_filename:
            logging.debug("found unique label %s which require old unique label to be removed: %s" % (str(unique_label_to_add), str(unique_labels_in_old_filename)))
            for tagname in unique_labels_in_old_filename:
                new_filename = removing_tag_from_filename(new_filename, tagname)

    for tagname in tags:
        if do_remove:
            new_filename = removing_tag_from_filename(new_filename, tagname)
        else:
            new_filename = adding_tag_to_filename(new_filename, tagname)

    if dryrun:
        logging.info(u" ")
        logging.info(u" renaming \"%s\"" % filename)
        try:
            logging.info(u"      ⤷   \"%s\"" % (new_filename))
        except UnicodeEncodeError:
            logging.info(u"      >   \"%s\"" % (new_filename))
    else:
        if filename != new_filename:
            if not options.quiet:
                try:
                    print u"   %s   →   %s" % (filename, new_filename)
                except UnicodeEncodeError:
                    print u"   %s   >   %s" % (filename, new_filename)
            logging.debug(u" renaming \"%s\"" % filename)
            try:
                logging.debug(u"      ⤷   \"%s\"" % (new_filename))
            except UnicodeEncodeError:
                logging.debug(u"      >   \"%s\"" % (new_filename))
            os.rename(filename, new_filename)

    return new_filename


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


def get_tags_from_files_and_subfolders(startdir=os.getcwdu(), starttags=False, recursive=False):
    """
    Traverses the file system starting with given directory,
    returns dict of all tags (including starttags) of all file

    @param return: dict of tags and their number of occurrence
    """

    assert os.path.isdir(startdir)

    if not starttags:
        tags = {}
    else:
        assert starttags.__class__ == dict
        tags = starttags

    assert not recursive ## FIXXME: not implemented yet

    logging.debug('get_tags_from_files_and_subfolders called with startdir [%s], starttags [%s], recursive[%s]' % (startdir, str(starttags), str(recursive)))
    for root, dirs, files in os.walk(startdir):
        logging.debug('get_tags_from_files_and_subfolders: root [%s]' % root)
        for filename in files:
            for tag in extract_tags_from_filename(filename):
                tags = add_tag_to_countdict(tag, tags)
        for dirname in dirs:
            for tag in extract_tags_from_filename(dirname):
                tags = add_tag_to_countdict(tag, tags)
        break  # do not loop

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

    ## omit exact matches   FIXXME: this can be done in one eloquent line -> refactor
    for match in similar_tags:
        if match != tag:
            close_but_not_exact_matches.append(match)

    return close_but_not_exact_matches


def list_tags_by_alphabet(only_with_similar_tags=False, vocabulary=False):
    """
    Traverses the file system, extracts all tags, prints them sorted by alphabet

    @param only_with_similar_tags: if true, print out only tags with similarity to others
    @param vocabulary: array of tags from controlled vocabulary or False
    @param return: dict of tags (if only_with_similar_tags, tags without similar ones are omitted)
    """

    tag_dict = get_tags_from_files_and_subfolders(startdir=os.getcwdu(), recursive=False)
    if not tag_dict:
        print "\nNo file containing tags found in this folder hierarchy.\n"
        return {}

    ## determine maximum length of strings for formatting:
    maxlength_tags = max(len(s) for s in tag_dict.keys()) + len(HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)
    maxlength_count = len(str(abs(max(tag_dict.values()))))
    if maxlength_count < 5:
        maxlength_count = 5

    hint_for_being_in_vocabulary = ''
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
            if vocabulary and tuple[0] in vocabulary:
                hint_for_being_in_vocabulary = HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
            else:
                hint_for_being_in_vocabulary = ''
            print "  {0:{1}s} : {2:{3}}{4}".format(tuple[0] + hint_for_being_in_vocabulary, maxlength_tags, tuple[1], maxlength_count, see_also)

        if only_with_similar_tags and len(close_matches) == 0:
            ## remove entries from dict for returning only tags with similar tag entries:
            del tag_dict[tuple[0]]

    print ''

    return tag_dict


def list_tags_by_number(max_tag_count=0, vocabulary=False):
    """
    Traverses the file system, extracts all tags, prints them sorted by tag usage count

    @param max_tag_count: print only tags which occur less or equal to this number (disabled if 0)
    @param vocabulary: array of tags from controlled vocabulary or False
    @param return: dict of tags (if max_tag_count is set, returned entries are set accordingly)
    """

    tag_dict = get_tags_from_files_and_subfolders(startdir=os.getcwdu(), recursive=False)
    if not tag_dict:
        print "\nNo file containing tags found in this folder hierarchy.\n"
        return {}

    print_tag_dict(tag_dict, max_tag_count, vocabulary)

    return tag_dict


def print_tag_dict(tag_dict, max_tag_count=0, vocabulary=False):
    """
    Takes a dictionary which holds tag names and their occurrence and prints it to stdout

    @param tag_dict: a dictionary holding tags and their occurrence number
    @param vocabulary: array of tags from controlled vocabulary or False
    @param max_tag_count: print only tags which occur less or equal to this number (disabled if 0)
    """

    ## determine maximum length of strings for formatting:
    maxlength_tags = max(len(s) for s in tag_dict.keys()) + len(HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)
    maxlength_count = len(str(abs(max(tag_dict.values()))))
    if maxlength_count < 5:
        maxlength_count = 5

    hint_for_being_in_vocabulary = ''
    if vocabulary:
        print u"\n  (Tags marked with an asterisk apprear in your vocabulary.)"
    print "\n {0:{1}} : {2:{3}}".format(u'count', maxlength_count, u'tag', maxlength_tags)
    print " " + '-' * (maxlength_tags + maxlength_count + 7)
    for tuple in sorted(tag_dict.items(), key=operator.itemgetter(1)):
        ## sort dict of (tag, count) according to count
        if (max_tag_count > 0 and tuple[1] <= max_tag_count) or max_tag_count == 0:
            if vocabulary and tuple[0] in vocabulary:
                hint_for_being_in_vocabulary = HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
            else:
                hint_for_being_in_vocabulary = ''
            print " {0:{1}} : {2:{3}}".format(tuple[1], maxlength_count, tuple[0] + hint_for_being_in_vocabulary, maxlength_tags)

        if max_tag_count > 0 and tuple[1] > max_tag_count:
            ## remove entries that exceed max_tag_count limit:
            del tag_dict[tuple[0]]
    print ''


def list_unknown_tags():
    """
    Traverses the file system, extracts all tags, prints tags that are found in file names which are not found in the controlled vocabulary file .filetags

    @param return: dict of tags (if max_tag_count is set, returned entries are set accordingly)
    """

    file_tag_dict = get_tags_from_files_and_subfolders(startdir=os.getcwdu(), recursive=False)
    if not file_tag_dict:
        print "\nNo file containing tags found in this folder hierarchy.\n"
        return {}

    vocabulary = locate_and_parse_controlled_vocabulary(False)

    ## filter out known tags from tag_dict
    tag_dict = {}
    for entry in file_tag_dict:
        if entry not in vocabulary:
            tag_dict[entry] = file_tag_dict[entry]

    if len(tag_dict) == 0:
        print "\n  " + str(len(file_tag_dict)) + " different tags were found in file names which are all" + \
        " part of your .filetags vocabulary (consisting of " + str(len(vocabulary)) + " tags).\n"
    else:
        print_tag_dict(tag_dict, vocabulary)

    return tag_dict


def handle_tag_gardening(vocabulary):
    """
    This method is quite handy to find tags that might contain typos or do not
    differ much from other tags. You might want to rename them accordinly.

    FIXXME: this is *not* performance optimized since it traverses the file
    system multiple times!

    @param vocabulary: array containing the controlled vocabulary (or False)
    @param return: -
    """

    tag_dict = get_tags_from_files_and_subfolders(startdir=os.getcwdu(), recursive=False)
    if not tag_dict:
        print "\nNo file containing tags found in this folder hierarchy.\n"
        return

    print "\nTags that appear only once are most probably typos or you have forgotten them:"
    tags_by_number = list_tags_by_number(max_tag_count=1, vocabulary=vocabulary)

    print "Tags which have similar other tags are probably typos or plural/singular forms of others:"
    tags_by_alphabet = list_tags_by_alphabet(only_with_similar_tags=True, vocabulary=vocabulary)

    set_by_number = Set(tags_by_number.keys())
    set_by_alphabet = Set(tags_by_alphabet.keys())
    tags_in_both_outputs = set_by_number & set_by_alphabet  # intersection of sets
    hint_for_being_in_vocabulary = ''

    if tags_in_both_outputs != Set([]):
        print "If tags appear in both lists from above, they most likely require your attention:"

        ## determine maximum length of strings for formatting:
        maxlength_tags = max(len(s) for s in tags_in_both_outputs) + len(HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)
        maxlength_count = len(str(abs(max(tag_dict.values()))))
        if maxlength_count < 5:
            maxlength_count = 5

        print("\n  {0:{1}s} : count".format(u'tag', maxlength_tags))
        print "  " + "-" * (maxlength_tags + maxlength_count + 3)
        for tag in sorted(tags_in_both_outputs):
            if vocabulary and tag in vocabulary:
                hint_for_being_in_vocabulary = HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
            else:
                hint_for_being_in_vocabulary = ''

            similar_tags = u'      (similar to:  ' + ', '.join(find_similar_tags(tag, tag_dict.keys())) + u')'
            print "  {0:{1}} : {2:{3}}  {4}".format(tag + hint_for_being_in_vocabulary, maxlength_tags, tags_by_number[tag], maxlength_count, similar_tags)
        print


def locate_file_in_cwd_and_parent_directories(startfile, filename):
    """This method looks for the filename in the folder of startfile and its
    parent folders. It returns the file name of the first file name found.

    @param startfile: file whose path is the starting point; if False, the working path is taken
    @param filename: string of file name to look for
    @param return: file name found
    """

    if startfile and os.path.isfile(startfile) and os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(startfile)), filename)):
        logging.debug('found \"%s\" in directory of \"%s\" ..' % (filename, startfile))
        return filename
    elif startfile and os.path.isdir(startfile) and os.path.isfile(os.path.join(startfile, filename)):
        logging.debug('found \"%s\" in directory \"%s\" ...' % (filename, startfile))
        return filename
    else:
        if os.path.isfile(startfile):
            starting_dir = os.path.dirname(os.path.abspath(startfile))
            logging.debug('startfile [%s] found, using it as starting_dir [%s] ....' % (str(startfile), starting_dir))
        elif os.path.isdir(startfile):
            starting_dir = startfile
            logging.debug('startfile [%s] is a directory, using it as starting_dir [%s] .....' % (str(startfile), starting_dir))
        else:
            starting_dir = os.getcwdu()
            logging.debug('no startfile found; using cwd as starting_dir [%s] ......' % (starting_dir))
        parent_dir = os.path.abspath(os.path.join(starting_dir, os.pardir))
        logging.debug('looking for \"%s\" in directory \"%s\" .......' % (filename, parent_dir))
        while parent_dir != os.getcwdu():
            os.chdir(parent_dir)
            filename_to_look_for = os.path.abspath(os.path.join(os.getcwdu(), filename))
            if os.path.isfile(filename_to_look_for):
                logging.debug('found \"%s\" in directory \"%s\" ........' % (filename, parent_dir))
                os.chdir(starting_dir)
                return filename_to_look_for
            parent_dir = os.path.abspath(os.path.join(os.getcwdu(), os.pardir))
        os.chdir(starting_dir)
        logging.debug('did NOT find \"%s\" in current directory or any parent directory' % filename)
        return False


def locate_and_parse_controlled_vocabulary(startfile):

    """This method is looking for files named
    CONTROLLED_VOCABULARY_FILENAME in the directory of startfile and parses
    it. Each line contains a tag which gets read in for tab
    completion.

    @param startfile: file whose location is the starting point of the search
    @param return: either False or a list of found tag strings

    """

    filename = locate_file_in_cwd_and_parent_directories(startfile, CONTROLLED_VOCABULARY_FILENAME)

    if filename:
        if os.path.isfile(filename):
            logging.debug('locate_and_parse_controlled_vocabulary: found controlled vocabulary in folder of startfile')
            tags = []
            with codecs.open(filename, encoding='utf-8') as filehandle:
                logging.debug('locate_and_parse_controlled_vocabulary: reading controlled vocabulary in [%s]' % filename)
                for line in filehandle:
                    tags.append(line.strip())
            logging.debug('locate_and_parse_controlled_vocabulary: controlled vocabulary has %i tags' % len(tags))
            return tags
        else:
            logging.debug('locate_and_parse_controlled_vocabulary: could not find controlled vocabulary in folder of startfile')
            return []
    else:
        logging.debug('locate_and_parse_controlled_vocabulary: could not derive filename for controlled vocabulary in folder of startfile')
        return []


def print_tag_shortcut_with_numbers(tag_list, tags_get_added=True):
    """A list of tags from the list are printed to stdout. Each tag
    gets a number associated which corresponds to the position in the
    list (although starting with 1).

    @param tag_list: list of string holding the tags
    @param tags_get_added: True if tags get added, False otherwise
    @param return: -
    """

    if tags_get_added:
        if len(tag_list) < 9:
            hint_string = u"Previously used tags in this directory:"
        else:
            hint_string = u"Top nine previously used tags in this directory:"
    else:
        if len(tag_list) < 9:
            hint_string = u"Possible tags to be removed:"
        else:
            hint_string = u"Top nine possible tags to be removed:"
    print "\n  " + hint_string

    count = 1
    list_of_tag_hints = []
    for tag in tag_list:
        list_of_tag_hints.append(tag + ' (' + str(count) + ')')
        count += 1
    print u'    ' + u' ⋅ '.join(list_of_tag_hints)
    print u'' ## newline at end


def check_for_possible_shortcuts_in_entered_tags(tags, list_of_shortcut_tags):
    """
    Returns tags if the only tag is not a shortcut (entered as integer).
    Returns a list of corresponding tags if it's an integer.

    @param tags: list of entered tags from the user, e.g., [u'23']
    @param list_of_shortcut_tags: list of possible shortcut tags, e.g., [u'bar', u'folder1', u'baz']
    @param return: list of tags which were meant by the user, e.g., [u'bar', u'baz']
    """

    assert tags.__class__ == list
    assert list_of_shortcut_tags.__class__ == list

    potential_shortcut_string = tags
    tags = []
    try:
        shortcut_index = int(potential_shortcut_string[0])
        logging.debug('single entered tag is an integer; stepping through the integers')
        for character in list(potential_shortcut_string[0]):
            logging.debug('adding tag number %s' % character)
            try:
                tags.append(list_of_shortcut_tags[int(character)-1])
            except IndexError:
                return potential_shortcut_string
    except ValueError:
        logging.debug('single entered tag is a normal tag')
        tags = potential_shortcut_string

    return tags


def get_upto_nine_keys_of_dict_with_highest_value(mydict):
    """
    Takes a dict, sorts it according to their values, and returns up to nine
    values with the highest values.

    Example1: { "key2":45, "key1": 33} -> [ "key1", "key2" ]

    @param mydict: dictionary holding keys and values
    @param return: list of up to top nine keys according to the rank of their values
    """

    assert mydict.__class__ == dict

    complete_list = sorted(mydict, key=mydict.get, reverse=True)
    return sorted(complete_list[:9])


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

    logging.debug("extracting list of files ...")
    logging.debug("len(args) [%s]" % str(len(args)))

    files = extract_filenames_from_argument(args)

    logging.debug("%s filenames found: [%s]" % (str(len(files)), '], ['.join(files)))

    tags_from_userinput = []
    vocabulary = locate_and_parse_controlled_vocabulary(os.getcwdu())
    logging.debug('finished locating of controlled vocabulary')

    if len(args) < 1 and not (options.list_tags_by_alphabet or options.list_tags_by_number or options.list_unknown_tags or options.tag_gardening):
        error_exit(5, "Please add at least one file name as argument")

    if options.list_tags_by_alphabet:
        logging.debug("handling option list_tags_by_alphabet")
        list_tags_by_alphabet()

    elif options.list_tags_by_number:
        logging.debug("handling option list_tags_by_number")
        list_tags_by_number()

    elif options.list_unknown_tags:
        logging.debug("handling option list_unknown_tags")
        list_unknown_tags()

    elif options.tag_gardening:
        logging.debug("handling option for tag gardening")
        handle_tag_gardening(vocabulary)

    elif options.interactive or not options.tags:

        completionhint = u''

        if len(args) < 1:
            error_exit(5, "Please add at least one file name as argument")

        tags_from_filenames_of_arguments_dict = {}
        upto9_tags_from_filenames_of_same_dir_list = []

        ## look out for .filetags file and add readline support for tag completion if found with content
        if options.remove:
            ## vocabulary for completing tags is current tags of files
            for file in files:
                ## add tags so that list contains all unique tags:
                for newtag in extract_tags_from_filename(file):
                    add_tag_to_countdict(newtag, tags_from_filenames_of_arguments_dict)

            logging.debug('generating vocabulary ...')
            vocabulary = sorted(tags_from_filenames_of_arguments_dict.keys())
            upto9_tags_from_filenames_of_arguments_list = sorted(get_upto_nine_keys_of_dict_with_highest_value(tags_from_filenames_of_arguments_dict))
        else:
            if files:

                logging.debug('deriving upto9_tags_from_filenames_of_same_dir_list ...')
                upto9_tags_from_filenames_of_same_dir_list = sorted(get_upto_nine_keys_of_dict_with_highest_value(get_tags_from_files_and_subfolders(startdir=os.path.dirname(os.path.abspath(files[0])))))
                logging.debug('derived upto9_tags_from_filenames_of_same_dir_list')
            vocabulary = sorted(locate_and_parse_controlled_vocabulary(args[0]))
            logging.debug('derived vocabulary with %i entries' % len(vocabulary))

        if vocabulary and len(vocabulary) > 0:

            assert(vocabulary.__class__ == list)

            # Register our completer function
            readline.set_completer(SimpleCompleter(vocabulary).complete)

            # Use the tab key for completion
            readline.parse_and_bind('tab: complete')

            completionhint = u'; complete %s tags with TAB' % str(len(vocabulary))

        logging.debug("len(args) [%s]" % str(len(args)))
        logging.debug("args %s" % str(args))

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
            if len(upto9_tags_from_filenames_of_arguments_list) > 0:
                print_tag_shortcut_with_numbers(upto9_tags_from_filenames_of_arguments_list, tags_get_added=False)
        else:
            logging.debug("Interactive mode: tags get ADDED to file names ...")
            if upto9_tags_from_filenames_of_same_dir_list:
                print_tag_shortcut_with_numbers(upto9_tags_from_filenames_of_same_dir_list, tags_get_added=True)


        ## interactive: ask for list of tags
        logging.debug("interactive mode: asking for tags ...")

        entered_tags = raw_input('Tags: ').strip()

        tags_from_userinput = extract_tags_from_argument(entered_tags)

        if not tags_from_userinput:
            logging.info("no tags given, exiting.")
            sys.stdout.flush()
            sys.exit(0)

        if options.remove:
            if len(tags_from_userinput) == 1 and len(upto9_tags_from_filenames_of_arguments_list) > 0:
                ## check if user entered number shortcuts for tags to be removed:
                tags_from_userinput = check_for_possible_shortcuts_in_entered_tags(tags_from_userinput, upto9_tags_from_filenames_of_arguments_list)

            logging.info("removing tags \"%s\" ..." % str(BETWEEN_TAG_SEPARATOR.join(tags_from_userinput)))
        else:
            if len(tags_from_userinput) == 1 and upto9_tags_from_filenames_of_same_dir_list:
                ## check if user entered number shortcuts for tags to be removed:
                tags_from_userinput = check_for_possible_shortcuts_in_entered_tags(tags_from_userinput, upto9_tags_from_filenames_of_same_dir_list)
            logging.info("adding tags \"%s\" ..." % str(BETWEEN_TAG_SEPARATOR.join(tags_from_userinput)))

    else:
        ## non-interactive: extract list of tags
        logging.debug("non-interactive mode: extracting tags from argument ...")

        tags_from_userinput = extract_tags_from_argument(options.tags)

        if not tags_from_userinput:
            ## FIXXME: check: can this be the case?
            logging.info("no tags given, exiting.")
            sys.stdout.flush()
            sys.exit(0)

    logging.debug("tags found: [%s]" % '], ['.join(tags_from_userinput))

    logging.debug("iterate over files ...")
    for filename in files:
        if filename.__class__ == str:
            filename = unicode(filename, "UTF-8")
        handle_file(filename, tags_from_userinput, options.remove, options.dryrun)

    logging.debug("successfully finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################

#end

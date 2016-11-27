#!/usr/bin/env python
# -*- coding: utf-8 -*-
PROG_VERSION = u"Time-stamp: <2016-11-27 12:21:13 vk>"

## TODO:
## - fix parts marked with «FIXXME»
## - error handling if dependency libraries are not installed/found
## - $HOME/.config/ with default options (e.g., geeqie)
##   - using clint/resource
##   - if not found, write default config with defaults (and comments)
## - move from optparse to argparse
## - tagfilter: --copy :: copy files instead of creating symlinks
## - tagfilter: all toggle-cmd line args as special tags: --copy and so forth
##   - e.g., when user enters tag "--copy" when interactively reading tags, handle it like options.copy
##   - overwriting cmd-line arguments (if contradictory)
##   - allow combination of cmd-line tags and interactive tags
##     - they get combined
## - tagfilter: additional parameter to move matching files to a temporary subfolder
##   - renaming/deleting of symlinks does not modify original files
## - tagfilter: --recursive :: recursively going into subdirectories and
##      collecting items (into one target directory) for:
##   - adding tags
##   - removing tags
##   - filter
## - tagfilter: --notag :: do not ask for tags, use all items that got no tag
##      at all
## - tagfilter: --ignoredirs :: do not symlink/copy directories
## - tagfilter: --emptytmpdir :: empty temporary directory after the image viewer exits
## - use "open" to open first(?) file


## ===================================================================== ##
##  You might not want to modify anything below this line if you do not  ##
##  know, what you are doing :-)                                         ##
## ===================================================================== ##

import importlib


def save_import(library):
    try:
        globals()[library] = importlib.import_module(library)
    except ImportError:
        print "Could not find Python module \"" + library + "\".\nPlease install it, e.g., with \"sudo pip install " + library + "\"."
        sys.exit(2)

import re
import sys
import os
save_import('optparse')  # for handling command line arguments
save_import('time')
save_import('logging')
save_import('operator')  # for sorting dicts
save_import('difflib')   # for good enough matching words
save_import('readline')  # for raw_input() reading from stdin
save_import('codecs')    # for handling Unicode content in .tagfiles
save_import('math')      # (integer) calculations
save_import('clint')     # for config file handling

PROG_VERSION_DATE = PROG_VERSION[13:23]
INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
FILENAME_TAG_SEPARATOR = u' -- '
BETWEEN_TAG_SEPARATOR = u' '
CONTROLLED_VOCABULARY_FILENAME = ".filetags"
HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE = ' *'
TAGFILTER_DIRECTORY = os.path.join(os.path.expanduser("~"), ".filetags_tagfilter")
DEFAULT_IMAGE_VIEWER_LINUX = 'geeqie'

try:
    TTY_HEIGHT, TTY_WIDTH = [int(x) for x in os.popen('stty size', 'r').read().split()]
except ValueError:
    TTY_HEIGHT, TTY_WIDTH = 80, 80

max_file_length = 0  # will be set after iterating over source files182

unique_tags = [[u'teststring1', u'teststring2']]  # list of list which contains tags that are mutually exclusive
## Note: u'teststring1' and u'teststring2' are hard-coded for testing purposes.
##       You might delete them if you don't use my unit test suite.


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
:version: " + PROG_VERSION_DATE + "\n"


## file names containing tags matches following regular expression
FILE_WITH_TAGS_REGEX = re.compile("(.+?)" + FILENAME_TAG_SEPARATOR + "(.+?)(\.(\w+))??$")
FILE_WITH_TAGS_REGEX_FILENAME_INDEX = 1  # component.group(1)
FILE_WITH_TAGS_REGEX_TAGLIST_INDEX = 2
FILE_WITH_TAGS_REGEX_EXTENSION_INDEX = 4

FILE_WITH_EXTENSION_REGEX = re.compile("(.*)\.(.*)$")
FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX = 1
FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX = 2

cache_of_tags_by_folder = {}
controlled_vocabulary_filename = u''

parser = optparse.OptionParser(usage=USAGE)

parser.add_option("-t", "--tag", "--tags", dest="tags",
                  help="one or more tags (in quotes, separated by spaces) to add/remove")

parser.add_option("-r", "--remove", "-d", "--delete", action="store_true",
                  help="remove tags from (instead of adding to) file name(s)")

parser.add_option("-f", "--filter", dest="tagfilter", action="store_true",
                  help="filter out all items that contain all given tags")

parser.add_option("--imageviewer", dest="imageviewer",
                  help="command to view images (for --filter; default: geeqie)")

parser.add_option("-i", "--interactive", action="store_true", dest="interactive",
                  help="interactive mode: ask for (a)dding or (r)emoving and name of tag(s)")

parser.add_option("--recursive", dest="recursive", action="store_true",
                  help="recursively go through the current directory and all of its subdirectories (for tag-gardening only)")

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
            old_filename = components.group(FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX)
            extension = components.group(FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX)
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
            old_filename = components.group(FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX)
            extension = components.group(FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX)
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
        if not extension:
            extension = u''
        else:
            extension = u'.' + extension

        if len(tags) < 2:
            logging.debug("given tagname is the only tag -> remove all tags and FILENAME_TAG_SEPARATOR as well")
            return old_filename + extension
        else:
            ## still tags left
            return old_filename + FILENAME_TAG_SEPARATOR + \
                BETWEEN_TAG_SEPARATOR.join([tag for tag in tags if tag != tagname]) + extension


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


def get_unique_tags_from_filename(filename):
    """
    Extracts tags that occur in the array of arrays "unique_tags".

    @param filename: string containing one file name
    @param return: list of found tags
    """

    filetags = extract_tags_from_filename(filename)
    result = []
    for tag in filetags:
        for taggroup in unique_tags:
            if tag in taggroup:
                result.append(tag)
    return result


def item_contained_in_list_of_lists(item, list_of_lists):
    """
    Returns true if item is member of at least one list in list_of_lists.

    @param item: item too look for in list_of_lists
    @param list_of_lists: list containing a list of items
    @param return: (item, list) or None
    """

    for current_list in list_of_lists:
        if item in current_list:
            return item, current_list
    return None, None


def print_item_transition(source, destination, transition):
    """
    Returns true if item is member of at least one list in list_of_lists.

    @param source: string of item before transition
    @param destination: string of item after transition or target
    @param transision: string which determines type of transision: ("add", "delete", "link")
    @param return: N/A
    """

    transition_description = u''
    if transition == 'add':
        transition_description = u'renaming'
    elif transition == 'delete':
        transition_description = u'renaming'
    elif transition == 'link':
        transition_description = u'linking'
    else:
        print "ERROR: print_item_transition(): unknown transition parameter: \"" + transition + "\""

    if 15 + len(transition_description) + (2 * max_file_length) < TTY_WIDTH:
        ## probably enough space: screen output with one item per line

        source_width = max_file_length

        try:
            arrow_left = u'――'
            arrow_right = u'―→'
            print u"  {0:<{width}s}   {1:s}{2:s}{3:s}   {4:s}".format(source, arrow_left, transition_description, arrow_right, destination, width=source_width)
        except UnicodeEncodeError:
            arrow_left = u'--'
            arrow_right = u'->'
            print u"  {0:<{width}s}   {1:s}{2:s}{3:s}   {4:s}".format(source, arrow_left, transition_description, arrow_right, destination, width=source_width)

    else:
        ## for narrow screens (and long file names): split up item source/destination in two lines

        print u" {0:<{width}s}  \"{1:s}\"".format(transition_description, source, width=len(transition_description))
        try:
            print u" {0:<{width}s}     ⤷   \"{1:s}\"".format(' ', destination, width=len(transition_description))
        except UnicodeEncodeError:
            print u" {0:<{width}s}     `-> \"{1:s}\"".format(' ', destination, width=len(transition_description))


def handle_file(filename, tags, do_remove, do_filter, dryrun):
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
    if do_filter:
        assert do_filter.__class__ == bool
    if dryrun:
        assert dryrun.__class__ == bool

    if os.path.isdir(filename):
        logging.warning("Skipping directory \"%s\" because this tool only renames file names." % filename)
        return
    elif not os.path.isfile(filename):
        logging.debug("file type error in folder [%s]: file type: is file? %s  -  is dir? %s  -  is mount? %s" % (os.getcwdu(), str(os.path.isfile(filename)), str(os.path.isdir(filename)), str(os.path.islink(filename))))
        logging.error("Skipping \"%s\" because this tool only renames existing file names." % filename)
        return

    if do_filter:
        print_item_transition(filename, TAGFILTER_DIRECTORY, transition='link')
        if not dryrun:
            os.symlink(os.path.join(os.getcwdu(), filename),
                       os.path.join(TAGFILTER_DIRECTORY, filename))

    else:  # add or remove tags:
        new_filename = filename

        for tagname in tags:
            if do_remove:
                new_filename = removing_tag_from_filename(new_filename, tagname)
            else:
                ## FIXXME: not performance optimized for large number of unique tags in many lists:
                tag_in_unique_tags, matching_unique_tag_list = item_contained_in_list_of_lists(tagname, unique_tags)

                if tagname != tag_in_unique_tags:
                    new_filename = adding_tag_to_filename(new_filename, tagname)
                else:
                    ## if tag within unique_tags found, and new unique tag is given, remove old tag:
                    ## e.g.: unique_tags = (u'yes', u'no') -> if 'no' should be added, remove existing tag 'yes' (and vice versa)
                    ## If user enters contradicting tags, only the last one will be applied.
                    ## FIXXME: this is an undocumented feature -> please add proper documentation

                    current_filename_tags = extract_tags_from_filename(new_filename)
                    conflicting_tags = list(set(current_filename_tags).intersection(matching_unique_tag_list))
                    logging.debug("found unique tag %s which require old unique tag(s) to be removed: %s" % (tagname, repr(conflicting_tags)))
                    for conflicting_tag in conflicting_tags:
                        new_filename = removing_tag_from_filename(new_filename, conflicting_tag)
                    new_filename = adding_tag_to_filename(new_filename, tagname)

        if do_remove:
            transition = 'delete'
        else:
            transition = 'add'

        if dryrun:
            logging.info(u" ")
            print_item_transition(filename, new_filename, transition=transition)
        else:
            if filename != new_filename:
                if not options.quiet:
                    print_item_transition(filename, new_filename, transition=transition)
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


def get_tags_from_files_and_subfolders(startdir=os.getcwdu(), use_cache=True):
    """
    Traverses the file system starting with given directory,
    returns dict of all tags (including starttags) of all file

    @param return: dict of tags and their number of occurrence
    """

    ## add ", starttags=False" to parameters to enable this feature in future
    starttags = False

    assert os.path.isdir(startdir)

    if not starttags:
        tags = {}
    else:
        assert starttags.__class__ == dict
        tags = starttags

    global cache_of_tags_by_folder

    logging.debug('get_tags_from_files_and_subfolders called with startdir [%s], cached startdirs [%s]' % (startdir, str(len(cache_of_tags_by_folder.keys()))))

    if use_cache and startdir in cache_of_tags_by_folder.keys():
        logging.debug("found " + str(len(cache_of_tags_by_folder[startdir])) + " tags in cache for directory: " + startdir)
        return cache_of_tags_by_folder[startdir]

    else:

        for root, dirs, files in os.walk(startdir):

            # logging.debug('get_tags_from_files_and_subfolders: root [%s]' % root)  # LOTS of debug output

            for filename in files:
                for tag in extract_tags_from_filename(filename):
                    tags = add_tag_to_countdict(tag, tags)

            for dirname in dirs:
                for tag in extract_tags_from_filename(dirname):
                    tags = add_tag_to_countdict(tag, tags)

            ## Enable recursive directory traversal for specific options:
            if not (options.recursive and (options.list_tags_by_alphabet or
                                           options.list_tags_by_number or
                                           options.list_unknown_tags or
                                           options.tag_gardening)):
                break  # do not loop

        logging.debug("Writing " + str(len(tags.keys())) + " tags in cache for directory: " + startdir)
        if use_cache:
            cache_of_tags_by_folder[startdir] = tags
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


def print_tag_dict(tag_dict_reference, vocabulary=False, sort_index=0, print_similar_vocabulary_tags=False, print_only_tags_with_similar_tags=False):
    """
    Takes a dictionary which holds tag names and their occurrence and prints it to stdout.
    Tags that appear also in the vocabulary get marked in the output.

    @param tag_dict: a dictionary holding tags and their occurrence number
    @param vocabulary: array of tags from controlled vocabulary or False
    """

    tag_dict = {}
    tag_dict = tag_dict_reference

    ## determine maximum length of strings for formatting:
    maxlength_tags = max(len(s) for s in tag_dict.keys()) + len(HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)
    maxlength_count = len(str(abs(max(tag_dict.values()))))
    if maxlength_count < 5:
        maxlength_count = 5

    hint_for_being_in_vocabulary = ''
    similar_tags = u''
    if vocabulary:
        print u"\n  (Tags marked with \"" + HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE + "\" appear in your vocabulary.)"
    print "\n {0:{1}} : {2:{3}}".format(u'count', maxlength_count, u'tag', maxlength_tags)
    print " " + '-' * (maxlength_tags + maxlength_count + 7)
    for tuple in sorted(tag_dict.items(), key=operator.itemgetter(sort_index)):
        ## sort dict of (tag, count) according to sort_index

        if vocabulary and tuple[0] in vocabulary:
            hint_for_being_in_vocabulary = HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
        else:
            hint_for_being_in_vocabulary = ''

        similar_tags_list = []
        if vocabulary and print_similar_vocabulary_tags:
            tags_for_comparing = list(set(tag_dict.keys()).union(set(vocabulary)))  # unified elements of both lists
            similar_tags_list = find_similar_tags(tuple[0], tags_for_comparing)
            if similar_tags_list:
                similar_tags = u'      (similar to:  ' + ', '.join(similar_tags_list) + u')'
            else:
                similar_tags = u''
        else:
            similar_tags = u''

        if (print_only_tags_with_similar_tags and similar_tags_list) or not print_only_tags_with_similar_tags:
            print " {0:{1}} : {2:{3}}   {4}".format(tuple[1], maxlength_count, tuple[0] + hint_for_being_in_vocabulary, maxlength_tags, similar_tags)

    print ''


def print_tag_set(tag_set, vocabulary=False, print_similar_vocabulary_tags=False):
    """
    Takes a set which holds tag names and prints it to stdout.
    Tags that appear also in the vocabulary get marked in the output.

    @param tag_set: a set holding tags
    @param vocabulary: array of tags from controlled vocabulary or False
    @param print_similar_vocabulary_tags: if a vocabulary is given and tags are similar to it, print a list of them
    """

    ## determine maximum length of strings for formatting:
    maxlength_tags = max(len(s) for s in tag_set) + len(HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)

    hint_for_being_in_vocabulary = ''
    if vocabulary:
        print u"\n  (Tags marked with \"" + HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE + "\" appear in your vocabulary.)\n"

    for tag in sorted(tag_set):

        if vocabulary and tag in vocabulary:
            hint_for_being_in_vocabulary = HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
        else:
            hint_for_being_in_vocabulary = ''

        if vocabulary and print_similar_vocabulary_tags:
            tags_for_comparing = list(tag_set.union(set(vocabulary)))  # unified elements of both lists
            similar_tags_list = find_similar_tags(tag, tags_for_comparing)
            if similar_tags_list:
                similar_tags = u'      (similar to:  ' + ', '.join(similar_tags_list) + u')'
            else:
                similar_tags = u''
        else:
            similar_tags = u''

        print "  {0:{1}}   {2}".format(tag + hint_for_being_in_vocabulary, maxlength_tags, similar_tags)

    print ''


def list_unknown_tags(file_tag_dict):
    """
    Traverses the file system, extracts all tags, prints tags that are found in file names which are not found in the controlled vocabulary file .filetags

    @param return: dict of tags (if max_tag_count is set, returned entries are set accordingly)
    """

    vocabulary = locate_and_parse_controlled_vocabulary(False)

    ## filter out known tags from tag_dict
    unknown_tag_dict = {key: value for key, value in file_tag_dict.items() if key not in vocabulary}

    if unknown_tag_dict:
        print_tag_dict(unknown_tag_dict, vocabulary)
    else:
        print "\n  " + str(len(file_tag_dict)) + " different tags were found in file names which are all" + \
            " part of your .filetags vocabulary (consisting of " + str(len(vocabulary)) + " tags).\n"

    return unknown_tag_dict


def handle_tag_gardening(vocabulary):
    """
    This method is quite handy to find tags that might contain typos or do not
    differ much from other tags. You might want to rename them accordinly.

    Tags are gathered from the file system.

    Tags that appear also in the vocabulary get marked in the output.

    @param vocabulary: array containing the controlled vocabulary (or False)
    @param return: -
    """

    tag_dict = get_tags_from_files_and_subfolders(startdir=os.getcwdu())
    if not tag_dict:
        print "\nNo file containing tags found in this folder hierarchy.\n"
        return

    print u"\nYou have used " + str(len(tag_dict)) + " tags in total.\n"

    if vocabulary:

        print u'\nYour controlled vocabulary is defined in ' + controlled_vocabulary_filename + ' and contains ' + str(len(vocabulary)) + ' tags.\n'

        vocabulary_tags_not_used = set(vocabulary) - set(tag_dict.keys())
        if vocabulary_tags_not_used:
            print u"\nTags from your vocabulary which you didn't use:\n"
            print_tag_set(vocabulary_tags_not_used)

        tags_not_in_vocabulary = set(tag_dict.keys()) - set(vocabulary)
        if tags_not_in_vocabulary:
            print u"\nTags you used that are not in the vocabulary:\n"
            print_tag_set(tags_not_in_vocabulary)

    print "\nTags that appear only once are most probably typos or you have forgotten them:"
    tags_only_used_once_dict = {key: value for key, value in tag_dict.items() if value < 2}
    print_tag_dict(tags_only_used_once_dict, vocabulary, sort_index=0, print_only_tags_with_similar_tags=False)

    print "\nTags which have similar other tags are probably typos or plural/singular forms of others:"
    tags_for_comparing = list(set(tag_dict.keys()).union(set(vocabulary)))  # unified elements of both lists
    only_similar_tags_by_alphabet_dict = {key: value for key, value in tag_dict.items() if find_similar_tags(key, tags_for_comparing)}
    print_tag_dict(only_similar_tags_by_alphabet_dict, vocabulary, sort_index=0, print_similar_vocabulary_tags=True)

    tags_only_used_once_set = set(tags_only_used_once_dict.keys())
    only_similar_tags_by_alphabet_set = set(only_similar_tags_by_alphabet_dict.keys())
    tags_in_both_outputs = tags_only_used_once_set.intersection(only_similar_tags_by_alphabet_set)

    if tags_in_both_outputs != set([]):
        print "\nIf tags appear in both lists from above (only once and similar to others), they most likely\nrequire your attention:"
        print_tag_set(tags_in_both_outputs, vocabulary=vocabulary, print_similar_vocabulary_tags=True)


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

    if startfile:
        filename = locate_file_in_cwd_and_parent_directories(startfile, CONTROLLED_VOCABULARY_FILENAME)
    else:
        filename = locate_file_in_cwd_and_parent_directories(os.getcwdu(), CONTROLLED_VOCABULARY_FILENAME)

    global unique_tags

    if filename:
        if os.path.isfile(filename):
            logging.debug('locate_and_parse_controlled_vocabulary: found controlled vocabulary in folder of startfile')
            tags = []
            with codecs.open(filename, encoding='utf-8') as filehandle:
                logging.debug('locate_and_parse_controlled_vocabulary: reading controlled vocabulary in [%s]' % filename)
                global controlled_vocabulary_filename
                controlled_vocabulary_filename = filename
                for rawline in filehandle:
                    line = rawline.strip()
                    if BETWEEN_TAG_SEPARATOR in line:
                        ## if multiple tags are in one line, they are mutually exclusive: only has can be set via filetags
                        logging.debug('locate_and_parse_controlled_vocabulary: found unique tags: %s' % (line))
                        unique_tags.append(line.split(BETWEEN_TAG_SEPARATOR))
                        for tag in line.split(BETWEEN_TAG_SEPARATOR):
                            ## *also* append unique tags to general tag list:
                            tags.append(tag)
                    else:
                        tags.append(line)
            logging.debug('locate_and_parse_controlled_vocabulary: controlled vocabulary has %i tags' % len(tags))
            logging.debug('locate_and_parse_controlled_vocabulary: controlled vocabulary has %i groups of unique tags' % (len(unique_tags) - 1))
            return tags
        else:
            logging.debug('locate_and_parse_controlled_vocabulary: could not find controlled vocabulary in folder of startfile')
            return []
    else:
        logging.debug('locate_and_parse_controlled_vocabulary: could not derive filename for controlled vocabulary in folder of startfile')
        return []


def print_tag_shortcut_with_numbers(tag_list, tags_get_added=True, tags_get_linked=False):
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
    elif tags_get_linked:
        if len(tag_list) < 9:
            hint_string = u"Used tags in this directory:"
        else:
            hint_string = u"Top nine used tags in this directory:"
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
    try:
        print u'    ' + u' ⋅ '.join(list_of_tag_hints)
    except UnicodeEncodeError:
        print u'    ' + u' - '.join(list_of_tag_hints)
    print u''  # newline at end


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
        logging.debug('single entered tag is an integer; stepping through the integers')
        for character in list(potential_shortcut_string[0]):
            logging.debug('adding tag number %s' % character)
            try:
                tags.append(list_of_shortcut_tags[int(character) - 1])
            except IndexError:
                return potential_shortcut_string
    except ValueError:
        logging.debug('single entered tag is a normal tag')
        tags = potential_shortcut_string

    return tags


def get_upto_nine_keys_of_dict_with_highest_value(mydict, list_of_tags_to_omit=[]):
    """
    Takes a dict, sorts it according to their values, and returns up to nine
    values with the highest values.

    Example1: { "key2":45, "key1": 33} -> [ "key1", "key2" ]

    @param mydict: dictionary holding keys and values
    @param list_of_tags_to_omit: list of strings that should not be part of the returned list
    @param return: list of up to top nine keys according to the rank of their values
    """

    assert mydict.__class__ == dict

    complete_list = sorted(mydict, key=mydict.get, reverse=True)

    logging.debug("get_upto_nine_keys_of_dict_with_highest_value: complete_list: " + ", ".join(complete_list))
    if list_of_tags_to_omit:
        logging.debug("get_upto_nine_keys_of_dict_with_highest_value: omitting tags: " + ", ".join(list_of_tags_to_omit))
        complete_list = [x for x in complete_list if x not in list_of_tags_to_omit]

    return sorted(complete_list[:9])


def _get_tag_visual(tags_for_visual=None):
    """
    Returns a visual representation of a tag. If the optional tags_for_visual
    is given, write the list of those tags into to the tag as well.

    @param tags_for_visual: list of strings with tags
    @param return: string with a multi-line representation of a visual tag
    """

    if not tags_for_visual:
        tags = " ? "
    else:
        tags = BETWEEN_TAG_SEPARATOR.join(sorted(tags_for_visual))

    length = len(tags)
    visual = "         .---" + '-' * length + "--, \n" + \
             "        | o  " + tags + "  | \n" + \
             "         `---" + '-' * length + "--' "

    return visual


def ask_for_tags(vocabulary, upto9_tags_for_shortcuts, tags_for_visual=None):
    """
    Takes a vocabulary and optional up to nine tags for shortcuts and interactively asks
    the user to enter tags. Aborts program if no tags were entered. Returns list of
    entered tags.

    @param vocabulary: array containing the controlled vocabulary
    @param upto9_tags_for_shortcuts: array of tags which can be used to generate number-shortcuts
    @param return: list of up to top nine keys according to the rank of their values
    """

    completionhint = u''
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
    print _get_tag_visual(tags_for_visual)
    print "                     "

    if len(upto9_tags_for_shortcuts) > 0:
        print_tag_shortcut_with_numbers(upto9_tags_for_shortcuts,
                                        tags_get_added=(not options.remove and not options.tagfilter),
                                        tags_get_linked=options.tagfilter)

    logging.debug("interactive mode: asking for tags ...")
    entered_tags = raw_input('Tags: ').strip()
    tags_from_userinput = extract_tags_from_argument(entered_tags)

    if not tags_from_userinput:
        logging.info("no tags given, exiting.")
        sys.stdout.flush()
        sys.exit(0)
    else:
        if len(tags_from_userinput) == 1 and len(upto9_tags_for_shortcuts) > 0:
            ## check if user entered number shortcuts for tags to be removed:
            tags_from_userinput = check_for_possible_shortcuts_in_entered_tags(tags_from_userinput, upto9_tags_for_shortcuts)
        return tags_from_userinput


def get_files_of_directory(directory):
    """
    Lists the files of the given directory and returns a list of its files.

    @param directory: string of an existing directory
    @param return: list of file names of given directory
    """

    files = []
    for (dirpath, dirnames, filenames) in os.walk(directory):
        files.extend(filenames)
        break
    return files


def filter_files_matching_tags(allfiles, tags):
    """
    Returns a list of file names that contain all given tags.

    @param allfiles: array of file names
    @param tags: array of tags
    @param return: list of file names that contain all tags
    """

    return [x for x in allfiles if set(extract_tags_from_filename(x)).issuperset(set(tags))]


def assert_empty_tagfilter_directory():
    """
    Creates non-existent tagfilter directory or deletes and re-creates it.
    """

    if not os.path.isdir(TAGFILTER_DIRECTORY):
        logging.debug('creating non-existent tagfilter directory "%s" ...' % str(TAGFILTER_DIRECTORY))
        if not options.dryrun:
            os.makedirs(TAGFILTER_DIRECTORY)
    else:
        logging.debug('found old tagfilter directory "%s"; deleting directory ...' % str(TAGFILTER_DIRECTORY))
        if not options.dryrun:
            save_import('shutil')  # for removing directories with shutil.rmtree()
            shutil.rmtree(TAGFILTER_DIRECTORY)
            logging.debug('re-creating tagfilter directory "%s" ...' % str(TAGFILTER_DIRECTORY))
            os.makedirs(TAGFILTER_DIRECTORY)
    if not options.dryrun:
        assert(os.path.isdir(TAGFILTER_DIRECTORY))


def get_common_tags_from_files(files):
    """
    Returns a list of tags that are common (intersection) for all files.

    @param files: array of file names
    @param return: list of tags
    """

    list_of_tags_per_file = []
    for currentfile in files:
        list_of_tags_per_file.append(set(extract_tags_from_filename(currentfile)))

    return list(set.intersection(*list_of_tags_per_file))


def successful_exit():
    logging.debug("successfully finished.")
    sys.stdout.flush()
    sys.exit(0)


def main():
    """Main function"""

    if options.version:
        print os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_DATE
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
    logging.debug('reported console width: ' + str(TTY_WIDTH) + ' and height: ' + str(TTY_HEIGHT) + '   (80/80 is the fall-back)')
    tags_from_userinput = []
    vocabulary = sorted(locate_and_parse_controlled_vocabulary(False))

    if len(args) < 1 and not (options.tagfilter or options.list_tags_by_alphabet or options.list_tags_by_number or options.list_unknown_tags or options.tag_gardening):
        error_exit(5, "Please add at least one file name as argument")

    if options.list_tags_by_alphabet or options.list_tags_by_number or options.list_unknown_tags:

        tag_dict = get_tags_from_files_and_subfolders(startdir=os.getcwdu())
        if not tag_dict:
            print "\nNo file containing tags found in this folder hierarchy.\n"
            return {}

        if options.list_tags_by_alphabet:
            logging.debug("handling option list_tags_by_alphabet")
            print_tag_dict(tag_dict, vocabulary=vocabulary, sort_index=0, print_similar_vocabulary_tags=True)
            successful_exit()

        elif options.list_tags_by_number:
            logging.debug("handling option list_tags_by_number")
            print_tag_dict(tag_dict, vocabulary=vocabulary, sort_index=1, print_similar_vocabulary_tags=True)
            successful_exit()

        elif options.list_unknown_tags:
            logging.debug("handling option list_unknown_tags")
            list_unknown_tags(tag_dict)
            successful_exit()

    elif options.tag_gardening:
        logging.debug("handling option for tag gardening")
        handle_tag_gardening(vocabulary)
        successful_exit()

    elif options.interactive or not options.tags:

        tags_for_visual = None

        if len(args) < 1 and not options.tagfilter:
            error_exit(5, "Please add at least one file name as argument")

        tags_for_vocabulary = {}
        upto9_tags_for_shortcuts = []

        # look out for .filetags file and add readline support for tag completion if found with content
        if options.remove:
            # vocabulary for completing tags is current tags of files
            for currentfile in files:
                # add tags so that list contains all unique tags:
                for newtag in extract_tags_from_filename(currentfile):
                    add_tag_to_countdict(newtag, tags_for_vocabulary)
            vocabulary = sorted(tags_for_vocabulary.keys())
            upto9_tags_for_shortcuts = sorted(get_upto_nine_keys_of_dict_with_highest_value(tags_for_vocabulary))

        elif options.tagfilter:
            for tag in get_tags_from_files_and_subfolders(startdir=os.getcwdu()):
                add_tag_to_countdict(tag, tags_for_vocabulary)

            logging.debug('generating vocabulary ...')
            vocabulary = sorted(tags_for_vocabulary.keys())
            upto9_tags_for_shortcuts = sorted(get_upto_nine_keys_of_dict_with_highest_value(tags_for_vocabulary))

        else:
            if files:

                # remove given (common) tags from the vocabulary:
                tags_intersection_of_files = get_common_tags_from_files(files)
                tags_for_visual = tags_intersection_of_files
                logging.debug("found common tags: tags_intersection_of_files[%s]" % '], ['.join(tags_intersection_of_files))
                vocabulary = list(set(vocabulary) - set(tags_intersection_of_files))

                logging.debug('deriving upto9_tags_for_shortcuts ...')
                upto9_tags_for_shortcuts = sorted(get_upto_nine_keys_of_dict_with_highest_value(get_tags_from_files_and_subfolders(startdir=os.path.dirname(os.path.abspath(files[0]))), tags_intersection_of_files))
                logging.debug('derived upto9_tags_for_shortcuts')
            logging.debug('derived vocabulary with %i entries' % len(vocabulary))  # using default vocabulary which was generate above

        # ==================== Interactive asking user for tags ============================= ##
        tags_from_userinput = ask_for_tags(vocabulary, upto9_tags_for_shortcuts, tags_for_visual)
        # ==================== Interactive asking user for tags ============================= ##

    else:
        # non-interactive: extract list of tags
        logging.debug("non-interactive mode: extracting tags from argument ...")

        tags_from_userinput = extract_tags_from_argument(options.tags)

        if not tags_from_userinput:
            # FIXXME: check: can this be the case?
            logging.info("no tags given, exiting.")
            sys.stdout.flush()
            sys.exit(0)

    logging.debug("tags found: [%s]" % '], ['.join(tags_from_userinput))
    if options.remove:
        logging.info("removing tags \"%s\" ..." % str(BETWEEN_TAG_SEPARATOR.join(tags_from_userinput)))
    elif options.tagfilter:
        logging.info("filtering items with tag(s) \"%s\" and linking to directory \"%s\" ..." %
                     (str(BETWEEN_TAG_SEPARATOR.join(tags_from_userinput)), str(TAGFILTER_DIRECTORY)))
    else:
        logging.info("adding tags \"%s\" ..." % str(BETWEEN_TAG_SEPARATOR.join(tags_from_userinput)))

    if options.tagfilter and not files:
        assert_empty_tagfilter_directory()
        files = filter_files_matching_tags(get_files_of_directory(os.getcwdu()), tags_from_userinput)

    logging.debug("iterate over files ...")

    global max_file_length
    for filename in files:
        if len(filename) > max_file_length:
            max_file_length = len(filename)
    logging.debug('determined maximum file name length with %i' % max_file_length)

    for filename in files:
        if filename.__class__ == str:
            filename = unicode(filename, "UTF-8")
        handle_file(filename, tags_from_userinput, options.remove, options.tagfilter, options.dryrun)

    if options.tagfilter:
        save_import('subprocess')
        save_import('platform')
        current_platform = platform.system()
        logging.debug('platform.system() is: [' + current_platform + ']')
        if current_platform == 'Linux':
            subprocess.call([DEFAULT_IMAGE_VIEWER_LINUX, TAGFILTER_DIRECTORY])
        else:
            logging.info('No (default) image viewer defined for platform \"' + current_platform + '\".')
            logging.info('Please visit ' + TAGFILTER_DIRECTORY + ' to view filtered items.')

    successful_exit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

# END OF FILE #################################################################

# end

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
PROG_VERSION = "Time-stamp: <2018-03-18 16:55:59 vk>"

# TODO:
# - fix parts marked with «FIXXME»
# - $HOME/.config/ with default options (e.g., geeqie)
#   - using clint/resource
#   - if not found, write default config with defaults (and comments)
# - tagfilter: --copy :: copy files instead of creating symlinks
# - tagfilter: all toggle-cmd line args as special tags: --copy and so forth
#   - e.g., when user enters tag "--copy" when interactively reading tags, handle it like options.copy
#   - overwriting cmd-line arguments (if contradictory)
#   - allow combination of cmd-line tags and interactive tags
#     - they get combined
# - tagfilter: additional parameter to move matching files to a temporary subfolder
#   - renaming/deleting of symlinks does not modify original files
# - tagfilter: --recursive :: recursively going into subdirectories and
#      collecting items (into one target directory) for:
#   - adding tags
#   - removing tags
#   - filter
# - tagfilter: --notags :: do not ask for tags, use all items that got no tag
#      at all
# - tagfilter: --ignoredirs :: do not symlink/copy directories
# - tagfilter: --emptytmpdir :: empty temporary directory after the image viewer exits
# - use "open" to open first(?) file


# ===================================================================== ##
#  You might not want to modify anything below this line if you do not  ##
#  know, what you are doing :-)                                         ##
# ===================================================================== ##

from importlib import import_module


def save_import(library):
    try:
        globals()[library] = import_module(library)
    except ImportError:
        print("Could not find Python module \"" + library + "\".\nPlease install it, e.g., with \"sudo pip install " + library + "\".")
        sys.exit(2)


import re
import sys
import os
import platform
save_import('argparse')   # for handling command line arguments
save_import('time')
save_import('logging')
save_import('operator')   # for sorting dicts
save_import('difflib')    # for good enough matching words
save_import('readline')   # for raw_input() reading from stdin
save_import('codecs')     # for handling Unicode content in .tagfiles
save_import('math')       # (integer) calculations
save_import('clint')      # for config file handling
save_import('itertools')  # for calculating permutations of tagtrees
save_import('colorama')   # for colorful output
if platform.system() == 'Windows':
    try:
        import win32com.client
    except ImportError:
        print("Could not find Python module \"win32com.client\".\nPlease install it, e.g., with \"sudo pip install pypiwin32\".")
        sys.exit(2)

PROG_VERSION_DATE = PROG_VERSION[13:23]
# unused: INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
FILENAME_TAG_SEPARATOR = ' -- '
BETWEEN_TAG_SEPARATOR = ' '
CONTROLLED_VOCABULARY_FILENAME = ".filetags"
HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE = ' *'
TAGFILTER_DIRECTORY = os.path.join(os.path.expanduser("~"), ".filetags_tagfilter")
DEFAULT_TAGTREES_MAXDEPTH = 2  # be careful when making this more than 2: exponential growth of time/links with number of tags!
DEFAULT_IMAGE_VIEWER_LINUX = 'geeqie'
DEFAULT_IMAGE_VIEWER_WINDOWS = 'explorer'
TAG_SYMLINK_ORIGINALS_WHEN_TAGGING_SYMLINKS = True

# Determining the window size of the terminal:
if platform.system() != 'Windows':
    try:
        TTY_HEIGHT, TTY_WIDTH = [int(x) for x in os.popen('stty size', 'r').read().split()]
    except ValueError:
        TTY_HEIGHT, TTY_WIDTH = 80, 80  # fall-back values
else:
    TTY_HEIGHT, TTY_WIDTH = 80, 80  # fall-back values

max_file_length = 0  # will be set after iterating over source files182

UNIQUE_TAG_TESTSTRINGS = ['teststring1', 'teststring2']
unique_tags = [UNIQUE_TAG_TESTSTRINGS]  # list of list which contains tags that are mutually exclusive
# Note: u'teststring1' and u'teststring2' are hard-coded for testing purposes.
#       You might delete them if you don't use my unit test suite.

DESCRIPTION = "This tool adds or removes simple tags to/from file names.\n\
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
  " + sys.argv[0] + " --tags=\"presentation projectA\" *.pptx\n\
      … adds the tags \"presentation\" and \"projectA\" to all PPTX-files\n\
  " + sys.argv[0] + " --tags=\"presentation -projectA\" *.pptx\n\
      … adds the tag \"presentation\" to and removes tag \"projectA\" from all PPTX-files\n\
  " + sys.argv[0] + " -i *\n\
      … ask for tag(s) and add them to all files in current folder\n\
  " + sys.argv[0] + " -r draft *report*\n\
      … removes the tag \"draft\" from all files containing the word \"report\"\n\
\n\
\n\
This tools is looking for the optional first text file named \".filetags\" in\n\
current and parent directories. Each of its lines is interpreted as a tag\n\
for tag completion. Multiple tags per line are considered mutual exclusive.\n\
\n\
Verbose description: http://Karl-Voit.at/managing-digital-photographs/"

EPILOG = u"\n\
:copyright: (c) by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:URL: https://github.com/novoid/filetag\n\
:bugreports: via github or <tools@Karl-Voit.at>\n\
:version: " + PROG_VERSION_DATE + "\n·\n"


# file names containing tags matches following regular expression
FILE_WITH_TAGS_REGEX = re.compile("(.+?)" + FILENAME_TAG_SEPARATOR + "(.+?)(\.(\w+))??$")
FILE_WITH_TAGS_REGEX_FILENAME_INDEX = 1  # component.group(1)
FILE_WITH_TAGS_REGEX_TAGLIST_INDEX = 2
FILE_WITH_TAGS_REGEX_EXTENSION_INDEX = 4

FILE_WITH_EXTENSION_REGEX = re.compile("(.*)\.(.*)$")
FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX = 1
FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX = 2

YYYY_MM_DD_PATTERN = re.compile('^(\d{4,4})-([01]\d)-([0123]\d)[- _T]')

cache_of_tags_by_folder = {}
cache_of_files_with_metadata = {}  # dict of big list of dicts: 'filename', 'path' and other metadata
controlled_vocabulary_filename = ''
list_of_symlink_directories = []

parser = argparse.ArgumentParser(prog=sys.argv[0],
                                 # keep line breaks in EPILOG and such
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=EPILOG,
                                 description=DESCRIPTION)

parser.add_argument(dest="files", metavar='FILE', nargs='*', help='One or more files to tag')

parser.add_argument("-t", "--tags",
                    dest="tags",
                    nargs=1,
                    type=str,
                    metavar='"STRING WITH TAGS"',
                    required=False,
                    help="one or more tags (in quotes, separated by spaces) to add/remove")

parser.add_argument("--remove", action="store_true",
                    help="remove tags from (instead of adding to) file name(s)")

parser.add_argument("-i", "--interactive", action="store_true", dest="interactive",
                    help="interactive mode: ask for (a)dding or (r)emoving and name of tag(s)")

parser.add_argument("-R", "--recursive", dest="recursive", action="store_true",
                    help="recursively go through the current directory and all of its subdirectories. Implemented for --tag-gardening and --tagtrees")

parser.add_argument("-s", "--dryrun", dest="dryrun", action="store_true",
                    help="enable dryrun mode: just simulate what would happen, do not modify files")

parser.add_argument("-f", "--filter", dest="tagfilter", action="store_true",
                    help="ask for list of tags and generate links in \"" + TAGFILTER_DIRECTORY + "\" " +
                    "containing symbolic links to all files with matching tags and start the filebrowser")

parser.add_argument("--filebrowser", dest="filebrowser", metavar='PATH_TO_FILEBROWSER',
                    help="use this option to override the tool to view/manage files (for --filter; default: " +
                    DEFAULT_IMAGE_VIEWER_LINUX + "). Use \"none\" to omit the default one.")

parser.add_argument("--tagtrees", dest="tagtrees", action="store_true",
                    help="This generates nested directories in \"" + TAGFILTER_DIRECTORY + "\" for each combination of tags " +
                    "up to a limit of " + str(DEFAULT_TAGTREES_MAXDEPTH) + ". " +
                    "Please note that this may take long since it relates " +
                    "exponentially to the number of tags involved. " +
                    "See also http://Karl-Voit.at/tagstore/ and http://Karl-Voit.at/tagstore/downloads/Voit2012b.pdf")

parser.add_argument("--tagtrees-handle-no-tag",
                    dest="tagtrees_handle_no_tag",
                    nargs=1,
                    type=str,
                    metavar='"treeroot" | "ignore" | "FOLDERNAME"',
                    required=False,
                    help="When tagtrees are created, this parameter defines how to handle items that got no tag at all. " +
                    "The value \"treeroot\" is the default behavior: items without a tag are linked to the tagtrees root. " +
                    "The value \"ignore\" will not link any non-tagged items at all. " +
                    "Any other value is interpreted as a folder name within the tagreees which is used to link all non-tagged items to.")

parser.add_argument("--tagtrees-link-missing-mutual-tagged-items", dest="tagtrees_link_missing_mutual_tagged_items", action="store_true",
                    help="When the controlled vocabulary holds mutual exclusive tags (multiple tags in one line) " +
                    "this option generates directories in the tagtrees root that hold links to items that have no " +
                    "single tag from those mutual exclusive sets. For example, when \"draft final\" is defined in the vocabulary, " +
                    "all items without \"draft\" and \"final\" are linked to the \"no-draft-final\" directory.")

parser.add_argument("--tagtrees-dir",
                    dest="tagtrees_directory",
                    nargs=1,
                    type=str,
                    metavar='<existing_directory>',
                    required=False,
                    help="When tagtrees are created, this parameter overrides the default target directory \"" + TAGFILTER_DIRECTORY +
                    "\" with a user-defined one. It has to be an empty directory or a non-existing directory which will be created.")

parser.add_argument("--tagtrees-depht",
                    dest="tagtrees_depth",
                    nargs=1,
                    type=int,
                    required=False,
                    help="When tagtrees are created, this parameter defines the level of depth of the tagtree hierarchy. " +
                    "The default value is 2. Please note that increasing the depth increases the number of links exponentially. " +
                    "Especially when running Windows (using lnk-files instead of symbolic links) the performance is really slow. " +
                    "Choose wisely.")

parser.add_argument("--ln", "--list-tags-by-number", dest="list_tags_by_number", action="store_true",
                    help="list all file-tags sorted by their number of use")

parser.add_argument("--la", "--list-tags-by-alphabet", dest="list_tags_by_alphabet", action="store_true",
                    help="list all file-tags sorted by their name")

parser.add_argument("--lu", "--list-tags-unknown-to-vocabulary", dest="list_unknown_tags", action="store_true",
                    help="list all file-tags which are found in file names but are not part of .filetags")

parser.add_argument("--tag-gardening", dest="tag_gardening", action="store_true",
                    help="This is for getting an overview on tags that might require to be renamed (typos, " +
                    "singular/plural, ...). See also http://www.webology.org/2008/v5n3/a58.html")

parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                    help="enable verbose mode")

parser.add_argument("-q", "--quiet", dest="quiet", action="store_true",
                    help="enable quiet mode")

parser.add_argument("--version", dest="version", action="store_true",
                    help="display version and exit")

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


class SimpleCompleter(object):
    # happily stolen from http://pymotw.com/2/readline/

    def __init__(self, options):
        self.options = sorted(options)

        # removing '-' as a delimiter character in order to be able to use '-tagname' for removing:
        readline.set_completer_delims(readline.get_completer_delims().replace('-', ''))

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

    assert(filename.__class__ == str)
    if tagname:
        assert(tagname.__class__ == str)

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

    assert(filename.__class__ == str)

    components = re.match(FILE_WITH_TAGS_REGEX, os.path.basename(filename))

    if not components:
        return []
    else:
        return components.group(FILE_WITH_TAGS_REGEX_TAGLIST_INDEX).split(BETWEEN_TAG_SEPARATOR)


def extract_tags_from_path(path):
    """
    Returns list of all tags contained within the absolute path that may contain
    directories and an optional file. If no tag is found, return empty list.

    @param path: an unicode string containing a path
    @param return: list of tags
    """

    def splitall(path):
        """
        Snippet from https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch04s16.html

        >>> splitall('a/b/c')
        ['a', 'b', 'c']
        >>> splitall('/a/b/c/')
        ['/', 'a', 'b', 'c', '']
        >>> splitall('/')
        ['/']
        >>> splitall('C:')
        ['C:']
        >>> splitall('C:\\')
        ['C:\\']
        >>> splitall('C:\\a')
        ['C:\\', 'a']
        >>> splitall('C:\\a\\')
        ['C:\\', 'a', '']
        >>> splitall('C:\\a\\b')
        ['C:\\', 'a', 'b']
        >>> splitall('a\\b')
        ['a', 'b']
        """

        allparts = []
        while 1:
            parts = os.path.split(path)
            if parts[0] == path:  # sentinel for absolute paths
                allparts.insert(0, parts[0])
                break
            elif parts[1] == path:  # sentinel for relative paths
                allparts.insert(0, parts[1])
                break
            else:
                path = parts[0]
                allparts.insert(0, parts[1])
        return allparts

    assert(path.__class__ == str)

    tags = []
    abspath = os.path.abspath(path)
    for item in splitall(abspath):
        itemtags = extract_tags_from_filename(item)
        for currentitemtag in itemtags:
            if currentitemtag not in tags:
                tags.append(currentitemtag)
    return tags


def adding_tag_to_filename(filename, tagname):
    """
    Returns string of file name with tagname as additional tag.

    @param filename: an unicode string containing a file name
    @param tagname: an unicode string containing a tag name
    @param return: an unicode string of filename containing tagname
    """

    assert(filename.__class__ == str)
    assert(tagname.__class__ == str)

    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)

    if contains_tag(basename) is False:
        logging.debug("adding_tag_to_filename(%s, %s): no tag found so far" % (filename, tagname))

        components = re.match(FILE_WITH_EXTENSION_REGEX, os.path.basename(basename))
        if components:
            old_basename = components.group(FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX)
            extension = components.group(FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX)
            return os.path.join(dirname, old_basename + FILENAME_TAG_SEPARATOR + tagname + '.' + extension)
        else:
            return os.path.join(dirname, basename + FILENAME_TAG_SEPARATOR + tagname)

    elif contains_tag(basename, tagname):
        logging.debug("adding_tag_to_filename(%s, %s): tag already found in filename" % (filename, tagname))

        return filename

    else:
        logging.debug("adding_tag_to_filename(%s, %s): add as additional tag to existing list of tags" %
                      (filename, tagname))

        components = re.match(FILE_WITH_EXTENSION_REGEX, basename)
        if components:
            old_basename = components.group(FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX)
            extension = components.group(FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX)
            return os.path.join(dirname, old_basename + BETWEEN_TAG_SEPARATOR + tagname + '.' + extension)
        else:
            return os.path.join(dirname, basename + BETWEEN_TAG_SEPARATOR + tagname)


def removing_tag_from_filename(filename, tagname):
    """
    Returns string of file name with tagname removed as tag.

    @param filename: an unicode string containing a file name
    @param tagname: an unicode string containing a tag name
    @param return: an unicode string of filename without tagname
    """

    assert(filename.__class__ == str)
    assert(tagname.__class__ == str)

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
            extension = ''
        else:
            extension = '.' + extension

        if len(tags) < 2:
            logging.debug("given tagname is the only tag -> remove all tags and FILENAME_TAG_SEPARATOR as well")
            return old_filename + extension
        else:
            # still tags left
            return old_filename + FILENAME_TAG_SEPARATOR + \
                BETWEEN_TAG_SEPARATOR.join([tag for tag in tags if tag != tagname]) + extension


def extract_tags_from_argument(argument):
    """
    @param argument: string containing one or more tags
    @param return: a list of unicode tags
    """

    assert(argument.__class__ == str)

    if len(argument) > 0:
        return argument.split(str(BETWEEN_TAG_SEPARATOR))
    else:
        return False


def extract_filenames_from_argument(argument):
    """
    @param argument: string containing one or more file names
    @param return: a list of unicode file names
    """

    # FIXXME: currently works without need to convertion but add check later on
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


def print_item_transition(path, source, destination, transition):
    """
    Returns true if item is member of at least one list in list_of_lists.

    @param path: string containing the path to the files
    @param source: string of basename of filename before transition
    @param destination: string of basename of filename after transition or target
    @param transision: string which determines type of transision: ("add", "delete", "link")
    @param return: N/A
    """

    transition_description = ''
    if transition == 'add':
        transition_description = 'renaming'
    elif transition == 'delete':
        transition_description = 'renaming'
    elif transition == 'link':
        transition_description = 'linking'
    else:
        print("ERROR: print_item_transition(): unknown transition parameter: \"" + transition + "\"")

    style_destination = colorama.Style.BRIGHT + colorama.Back.GREEN + colorama.Fore.BLACK
    destination = style_destination + destination + colorama.Style.RESET_ALL

    if 15 + len(transition_description) + (2 * max_file_length) < TTY_WIDTH:
        # probably enough space: screen output with one item per line

        source_width = max_file_length

        source = source
        arrow_left = colorama.Style.DIM + '――'
        arrow_right = '―→'
        print("  {0:<{width}s}   {1:s}{2:s}{3:s}   {4:s}".format(source, arrow_left, transition_description, arrow_right, destination, width=source_width))

    else:
        # for narrow screens (and long file names): split up item source/destination in two lines

        print(" {0:<{width}s}  \"{1:s}\"".format(transition_description, source, width=len(transition_description)))
        print(" {0:<{width}s}     ⤷   \"{1:s}\"".format(' ', destination, width=len(transition_description)))


def find_unique_alternative_to_file(filename):
    """
    @param filename: string containing one file name which does not exist
    @param return: False or filename that starts with same substring within this directory
    """

    logging.debug("file type error for file [%s] in folder [%s]: file type: is file? %s  -  is dir? %s  -  is mount? %s" %
                  (filename, os.getcwd(), str(os.path.isfile(filename)), str(os.path.isdir(filename)), str(os.path.islink(filename))))
    logging.debug("trying to find a unique file starting with the same characters ...")

    path = os.path.dirname(filename)
    if len(path) < 1:
        path = os.getcwd()

    # get existing filenames of the directory of filename:
    existingfilenames = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        existingfilenames.extend(filenames)
        break

    # reduce filename one character by character from the end and see if any
    # existing filename starts with this substring:
    matchingfilenames = []
    filenamesubstring = filename  # start with the whole filename to match cases where filename is a complete substring
    for i in range(len(filename)):
        for existingfilename in existingfilenames:
            # logging.debug('Checking substring [%s] with existing filename [%s]' % (filenamesubstring, existingfilename))
            if existingfilename.startswith(filenamesubstring):
                matchingfilenames.append(existingfilename)
        if matchingfilenames:
            logging.debug('For substring [%s] I found existing filenames: %s' % (filenamesubstring, str(matchingfilenames)))
            if len(matchingfilenames) > 1:
                logging.debug('Can not use an alternative filename since it is not unique')
            break
        filenamesubstring = filename[:-(i + 1)]  # get rid of the last character of filename, one by one

    # see if the list of matchingfilenames is unique (contains one entry)
    if len(matchingfilenames) == 1:
        return matchingfilenames[0]
    else:
        return False


def is_nonbroken_symlink_file(filename):
    """
    Returns true if the filename is a non-broken symbolic link and not just an ordinary file. False, for any other case like no file at all.

    @param filename: an unicode string containing a file name
    @param return: bookean
    """

    if os.path.isfile(filename):
        if os.path.islink(filename):
            return True
    else:
        return False


def get_link_source_file(filename):
    """
    Return a string representing the path to which the symbolic link points.

    @param filename: an unicode string containing a file name
    @param return: file path string
    """

    assert(os.path.islink(filename))
    return os.readlink(filename)


def is_broken_link(name):
    """
    This function determines if the given name points to a file that is a broken link.
    It returns False for any other cases such as non existing files and so forth.

    @param name: an unicode string containing a file name
    @param return: boolean
    """

    if os.path.isfile(name) or os.path.isdir(name):
        return False

    try:
        return not os.path.exists(os.readlink(name))
    except FileNotFoundError:
        return False


def split_up_filename(filename):
    """
    Returns separate strings for the given filename.

    @param filename: an unicode string containing a file name
    @param return: filename with absolute path, pathname, basename
    """

    basename = os.path.basename(filename)
    dirname = os.path.abspath(os.path.dirname(filename))
    return os.path.join(dirname, basename), dirname, basename


def handle_file_and_symlink_source_if_found(orig_filename, tags, do_remove, do_filter, dryrun):
    """
    @param orig_filename: string containing one file name
    @param tags: list containing one or more tags
    @param do_remove: boolean which defines if tags should be added (False) or removed (True)
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value or new filename
    """

    logging.debug("handle_file_and_symlink_source_if_found(\"" + orig_filename + "\") …  " + '★' * 20)

    if os.path.isdir(orig_filename):
        logging.warning("Skipping directory \"%s\" because this tool only renames file names." % orig_filename)
        return

    filename, dirname, basename = split_up_filename(orig_filename)
    global list_of_symlink_directories

    if not (os.path.isfile(filename) or os.path.islink(filename)):
        logging.debug('handle_file_and_symlink_source_if_found: this is no regular file nor a symlink; looking for an alternative file that starts with same substring …')

        # try to find unique alternative file:
        alternative_filename = find_unique_alternative_to_file(filename)

        if not alternative_filename:
            logging.debug('handle_file_and_symlink_source_if_found: Could not locate alternative basename that starts with same substring')
            logging.error("Skipping \"%s\" because this tool only renames existing file names." % filename)
            return
        else:
            logging.info("Could not find basename \"%s\" but found \"%s\" instead which starts with same substring ..." %
                         (filename, alternative_filename))
            filename, dirname, basename = split_up_filename(orig_filename)

    if dirname:
        logging.debug("handle_file_and_symlink_source_if_found: changing to dir \"%s\"" % dirname)
        os.chdir(dirname)
    else:
        logging.debug("handle_file_and_symlink_source_if_found: no dirname found")

    # if basename is a symbolic link and has same basename, tag the source file as well:
    if TAG_SYMLINK_ORIGINALS_WHEN_TAGGING_SYMLINKS and is_nonbroken_symlink_file(filename):
        logging.debug('handle_file_and_symlink_source_if_found: file is a non-broken symlink and TAG_SYMLINK_ORIGINALS_WHEN_TAGGING_SYMLINKS is set')

        old_source_filename, old_source_dirname, old_source_basename = split_up_filename(get_link_source_file(basename))

        if old_source_basename == basename:
            logging.debug('handle_file_and_symlink_source_if_found: symlink "' + filename +
                          '" has same basename as its source file "' + old_source_filename + '"')

            new_source_basename = handle_file_and_symlink_source_if_found(old_source_filename, tags, do_remove, do_filter, dryrun)
            new_source_filename = os.path.join(old_source_dirname, new_source_basename)

            if old_source_basename != new_source_basename:
                logging.debug('handle_file_and_symlink_source_if_found: Tagging the symlink-destination file of "' + basename + '" ("' +
                             old_source_filename + '") as well …')

                if options.dryrun:
                    logging.debug('handle_file_and_symlink_source_if_found: I would re-link the old sourcefilename "'
                                  + old_source_filename +
                                  '" to the new one "' + new_source_filename + '"')
                else:
                    logging.debug('handle_file_and_symlink_source_if_found: re-linking symlink "' + os.path.join(dirname, basename) +
                                  '" from the old sourcefilename "' +
                                  old_source_filename + '" to the new one "' + new_source_filename + '"')
                    os.remove(filename)
                    create_link(new_source_filename, filename)
            else:
                logging.debug('handle_file_and_symlink_source_if_found: The old sourcefilename "' + old_source_filename +
                              '" did not change. So therefore I don\'t re-link.')
        else:
            logging.debug('handle_file_and_symlink_source_if_found: The file "' + filename +
                          '" is a symlink to "' + old_source_filename +
                          '" but they two do have different basenames. Therefore I ignore the original file.')
        os.chdir(dirname)  # go back to original dir after handling symlinks of different directories
    else:
        logging.debug('handle_file_and_symlink_source_if_found: file is not a non-broken symlink (' +
                      repr(is_nonbroken_symlink_file(basename)) + ') or TAG_SYMLINK_ORIGINALS_WHEN_TAGGING_SYMLINKS is not set')

    # after handling potential symlink originals, I now handle the file we were talking about in the first place:
    new_filename = handle_file(filename, tags, do_remove, do_filter, dryrun)

    return new_filename


def create_link(source, destination):
    """
    On non-Windows systems, a symbolic link is created that links
    source (existing file) to destination (the new symlink). On
    Windows systems a lnk-file is created instead.

    The reason why we have to use really poor performing error-prone
    "lnk"-files instead of symlinks on Windows is that you're required
    to have administration permission so that "SeCreateSymbolicLinkPrivilege"
    is granted. Sorry for this lousy operating system.
    See: https://docs.python.org/3/library/os.html#os.symlink for details about that.

    This is the reason why the "--tagrees" option does perform really bad
    on Windows. And "really bad" means factor 10 to 1000. I measured it.

    @param source: a file name of the source, an existing file
    @param destination: a file name for the link which is about to be created
    """

    if platform.system() == 'Windows':
        # do lnk-files instead of symlinks:
        shell = win32com.client.Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(destination + '.lnk')
        shortcut.Targetpath = source
        shortcut.WorkingDirectory = os.path.dirname(destination)
        # shortcut.IconLocation: is derived from the source file
        shortcut.save()

    else:
        # for normal operating systems, use good old high-performing symbolic links:
        os.symlink(source, destination)


def handle_file(orig_filename, tags, do_remove, do_filter, dryrun):
    """
    @param orig_filename: string containing one file name with absolute path
    @param tags: list containing one or more tags
    @param do_remove: boolean which defines if tags should be added (False) or removed (True)
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value or new filename
    """

    assert(orig_filename.__class__ == str)
    assert(tags.__class__ == list)
    if do_remove:
        assert(do_remove.__class__ == bool)
    if do_filter:
        assert(do_filter.__class__ == bool)
    if dryrun:
        assert(dryrun.__class__ == bool)

    filename, dirname, basename = split_up_filename(orig_filename)

    logging.debug("handle_file(\"" + filename + "\") …   with woring dir \"" + os.getcwd() + "\"")

    if do_filter:
        print_item_transition(dirname, basename, TAGFILTER_DIRECTORY, transition='link')
        if not dryrun:
            create_link(filename, os.path.join(TAGFILTER_DIRECTORY, basename))

    else:  # add or remove tags:
        new_basename = basename
        logging.debug('handle_file: set new_basename [' + new_basename + '] according to parameters (initialization)')

        for tagname in tags:
            if do_remove:
                new_basename = removing_tag_from_filename(new_basename, tagname)
                logging.debug('handle_file: set new_basename [' + new_basename + '] when do_remove')
            elif tagname[0] == '-':
                new_basename = removing_tag_from_filename(new_basename, tagname[1:])
                logging.debug('handle_file: set new_basename [' + new_basename + '] when tag starts with a minus')
            else:
                # FIXXME: not performance optimized for large number of unique tags in many lists:
                tag_in_unique_tags, matching_unique_tag_list = item_contained_in_list_of_lists(tagname, unique_tags)

                if tagname != tag_in_unique_tags:
                    new_basename = adding_tag_to_filename(new_basename, tagname)
                    logging.debug('handle_file: set new_basename [' + new_basename + '] when tagname != tag_in_unique_tags')
                else:
                    # if tag within unique_tags found, and new unique tag is given, remove old tag:
                    # e.g.: unique_tags = (u'yes', u'no') -> if 'no' should be added, remove existing tag 'yes' (and vice versa)
                    # If user enters contradicting tags, only the last one will be applied.
                    # FIXXME: this is an undocumented feature -> please add proper documentation

                    current_filename_tags = extract_tags_from_filename(new_basename)
                    conflicting_tags = list(set(current_filename_tags).intersection(matching_unique_tag_list))
                    logging.debug("handle_file: found unique tag %s which require old unique tag(s) to be removed: %s" % (tagname, repr(conflicting_tags)))
                    for conflicting_tag in conflicting_tags:
                        new_basename = removing_tag_from_filename(new_basename, conflicting_tag)
                        logging.debug('handle_file: set new_basename [' + new_basename + '] when conflicting_tag in conflicting_tags')
                    new_basename = adding_tag_to_filename(new_basename, tagname)
                    logging.debug('handle_file: set new_basename [' + new_basename + '] after adding_tag_to_filename()')

        new_filename = os.path.join(dirname, new_basename)

        if do_remove:
            transition = 'delete'
        else:
            transition = 'add'

        if basename != new_basename:

            list_of_symlink_directories.append(dirname)

            if len(list_of_symlink_directories) > 1:
                logging.debug('new_filename is a symlink. Screen output of transistion gets postponed to later on.')
            elif not options.quiet:
                print_item_transition(dirname, basename, new_basename, transition=transition)

            if not dryrun:
                os.rename(filename, new_filename)

        return new_filename


def add_tag_to_countdict(tag, tags):
    """
    Takes a tag (string) and a dict. Returns the dict with count value increased by one

    @param tag: a (unicode) string
    @param tags: dict of tags
    @param return: dict of tags with incremented counter of tag (or 0 if new)
    """

    assert(tag.__class__ == str)
    assert(tags.__class__ == dict)

    if tag in list(tags.keys()):
        tags[tag] = tags[tag] + 1
    else:
        tags[tag] = 1

    return tags


def extract_iso_datestamp_from_filename(filename):
    """
    Returns array of year, month, day if filename starts with
    YYYY-MM-DD datestamp. Returns empty array else.
    """

    components = re.match(YYYY_MM_DD_PATTERN, filename)
    if components:
        return [components.group(1), components.group(2), components.group(3)]
    else:
        return []


def get_files_with_metadata(startdir=os.getcwd(), use_cache=True):
    """
    Traverses the file system starting with given directory,
    returns list: filename and metadata-dict:

    The result is stored in the global dict as
    cache_of_files_with_metadata[startdir] with dict elements like:
      'filename': '2018-03-18 this is a file name -- tag1 tag2.txt',
      'filetags': ['tag1', 'tag2'],
      'path': '/this/is -- tag1/the -- tag3/path',
      'alltags': ['tag1', 'tag2', 'tag3'],
      'ctime': time.struct_time,
      'datestamp': ['2018', '03', '18'],

    @param use_cache: FOR FUTURE USE; default = True
    @param return: list of filenames and metadata-dict
    """

    global cache_of_files_with_metadata

    assert(os.path.isdir(startdir))

    logging.debug('get_files_with_metadata called with startdir [%s], cached startdirs [%s]' % (startdir, str(len(list(cache_of_files_with_metadata.keys())))))

    if use_cache and len(cache_of_files_with_metadata) > 0:
        logging.debug("found " + str(len(cache_of_files_with_metadata)) + " files in cache for files")
        return cache_of_files_with_metadata

    else:

        cache = []
        for root, dirs, files in os.walk(startdir):

            # logging.debug('get_files_with_metadata: root [%s]' % root)  # LOTS of debug output
            for filename in files:

                absfilename = os.path.abspath(os.path.join(root, filename))
                # logging.debug('get_files_with_metadata: file [%s]' % absfilename)  # LOTS of debug output
                path, basename = os.path.split(absfilename)
                if os.path.islink(absfilename):
                    # link files do not have ctime and must be dereferenced before. However, they can link to another link file or they can be broken.
                    # Design decision: ignoring link files alltogether. Their source should speak for themselves.
                    logging.debug('get_files_with_metadata: file [%s] is link to [%s] and gets ignored here' %
                                  (absfilename,
                                   os.path.join(os.path.dirname(absfilename), os.readlink(absfilename))))
                    continue
                else:
                    ctime = time.localtime(os.path.getctime(absfilename))

                cache.append({
                    'filename': basename,
                    'filetags': extract_tags_from_filename(basename),
                    'path': path,
                    'alltags': extract_tags_from_path(absfilename),
                    'ctime': ctime,
                    'datestamp': extract_iso_datestamp_from_filename(basename)
                })

            # Enable recursive directory traversal for specific options:
            if not (options.recursive and (options.list_tags_by_alphabet or
                                           options.list_tags_by_number or
                                           options.list_unknown_tags or
                                           options.tag_gardening)):
                break  # do not loop

        logging.debug("Writing " + str(len(cache)) + " files in cache for directory: " + startdir)
        if use_cache:
            cache_of_files_with_metadata[startdir] = cache
        return cache


def get_tags_from_files_and_subfolders(startdir=os.getcwd(), use_cache=True):
    """
    Traverses the file system starting with given directory,
    returns dict of all tags (including starttags) of all file.
    Uses cache_of_files_with_metadata of use_cache is true and
    cache is populated with same startdir.

    @param use_cache: FOR FUTURE USE
    @param return: dict of tags and their number of occurrence
    """

    # add ", starttags=False" to parameters to enable this feature in future
    starttags = False

    assert(os.path.isdir(startdir))

    if not starttags:
        tags = {}
    else:
        assert(starttags.__class__ == dict)
        tags = starttags

    global cache_of_tags_by_folder

    logging.debug('get_tags_from_files_and_subfolders called with startdir [%s], cached startdirs [%s]' % (startdir, str(len(list(cache_of_tags_by_folder.keys())))))

    if use_cache and startdir in list(cache_of_tags_by_folder.keys()):
        logging.debug("found " + str(len(cache_of_tags_by_folder[startdir])) + " tags in cache for directory: " + startdir)
        return cache_of_tags_by_folder[startdir]

    elif use_cache and startdir in cache_of_files_with_metadata.keys():
        logging.debug('using cache_of_files_with_metadata instead of traversing file system again')
        cachedata = cache_of_files_with_metadata[startdir]

        # FIXXME: check if tags are extracted from dirnames as in traversal algorithm below

        for entry in cachedata:
            for tag in entry['alltags']:
                tags = add_tag_to_countdict(tag, tags)

    else:

        for root, dirs, files in os.walk(startdir):

            # logging.debug('get_tags_from_files_and_subfolders: root [%s]' % root)  # LOTS of debug output

            for filename in files:
                for tag in extract_tags_from_filename(filename):
                    tags = add_tag_to_countdict(tag, tags)

            for dirname in dirs:
                for tag in extract_tags_from_filename(dirname):
                    tags = add_tag_to_countdict(tag, tags)

            # Enable recursive directory traversal for specific options:
            if not (options.recursive and (options.list_tags_by_alphabet or
                                           options.list_tags_by_number or
                                           options.list_unknown_tags or
                                           options.tag_gardening)):
                break  # do not loop

    logging.debug("Writing " + str(len(list(tags.keys()))) + " tags in cache for directory: " + startdir)
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

    assert(tag.__class__ == str)
    assert(tags.__class__ == list)

    similar_tags = difflib.get_close_matches(tag, tags, n=999, cutoff=0.7)
    close_but_not_exact_matches = []

    # omit exact matches   FIXXME: this can be done in one eloquent line -> refactor
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

    # determine maximum length of strings for formatting:
    if len(tag_dict) > 0:
        maxlength_tags = max(len(s) for s in list(tag_dict.keys())) + len(HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)
        maxlength_count = len(str(abs(max(tag_dict.values()))))
    else:
        maxlength_tags = len(HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)
        maxlength_count = 5

    if maxlength_count < 5:
        maxlength_count = 5

    hint_for_being_in_vocabulary = ''
    similar_tags = ''
    if vocabulary:
        print("\n  (Tags marked with \"" + HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE + "\" appear in your vocabulary.)")
    print("\n {0:{1}} : {2:{3}}".format('count', maxlength_count, 'tag', maxlength_tags))
    print(" " + '-' * (maxlength_tags + maxlength_count + 7))
    for tuple in sorted(list(tag_dict.items()), key=operator.itemgetter(sort_index)):
        # sort dict of (tag, count) according to sort_index

        if vocabulary and tuple[0] in vocabulary:
            hint_for_being_in_vocabulary = HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
        else:
            hint_for_being_in_vocabulary = ''

        similar_tags_list = []
        if vocabulary and print_similar_vocabulary_tags:
            tags_for_comparing = list(set(tag_dict.keys()).union(set(vocabulary)))  # unified elements of both lists
            similar_tags_list = find_similar_tags(tuple[0], tags_for_comparing)
            if similar_tags_list:
                similar_tags = '      (similar to:  ' + ', '.join(similar_tags_list) + ')'
            else:
                similar_tags = ''
        else:
            similar_tags = ''

        if (print_only_tags_with_similar_tags and similar_tags_list) or not print_only_tags_with_similar_tags:
            print(" {0:{1}} : {2:{3}}   {4}".format(tuple[1], maxlength_count, tuple[0] + hint_for_being_in_vocabulary, maxlength_tags, similar_tags))

    print('')


def print_tag_set(tag_set, vocabulary=False, print_similar_vocabulary_tags=False):
    """
    Takes a set which holds tag names and prints it to stdout.
    Tags that appear also in the vocabulary get marked in the output.

    @param tag_set: a set holding tags
    @param vocabulary: array of tags from controlled vocabulary or False
    @param print_similar_vocabulary_tags: if a vocabulary is given and tags are similar to it, print a list of them
    """

    # determine maximum length of strings for formatting:
    maxlength_tags = max(len(s) for s in tag_set) + len(HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)

    hint_for_being_in_vocabulary = ''
    if vocabulary:
        print("\n  (Tags marked with \"" + HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE + "\" appear in your vocabulary.)\n")

    for tag in sorted(tag_set):

        if vocabulary and tag in vocabulary:
            hint_for_being_in_vocabulary = HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
        else:
            hint_for_being_in_vocabulary = ''

        if vocabulary and print_similar_vocabulary_tags:
            tags_for_comparing = list(tag_set.union(set(vocabulary)))  # unified elements of both lists
            similar_tags_list = find_similar_tags(tag, tags_for_comparing)
            if similar_tags_list:
                similar_tags = '      (similar to:  ' + ', '.join(similar_tags_list) + ')'
            else:
                similar_tags = ''
        else:
            similar_tags = ''

        print("  {0:{1}}   {2}".format(tag + hint_for_being_in_vocabulary, maxlength_tags, similar_tags))

    print('')


def list_unknown_tags(file_tag_dict):
    """
    Traverses the file system, extracts all tags, prints tags that are found in file names which are not found in the controlled vocabulary file .filetags

    @param return: dict of tags (if max_tag_count is set, returned entries are set accordingly)
    """

    vocabulary = locate_and_parse_controlled_vocabulary(False)

    # filter out known tags from tag_dict
    unknown_tag_dict = {key: value for key, value in list(file_tag_dict.items()) if key not in vocabulary}

    if unknown_tag_dict:
        print_tag_dict(unknown_tag_dict, vocabulary)
    else:
        print("\n  " + str(len(file_tag_dict)) + " different tags were found in file names which are all" +
              " part of your .filetags vocabulary (consisting of " + str(len(vocabulary)) + " tags).\n")

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

    files_with_metadata = get_files_with_metadata(startdir=os.getcwd())  # = cache_of_files_with_metadata of current dir
    tag_dict = get_tags_from_files_and_subfolders(startdir=os.getcwd())
    if not tag_dict:
        print("\nNo file containing tags found in this folder hierarchy.\n")
        return

    print("\nYou have used " + str(len(tag_dict)) + " tags in total.\n")

    number_of_files = len(files_with_metadata)
    print("\nNumber of total files:                           " + str(number_of_files))

    def str_percentage(fraction, total):
        "returns a string containing the percentage of the fraction wrt the total"
        assert(type(fraction) == int)
        assert(type(total) == int)
        if total == 0:
            return "0%"  # avoid division by zero
        else:
            return str(round(100*fraction/total, 1)) + '%'

    files_without_alltags = [x for x in files_with_metadata if not x['alltags']]
    num_files_without_alltags = len(files_without_alltags)

    files_without_filetags = [x for x in files_with_metadata if not x['filetags']]
    num_files_without_filetags = len(files_without_filetags)

    num_files_with_alltags = number_of_files - len(files_without_alltags)

    files_with_filetags = [x for x in files_with_metadata if x['filetags']]
    num_files_with_filetags = len(files_with_filetags)

    print("\nNumber of files without tags including pathtags: " + str(num_files_without_alltags) +
          "   (" + str_percentage(num_files_without_alltags, number_of_files) + " of total files)")

    print("Number of files without filetags:                " + str(num_files_without_filetags) +
          "   (" + str_percentage(num_files_without_filetags, number_of_files) + " of total files)")

    print("Number of files with filetags:                   " + str(num_files_with_filetags) +
          "   (" + str_percentage(num_files_with_filetags, number_of_files) + " of total files)")

    top_10_tags = sorted(tag_dict.items(), key=lambda x:x[1], reverse=True)[:10]  # e.g.: [('v', 5), ('tag1', 4), ('tag4', 4)]
    if len(top_10_tags) > 0:
        print('\nTop 10 tags:')
        longest_tag = len(max([x[0] for x in top_10_tags], key=len))
        for item in top_10_tags:
            print('   {:<{}}  •  {:>{}} tagged file(s)   = {:>5} of tagged files'.format(
                item[0],
                longest_tag,
                item[1],
                6,
                str_percentage(item[1], num_files_with_alltags)))

    if vocabulary:
        print('\n\nYour controlled vocabulary is defined in ' + controlled_vocabulary_filename +
              ' and contains ' + str(len(vocabulary)) + ' tags.\n')

        vocabulary_tags_not_used = set(vocabulary) - set(tag_dict.keys())
        if vocabulary_tags_not_used:
            print("\nTags from your vocabulary which you didn't use:\n")
            print_tag_set(vocabulary_tags_not_used)

        tags_not_in_vocabulary = set(tag_dict.keys()) - set(vocabulary)
        if tags_not_in_vocabulary:
            print("\nTags you used that are not in the vocabulary:\n")
            print_tag_set(tags_not_in_vocabulary)

        if unique_tags and len(unique_tags) > 0:
            # There are mutually exclusive tags defined in the controlled vocabulary
            for taggroup in unique_tags:
                # iterate over mutually exclusive tag groups one by one

                if taggroup == UNIQUE_TAG_TESTSTRINGS:
                    continue
                if len(set(tag_dict.keys()).intersection(set(taggroup))) > 0:
                    files_with_any_tag_from_taggroup = [x for x in
                                                        files_with_metadata if
                                                        len(set(x['alltags']).intersection(set(taggroup))) > 0]
                    num_files_with_any_tag_from_taggroup = len(files_with_any_tag_from_taggroup)
                    print('\nTag group ' + str(taggroup) + ":\n   Number of files with tag from tag group: " +
                          str(num_files_with_any_tag_from_taggroup) +
                          "   (" + str_percentage(num_files_with_any_tag_from_taggroup, num_files_with_alltags) +
                          " of tagged files)")

                    longest_tagname = max(taggroup, key=len)
                    for tag in taggroup:
                        files_with_tag_from_taggroup = [x for x in files_with_metadata if tag in x['alltags']]
                        num_files_with_tag_from_taggroup = len(files_with_tag_from_taggroup)
                        if num_files_with_tag_from_taggroup > 0:
                            print('   {:<{}}  •  {:>{}} tagged file(s)   = {:>5} of tag group'.format(
                                tag,
                                len(longest_tagname),
                                str(num_files_with_tag_from_taggroup),
                                len(str(num_files_with_any_tag_from_taggroup)),
                                str_percentage(num_files_with_tag_from_taggroup, num_files_with_any_tag_from_taggroup)))
                        else:
                            print('   "' + tag + '": Not used')
                else:
                    print('Tag group ' + str(taggroup) + ': Not used')

    print("\nTags that appear only once are most probably typos or you have forgotten them:")
    tags_only_used_once_dict = {key: value for key, value in list(tag_dict.items()) if value < 2}
    print_tag_dict(tags_only_used_once_dict, vocabulary, sort_index=0, print_only_tags_with_similar_tags=False)

    print("\nTags which have similar other tags are probably typos or plural/singular forms of others:")
    tags_for_comparing = list(set(tag_dict.keys()).union(set(vocabulary)))  # unified elements of both lists
    only_similar_tags_by_alphabet_dict = {key: value for key, value in list(tag_dict.items())
                                          if find_similar_tags(key, tags_for_comparing)}
    print_tag_dict(only_similar_tags_by_alphabet_dict, vocabulary, sort_index=0, print_similar_vocabulary_tags=True)

    tags_only_used_once_set = set(tags_only_used_once_dict.keys())
    only_similar_tags_by_alphabet_set = set(only_similar_tags_by_alphabet_dict.keys())
    tags_in_both_outputs = tags_only_used_once_set.intersection(only_similar_tags_by_alphabet_set)

    if tags_in_both_outputs != set([]):
        print("\nIf tags appear in both lists from above (only once and similar to others), they most likely\nrequire your attention:")
        print_tag_set(tags_in_both_outputs, vocabulary=vocabulary, print_similar_vocabulary_tags=True)


def locate_file_in_cwd_and_parent_directories(startfile, filename):
    """This method looks for the filename in the folder of startfile and its
    parent folders. It returns the file name of the first file name found.

    @param startfile: file whose path is the starting point; if False, the working path is taken
    @param filename: string of file name to look for
    @param return: file name found
    """

    if startfile and os.path.isfile(startfile) and os.path.isfile(
            os.path.join(os.path.dirname(os.path.abspath(startfile)), filename)):
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
            starting_dir = os.getcwd()
            logging.debug('no startfile found; using cwd as starting_dir [%s] ......' % (starting_dir))
        parent_dir = os.path.abspath(os.path.join(starting_dir, os.pardir))
        logging.debug('looking for \"%s\" in directory \"%s\" .......' % (filename, parent_dir))
        while parent_dir != os.getcwd():
            os.chdir(parent_dir)
            filename_to_look_for = os.path.abspath(os.path.join(os.getcwd(), filename))
            if os.path.isfile(filename_to_look_for):
                logging.debug('found \"%s\" in directory \"%s\" ........' % (filename, parent_dir))
                os.chdir(starting_dir)
                return filename_to_look_for
            parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
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
        filename = locate_file_in_cwd_and_parent_directories(os.getcwd(), CONTROLLED_VOCABULARY_FILENAME)

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
                            # *also* append unique tags to general tag list:
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
            hint_string = "Previously used tags in this directory:"
        else:
            hint_string = "Top nine previously used tags in this directory:"
    elif tags_get_linked:
        if len(tag_list) < 9:
            hint_string = "Used tags in this directory:"
        else:
            hint_string = "Top nine used tags in this directory:"
    else:
        if len(tag_list) < 9:
            hint_string = "Possible tags to be removed:"
        else:
            hint_string = "Top nine possible tags to be removed:"
    print("\n  " + colorama.Style.DIM + hint_string + colorama.Style.RESET_ALL)

    count = 1
    list_of_tag_hints = []
    for tag in tag_list:
        list_of_tag_hints.append(tag + ' (' + str(count) + ')')
        count += 1
    try:
        print('    ' + ' ⋅ '.join(list_of_tag_hints))
    except UnicodeEncodeError:
        logging.debug('ERROR: I got an UnicodeEncodeError when displaying "⋅" (or list_of_tag_hints) ' +
                      'but I re-try with "|" as a separator instead ...')
        print('    ' + ' | '.join(list_of_tag_hints))
    print('')  # newline at end


def check_for_possible_shortcuts_in_entered_tags(usertags, list_of_shortcut_tags):
    """
    Returns tags if the only tag is not a shortcut (entered as integer).
    Returns a list of corresponding tags if it's an integer.

    @param usertags: list of entered tags from the user, e.g., [u'23']
    @param list_of_shortcut_tags: list of possible shortcut tags, e.g., [u'bar', u'folder1', u'baz']
    @param return: list of tags which were meant by the user, e.g., [u'bar', u'baz']
    """

    assert(usertags.__class__ == list)
    assert(list_of_shortcut_tags.__class__ == list)

    foundtags = []  # collect all found tags which are about to return from this function

    for currenttag in usertags:
        try:
            logging.debug('tag is an integer; stepping through the integers')
            found_shortcut_tags_within_currenttag = []  # collects the shortcut tags of a (single) currenttag
            for character in list(currenttag):
                # step through the characters and find out if it consists of valid indexes of the list_of_shortcut_tags:
                if currenttag in foundtags:
                    # we already started to step through currenttag, character by character, and found out (via
                    # IndexError) that the whole currenttag is a valid tag and added it already to the tags-list.
                    # Continue with the next tag from the user instead of continue to step through the characters:
                    continue
                try:
                    # try to append the index element to the list of found shortcut tags so far (and risk an IndexError):
                    found_shortcut_tags_within_currenttag.append(list_of_shortcut_tags[int(character) - 1])
                except IndexError:
                    # IndexError tells us that the currenttag contains a character which is not a valid index of
                    # list_of_shortcut_tags. Therefore, the whole currenttag is a valid tag and not a set of
                    # indexes for shortcuts:
                    foundtags.append(currenttag)
                    continue
            if currenttag not in foundtags:
                # Stepping through all characters without IndexErrors
                # showed us that all characters were valid indexes for
                # shortcuts and therefore extending those shortcut tags to
                # the list of found tags:
                logging.debug('adding shortcut tags of number(s) %s' % currenttag)
                foundtags.extend(found_shortcut_tags_within_currenttag)
        except ValueError:
            # ValueError tells us that one character is not an integer. Therefore, the whole currenttag is a valid tag:
            logging.debug('whole tag is a normal tag')
            foundtags.append(currenttag)

    return foundtags


def get_upto_nine_keys_of_dict_with_highest_value(mydict, list_of_tags_to_omit=[]):
    """
    Takes a dict, sorts it according to their values, and returns up to nine
    values with the highest values.

    Example1: { "key2":45, "key1": 33} -> [ "key1", "key2" ]
    Example2: { "key2":45, "key1": 33, "key3": 99} list_of_tags_to_omit=["key3"] -> [ "key1", "key2" ]

    @param mydict: dictionary holding keys and values
    @param list_of_tags_to_omit: list of strings that should not be part of the returned list
    @param return: list of up to top nine keys according to the rank of their values
    """

    assert(mydict.__class__ == dict)

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

    style = colorama.Back.BLACK + colorama.Fore.GREEN

    length = len(tags)
    visual = "         " + style + ".---" + '-' * length + "--," + colorama.Style.RESET_ALL + " \n" + \
             "        " + style + "| o  " + colorama.Style.BRIGHT + tags + colorama.Style.NORMAL + "  |" + colorama.Style.RESET_ALL + " \n" + \
             "         " + style + "`---" + '-' * length + "--'" + colorama.Style.RESET_ALL + " "

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

    completionhint = ''
    if vocabulary and len(vocabulary) > 0:

        assert(vocabulary.__class__ == list)

        # Register our completer function
        readline.set_completer(SimpleCompleter(vocabulary).complete)

        # Use the tab key for completion
        readline.parse_and_bind('tab: complete')

        completionhint = '; complete %s tags with TAB' % str(len(vocabulary))

    logging.debug("len(files) [%s]" % str(len(options.files)))
    logging.debug("files: %s" % str(options.files))

    print("                 ")
    print("Please enter tags" + colorama.Style.DIM + ", separated by \"" + BETWEEN_TAG_SEPARATOR + "\"; abort with Ctrl-C" +
          completionhint + colorama.Style.RESET_ALL)
    print("                     ")
    print(_get_tag_visual(tags_for_visual))
    print("                     ")

    if len(upto9_tags_for_shortcuts) > 0:
        print_tag_shortcut_with_numbers(upto9_tags_for_shortcuts,
                                        tags_get_added=(not options.remove and not options.tagfilter),
                                        tags_get_linked=options.tagfilter)

    logging.debug("interactive mode: asking for tags ...")
    entered_tags = input(colorama.Style.DIM + 'Tags: ' + colorama.Style.RESET_ALL).strip()
    tags_from_userinput = extract_tags_from_argument(entered_tags)

    if not tags_from_userinput:
        logging.info("no tags given, exiting.")
        sys.stdout.flush()
        sys.exit(0)
    else:
        if len(upto9_tags_for_shortcuts) > 0:
            # check if user entered number shortcuts for tags to be removed:
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
        if options.recursive:
            files.extend([os.path.join(dirpath, x) for x in filenames])
        else:
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


def assert_empty_tagfilter_directory(directory):
    """
    Creates non-existent tagfilter directory or deletes and re-creates it.

    @param directory: the directory to use as starting directory
    """

    if options.tagtrees_directory and os.path.isdir(directory) and os.listdir(directory):
        error_exit(13, 'The given tagtrees directory ' + directory + ' is not empty. Aborting here instead ' +
                   'of removing its content without asking. Please free it up yourself and try again.')

    if not os.path.isdir(directory):
        logging.debug('creating non-existent tagfilter directory "%s" ...' % str(directory))
        if not options.dryrun:
            os.makedirs(directory)
    else:
        logging.debug('found old tagfilter directory "%s"; deleting directory ...' % str(directory))
        if not options.dryrun:
            save_import('shutil')  # for removing directories with shutil.rmtree()
            shutil.rmtree(directory)
            logging.debug('re-creating tagfilter directory "%s" ...' % str(directory))
            os.makedirs(directory)
    if not options.dryrun:
        assert(os.path.isdir(directory))


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


def generate_tagtrees(directory, maxdepth, ignore_nontagged, nontagged_subdir, link_missing_mutual_tagged_items):
    """
    This functions is somewhat sophisticated with regards to the background.
    If you're really interested in the whole story behind the
    visualization/navigation of tags using tagtrees, feel free to read [my
    PhD thesis] about it on [the tagstore webpage]. It is surely a piece of
    work I am proud of and the general chapters of it are written so that
    the average person is perfectly well able to follow.

    In short: this function takes the files of the current directory and
    generates hierarchies up to level of `$maxdepth' (by default 2) of all
    combinations of tags, [linking] all files according to their tags.

    Consider having a file like:

    ┌────
    │ My new car -- car hardware expensive.jpg
    └────

    Now you generate the tagtrees, you'll find [links] to this file within
    `~/.filetags', the default target directory: `new/' and `hardware/' and
    `expensive/' and `new/hardware/' and `new/expensive/' and
    `hardware/new/' and so on. You get the idea.

    Therefore, within the folder `new/expensive/' you will find all files
    that have at least the tags "new" and "expensive" in any order. This is
    /really/ cool to have.

    Files of the current directory that don't have any tag at all, are
    linked directly to `~/.filetags' so that you can find and tag them
    easily.

    I personally, do use this feature within my image viewer of choice
    ([geeqie]). I mapped it to `Shift-T' because `Shift-t' is occupied by
    `filetags' for tagging of course. So when I am within my image viewer
    and I press `Shift-T', tagtrees of the currently shown images are
    created. Then an additional image viewer window opens up for me, showing
    the resulting tagtrees. This way, I can quickly navigate through the tag
    combinations to easily interactively filter according to tags.

    Please note: when you are tagging linked files within the tagtrees with
    filetags, only the current link gets updated with the new name. All
    other links to this modified filename within the other directories of
    the tagtrees gets broken. You have to re-create the tagtrees to update
    all the links after tagging files.


    [my PhD thesis] http://Karl-Voit.at/tagstore/downloads/Voit2012b.pdf

    [the tagstore webpage] http://Karl-Voit.at/tagstore/

    [linking] https://en.wikipedia.org/wiki/Symbolic_link

    [links] https://en.wikipedia.org/wiki/Symbolic_link

    [geeqie] http://geeqie.sourceforge.net/

    Valid combinations for ignore_nontagged and nontagged_subdir are:

    | ignore_nontagged | nontagged_subdir | results in ...                                                    |
    |------------------+------------------+-------------------------------------------------------------------|
    | False            | False            | non-linked items are linked to tagtrees root                      |
    | False            | <a string>       | non-linked items are linked to a tagtrees folder named <a string> |
    | True             | False            | non-linked items are ignored                                      |

    @param directory: the directory to use for generating the tagtrees hierarchy
    @param maxdepth: integer which holds the depth to which the tagtrees are generated; keep short to avoid HUGE execution times!
    @param ignore_nontagged: (bool) if True, non-tagged items are ignored and not linked
    @param nontagged_subdir: (string) holds a string containing the sub-directory name to link non-tagged items to
    @param link_missing_mutual_tagged_items: (bool) if True, any item that has a missing tag of any unique_tags entry is linked to a separate directory which is auto-generated from the unique_tags set names
    """

    assert_empty_tagfilter_directory(directory)

    # The boolean ignore_nontagged must be "False" when nontagged_subdir holds a value:
    # valid combinations:
    assert((ignore_nontagged and not nontagged_subdir) or
           (not ignore_nontagged and (not nontagged_subdir or type(nontagged_subdir)==str)))

    # Extract the variables nontagged_item_dest_dir from the valid combinations
    # of nontagged_subdir and ignore_nontagged:
    nontagged_item_dest_dir = False  # ignore non-tagged items
    if nontagged_subdir:
        nontagged_item_dest_dir = os.path.join(directory, nontagged_subdir)
        assert_empty_tagfilter_directory(nontagged_item_dest_dir)
    elif not ignore_nontagged:
        nontagged_item_dest_dir = directory

    try:
        files = get_files_of_directory(os.getcwd())
    except FileNotFoundError:
        error_exit(11, 'When trying to look for files, I could not even find the current working directory. ' + \
                   'Could it be the case that you\'ve tried to generate tagtrees within the directory "' + directory + '"? ' + \
                   'This would be a pity because filetags tends to delete and re-create this directory on each call of this feature. ' + \
                   'Therefore, this directory does not exist after starting filetags and cleaning up the old content of it. ' + \
                   'So it looks like we\'ve got a shot-yourself-in-the-foot situation here … You can imagine that this was not ' + \
                   'even simple to find and catch while testing for me either. Or was it? Make an educated guess. :-)')

    if len(files) == 0 and not options.recursive:
        error_exit(10, 'There is no single file in the current directory "' + os.getcwd() + '". I can\'t create ' + \
                   'tagtrees from nothing. You gotta give me at least something to work with here, dude.')

    # If a controlled vocabulary file is found for the directory where the tagtree
    # should be generated for, we link this file to the resulting tagtrees root
    # directory as well. This way, adding tags using tag completion also works for
    # the linked items.
    controlled_vocabulary_filename = locate_file_in_cwd_and_parent_directories(os.getcwd(), CONTROLLED_VOCABULARY_FILENAME)
    if controlled_vocabulary_filename:
        logging.debug('I found controlled_vocabulary_filename "' + controlled_vocabulary_filename + '" which I\'m going to link to the tagtrees folder')
        if not options.dryrun:
            create_link(os.path.abspath(controlled_vocabulary_filename), os.path.join(directory, CONTROLLED_VOCABULARY_FILENAME))

    else:
        logging.debug('I did not find a controlled_vocabulary_filename')

    logging.info('Creating tagtrees and their symlinks. It may take a while …  (exponentially with respect to number of tags)')

    tags = get_tags_from_files_and_subfolders(startdir=os.getcwd(), use_cache=True)

    # Here, we define a small helper function within a function. Cool,
    # heh? Bet many folks are not aware of those nifty things I know of ;-P
    def create_tagtrees_dir(basedirectory, tagpermutation):
        "Creates (empty) directories of the tagtrees directory structure"

        current_directory = os.path.join(basedirectory, *[x for x in tagpermutation])  # flatten out list of permutations to elements
        # logging.debug('generate_tagtrees: mkdir ' + current_directory)
        if not options.dryrun and not os.path.exists(current_directory):
            os.makedirs(current_directory)

    # this generates a list whose elements (the tags) corresponds to
    # the filenames in the files list:
    tags_of_files = [extract_tags_from_filename(x) for x in files]

    # Firstly, let's iterate over the files, create tagtree
    # directories according to the set of tags from the current file
    # to avoid empty tagtree directories. Then we're going to link the
    # file to its tagtree directories. I'm confident that this is
    # going to be great.

    num_of_links = 0
    for currentfile in enumerate(files):

        tags_of_currentfile = tags_of_files[currentfile[0]]
        filename, dirname, basename = split_up_filename(currentfile[1])


        logging.debug('generate_tagtrees: handling file "' + filename + '" …')

        if len(tags_of_currentfile) == 0:
            # current file has no tags. It gets linked to the
            # nontagged_item_dest_dir folder (if set). This is somewhat handy to find files
            # which are - you guessed right - not tagged yet ;-)

            if ignore_nontagged:
                logging.debug('generate_tagtrees: file "' + filename + '" has no tags and will be ignores because of command line switch.')
            else:
                logging.debug('generate_tagtrees: file "' + filename + '" has no tags. Linking to "' +
                              nontagged_item_dest_dir + '"')
                if not options.dryrun:
                    try:
                        create_link(filename, os.path.join(nontagged_item_dest_dir, basename))
                    except FileExistsError:
                        logging.warning('Untagged file \"' + filename + '\" is already linked: \"' +
                                        os.path.join(nontagged_item_dest_dir, basename) + '\". You must have used the recursive ' +
                                        'option and the sub-tree you\'re generating a tagtree from has two times the ' +
                                        'same filename. I stick with the first one.')
                num_of_links += 1

        else:

            # Here we go: current file has at least one tag. Create
            # its tagtree directories and link the file:

            # logging.debug('generate_tagtrees: permutations for file: "' + filename + '"')
            for currentdepth in range(1, maxdepth+1):
                # logging.debug('generate_tagtrees: currentdepth: ' + str(currentdepth))
                for tagpermutation in itertools.permutations(tags_of_currentfile, currentdepth):

                    # WHAT I THOUGHT:
                    # Creating the directories does not require to iterate
                    # over the different level of depht because
                    # "os.makedirs()" is able to create all parent folders
                    # that are necessary. This spares us a loop.
                    # WHAT I LEARNED:
                    # We *have* to iterate over the depht as well
                    # because when a file has only one tag and the
                    # maxdepth is more than one, we are forgetting
                    # to create all those tagtree directories for this
                    # single tag. Therefore: we need to depth-loop for
                    # creating the directories as well. Bummer.
                    create_tagtrees_dir(directory, tagpermutation)

                    current_directory = os.path.join(directory, *[x for x in tagpermutation])  ## flatten out list of permutations to elements
                    # logging.debug('generate_tagtrees: linking file in ' + current_directory)
                    if not options.dryrun:
                        try:
                            create_link(filename, os.path.join(current_directory, basename))
                        except FileExistsError:
                            logging.warning('Tagged file \"' + filename + '\" is already linked: \"' +
                                            os.path.join(current_directory, basename) + '\". You must have used the recursive ' +
                                            'option and the sub-tree you\'re generating a tagtree from has two times the same ' +
                                            'filename. I stick with the first one.')
                    num_of_links += 1

            if link_missing_mutual_tagged_items:
                for unique_tagset in unique_tags:

                    # Oh yes, I do wish I had solved the default teststring issue in
                    # a cleaner way. Ignore it here hard-coded.
                    if unique_tagset == ['teststring1', 'teststring2']:
                        continue

                    # When there is no intersection between the item tags and the current unique_tagset ...
                    if not set(tags_of_currentfile).intersection(set(unique_tagset)):

                        # ... generate a no-$unique_tagset directory ...
                        no_uniqueset_tag_found_dir = os.path.join(directory, 'no-' + ("-").join(unique_tagset))  # example: "no-draft-final"
                        if not os.path.isdir(no_uniqueset_tag_found_dir):
                            logging.debug('creating non-existent no_uniqueset_tag_found_dir "%s" ...' % str(no_uniqueset_tag_found_dir))
                            if not options.dryrun:
                                os.makedirs(no_uniqueset_tag_found_dir)

                        # ... and link the item into it:
                        if not options.dryrun:
                            try:
                                create_link(filename, os.path.join(no_uniqueset_tag_found_dir, basename))
                            except FileExistsError:
                                logging.warning('Tagged file \"' + filename + '\" is already linked: \"' +
                                                os.path.join(no_uniqueset_tag_found_dir, basename) + '\". I stick with the first one.')
                        num_of_links += 1


    # Brag about how brave I was. And: it also shows the user why the
    # runtime was that long. The number of links grows exponentially
    # with the number of tags. Keep this in mind when tempering with
    # the maxdepth!
    logging.info('Number of symbolic links created in "' + directory + '" for the ' + str(len(files)) + ' files: ' +
                 str(num_of_links) + '  (tagtrees depth is ' + str(maxdepth) + ')')


def start_filebrowser(directory):
    """
    This function starts up the default file browser or the one given in the overriding command line parameter.

    @param directory: the directory to use as starting directory
    """

    if options.filebrowser and options.filebrowser == 'none':
        logging.debug('user overrides filebrowser with "none". Skipping filebrowser alltogether.')
        return

    save_import('subprocess')
    current_platform = platform.system()
    logging.debug('platform.system() is: [' + current_platform + ']')
    if current_platform == 'Linux':
        chosen_filebrowser = DEFAULT_IMAGE_VIEWER_LINUX
        if options.filebrowser:
            chosen_filebrowser = options.filebrowser  # override if given

        if options.dryrun:
            logging.info('DRYRUN: I would now open the file browser "' + chosen_filebrowser + '"')
        else:
            subprocess.call([chosen_filebrowser, directory])

    elif current_platform == 'Windows':
        chosen_filebrowser = DEFAULT_IMAGE_VIEWER_WINDOWS
        if options.filebrowser:
            chosen_filebrowser = options.filebrowser  # override if given

        if options.dryrun:
            logging.info('DRYRUN: I would now open the file browser "' + chosen_filebrowser + '"')
        else:
            if chosen_filebrowser == 'explorer':
                os.system(r'start explorer.exe "' + directory + '"')
            else:
                logging.warning('FIXXME: for Windows, this script only supports the default file browser which is the file explorer.')

    else:
        logging.info('No (default) file browser defined for platform \"' + current_platform + '\".')
        logging.info('Please visit ' + directory + ' to view filtered items.')

def all_files_are_symlink_to_same_directory(files):
    """
    This function returns True when: all files in "files" are symbolic links with same
    filenames in one single directory to a matching set of original filenames in a
    different directory.

    Returns False for any other case

    @param files: list of files
    @param return: boolean
    """

    if files and is_nonbroken_symlink_file(files[0]):
        first_symlink_file_components = split_up_filename(files[0])
        first_original_file_components = split_up_filename(get_link_source_file(files[0]))
    else:
        return False

    for current_file in files:
        if type(current_file) != str:
            logging.info('not str')
            return False
        if not os.path.exists(current_file):
            logging.info('not path exists')
            return False
        current_symlink_components = split_up_filename(current_file)  # 0 = absolute path incl. filename; 1 = dir; 2 = filename
        current_original_components = split_up_filename(get_link_source_file(current_file))
        if current_original_components[1] != first_original_file_components[1] or \
           current_symlink_components[2] != current_original_components[2]:
            logging.info('non matching')
            return False
    return True

def successful_exit():
    logging.debug("successfully finished.")
    sys.stdout.flush()
    sys.exit(0)


def main():
    """Main function"""

    if options.version:
        print(os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_DATE)
        sys.exit(0)

    handle_logging()

    if options.verbose and options.quiet:
        error_exit(1, "Options \"--verbose\" and \"--quiet\" found. " +
                   "This does not make any sense, you silly fool :-)")

    # interactive mode and tags are given
    if options.interactive and options.tags:
        error_exit(3, "I found option \"--tag\" and option \"--interactive\". \n" +
                   "Please choose either tag option OR interactive mode.")

    if options.list_tags_by_number and options.list_tags_by_alphabet:
        error_exit(6, "Please use only one list-by-option at once.")

    if options.tag_gardening and (options.list_tags_by_number or options.list_tags_by_alphabet or
                                  options.tags or options.tagtrees or options.tagfilter):
        error_exit(7, "Please don't use that gardening option together with any other option.")

    if options.tagfilter and (options.list_tags_by_number or options.list_tags_by_alphabet or
                              options.tags or options.tagtrees or options.tag_gardening):
        error_exit(14, "Please don't use that filter option together with any other option.")

    if options.list_tags_by_number and (options.tagfilter or options.list_tags_by_alphabet or
                                        options.tags or options.tagtrees or options.tag_gardening):
        error_exit(15, "Please don't use that list option together with any other option.")

    if options.list_tags_by_alphabet and (options.tagfilter or options.list_tags_by_number or
                                          options.tags or options.tagtrees or options.tag_gardening):
        error_exit(16, "Please don't use that list option together with any other option.")

    if options.tags and (options.tagfilter or options.list_tags_by_number or
                         options.list_tags_by_alphabet or options.tagtrees or options.tag_gardening):
        error_exit(17, "Please don't use that tags option together with any other option.")

    if options.tagtrees and (options.tagfilter or options.list_tags_by_number or
                             options.list_tags_by_alphabet or options.tags or options.tag_gardening):
        error_exit(18, "Please don't use the tagtrees option together with any other option.")

    if (options.list_tags_by_alphabet or options.list_tags_by_number) and (options.tags or options.interactive or options.remove):
        error_exit(8, "Please don't use list any option together with add/remove tag options.")

    logging.debug("extracting list of files ...")
    logging.debug("len(options.files) [%s]" % str(len(options.files)))

    files = extract_filenames_from_argument(options.files)

    global list_of_symlink_directories

    logging.debug("%s filenames found: [%s]" % (str(len(files)), '], ['.join(files)))
    logging.debug('reported console width: ' + str(TTY_WIDTH) + ' and height: ' + str(TTY_HEIGHT) + '   (80/80 is the fall-back)')
    tags_from_userinput = []
    vocabulary = sorted(locate_and_parse_controlled_vocabulary(False))

    if len(options.files) < 1 and not (options.tagtrees or options.tagfilter or options.list_tags_by_alphabet or
                                       options.list_tags_by_number or options.list_unknown_tags or options.tag_gardening):
        error_exit(5, "Please add at least one file name as argument")

    if options.list_tags_by_alphabet or options.list_tags_by_number or options.list_unknown_tags:

        tag_dict = get_tags_from_files_and_subfolders(startdir=os.getcwd())
        if not tag_dict:
            print("\nNo file containing tags found in this folder hierarchy.\n")
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

    elif options.tagtrees:
        logging.debug("handling option for tagtrees")

        # The command line options for tagtrees_handle_no_tag is checked:
        ignore_nontagged = False
        nontagged_subdir = False
        if options.tagtrees_handle_no_tag:
            if options.tagtrees_handle_no_tag[0] == 'treeroot':
                logging.debug("options.tagtrees_handle_no_tag found: treeroot (default)")
                pass  # keep defaults
            elif options.tagtrees_handle_no_tag[0] == 'ignore':
                logging.debug("options.tagtrees_handle_no_tag found: ignore")
                ignore_nontagged = True
            else:
                ignore_nontagged = False
                nontagged_subdir = options.tagtrees_handle_no_tag[0]
                logging.debug("options.tagtrees_handle_no_tag found: use foldername [" + repr(options.tagtrees_handle_no_tag) + "]")

        chosen_maxdepth = DEFAULT_TAGTREES_MAXDEPTH
        if options.tagtrees_depth:
            chosen_maxdepth = options.tagtrees_depth[0]
            logging.debug('User overrides the default tagtrees depth to: ' + str(chosen_maxdepth))
            if chosen_maxdepth > 4:
                logging.warning('The chosen tagtrees depth of ' + str(chosen_maxdepth) + ' is rather high.')
                logging.warning('When linking more than a few files, this might take a long time using many filesystem inodes.')

        chosen_tagtrees_dir = TAGFILTER_DIRECTORY
        if options.tagtrees_directory:
            chosen_tagtrees_dir = options.tagtrees_directory[0]
            logging.debug('User overrides the default tagtrees directory to: ' + str(chosen_tagtrees_dir))

        start = time.time()
        generate_tagtrees(chosen_tagtrees_dir, chosen_maxdepth, ignore_nontagged, nontagged_subdir, options.tagtrees_link_missing_mutual_tagged_items)
        delta = time.time() - start  # it's a float
        if delta > 3:
            logging.info("Generated tagtrees in %.2f seconds" % delta)
        start_filebrowser(chosen_tagtrees_dir)
        successful_exit()

    elif options.interactive or not options.tags:

        tags_for_visual = None

        if len(options.files) < 1 and not options.tagfilter:
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
            for tag in get_tags_from_files_and_subfolders(startdir=os.getcwd()):
                add_tag_to_countdict(tag, tags_for_vocabulary)

            logging.debug('generating vocabulary ...')
            vocabulary = sorted(tags_for_vocabulary.keys())
            upto9_tags_for_shortcuts = sorted(get_upto_nine_keys_of_dict_with_highest_value(tags_for_vocabulary))

        else:
            if files:

                # if it is only one file which is a symlink to the same basename
                # in a different directory, show the original directory:
                if len(files) == 1 and TAG_SYMLINK_ORIGINALS_WHEN_TAGGING_SYMLINKS and os.path.islink(files[0]):
                    symlink_file = split_up_filename(files[0])
                    original_file = split_up_filename(get_link_source_file(files[0]))  # 0 = absolute path incl. filename; 1 = dir; 2 = filename
                    if symlink_file[1] != original_file[1] and symlink_file[2] == original_file[2]:
                        # basenames are same, dirs are different
                        print("     ... symlink: tagging also matching filename in " + original_file[1])
                # do the same but for a list of symlink files whose paths have to match:
                if len(files) > 1 and TAG_SYMLINK_ORIGINALS_WHEN_TAGGING_SYMLINKS and all_files_are_symlink_to_same_directory(files):
                    # using first file for determining directories:
                    symlink_file = split_up_filename(files[0])
                    original_file = split_up_filename(get_link_source_file(files[0]))  # 0 = absolute path incl. filename; 1 = dir; 2 = filename
                    print("     ... symlinks: tagging also matching filenames in " + original_file[1])

                # remove given (shared) tags from the vocabulary:
                tags_intersection_of_files = get_common_tags_from_files(files)
                tags_for_visual = tags_intersection_of_files
                logging.debug("found common tags: tags_intersection_of_files[%s]" % '], ['.join(tags_intersection_of_files))

                # append current filetags with a prepended '-' in order to allow tag completion for removing tags via '-tagname'
                tags_from_filenames = set()
                for currentfile in files:
                    tags_from_filenames = tags_from_filenames.union(set(extract_tags_from_filename(currentfile)))
                negative_tags_from_filenames = set()
                for currenttag in list(tags_from_filenames):
                    negative_tags_from_filenames.add('-' + currenttag)

                vocabulary = list(set(vocabulary).union(negative_tags_from_filenames) - set(tags_intersection_of_files))

                logging.debug('deriving upto9_tags_for_shortcuts ...')
                upto9_tags_for_shortcuts = sorted(
                    get_upto_nine_keys_of_dict_with_highest_value(
                        get_tags_from_files_and_subfolders(
                            startdir=os.path.dirname(
                                os.path.abspath(files[0]))),
                        tags_intersection_of_files))
                logging.debug('derived upto9_tags_for_shortcuts')
            logging.debug('derived vocabulary with %i entries' % len(vocabulary))  # using default vocabulary which was generate above

        # ==================== Interactive asking user for tags ============================= ##
        tags_from_userinput = ask_for_tags(vocabulary, upto9_tags_for_shortcuts, tags_for_visual)
        # ==================== Interactive asking user for tags ============================= ##
        print('')  # new line after input for separating input from output

    else:
        # non-interactive: extract list of tags
        logging.debug("non-interactive mode: extracting tags from argument ...")

        tags_from_userinput = extract_tags_from_argument(options.tags[0])

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
    elif options.interactive:
        logging.info("processing tags \"%s\" ..." % str(BETWEEN_TAG_SEPARATOR.join(tags_from_userinput)))

    if options.tagfilter and not files:
        assert_empty_tagfilter_directory(TAGFILTER_DIRECTORY)
        files = filter_files_matching_tags(get_files_of_directory(os.getcwd()), tags_from_userinput)

    logging.debug("iterate over files ...")

    global max_file_length
    for filename in files:
        if len(filename) > max_file_length:
            max_file_length = len(filename)
    logging.debug('determined maximum file name length with %i' % max_file_length)

    for filename in files:

        if is_broken_link(filename):

            # skip broken links completely and write error message:
            logging.error('File "' + filename + '" is a broken symbolic link. Skipping this one …')

        else:

            # if filename is a symbolic link, tag the source file as well:
            handle_file_and_symlink_source_if_found(filename, tags_from_userinput, options.remove, options.tagfilter, options.dryrun)
            logging.debug('list_of_symlink_directories: ' + repr(list_of_symlink_directories))

            if len(list_of_symlink_directories) > 1:
                logging.debug('Seems like we\'ve found symlinks and renamed their source as well. Print out the those directories as well:')
                print('      This symbolic link has a link source with a matching basename. I renamed it there as well:')
                for directory in list_of_symlink_directories[:-1]:
                    print('      · ' + directory)
            list_of_symlink_directories = []

    if options.tagfilter:
        start_filebrowser(TAGFILTER_DIRECTORY)

    successful_exit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

# END OF FILE #################################################################

# end

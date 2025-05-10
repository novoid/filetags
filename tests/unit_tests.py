#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2023-08-28 18:16:44 vk>

# invoke tests using following command line:
# ~/src/vktag % PYTHONPATH="~/src/filetags:" tests/unit_tests.py --verbose

import unittest
import os
import filetags
import tempfile
import os.path
import logging
import platform
import time  # for sleep()
from shutil import rmtree


# TEMPLATE for debugging:
#        try:
#        except AssertionError:
#            import pdb; pdb.set_trace()

FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

# Missing tests:
# - FIXXME: find code which is not tested yet (before 2017-11-11)
# - everything related to tagtrees

class TestMethods(unittest.TestCase):

    def setUp(self):
        pass

    def test_contains_tag(self):

        self.assertEqual(filetags.contains_tag('Some file name -- foo.jpeg', 'foo'), True)
        self.assertEqual(filetags.contains_tag('Some file name -- foo bar.jpeg', 'foo'), True)
        self.assertEqual(filetags.contains_tag('Some file name -- bar foo.jpeg', 'foo'), True)
        self.assertEqual(filetags.contains_tag('Some file name -- foobar.jpeg', 'foo'), False)
        self.assertEqual(filetags.contains_tag('Some file name -- foo.jpeg', 'bar'), False)
        self.assertEqual(filetags.contains_tag('Some foo file name -- bar.jpeg', 'foo'), False)

        # without tagname -> check if any tags are found:
        self.assertEqual(filetags.contains_tag('Some file name -- foo.jpeg'), True)
        self.assertEqual(filetags.contains_tag('Some file name -- foo bar.jpeg'), True)
        self.assertEqual(filetags.contains_tag('Some file name.jpeg'), False)

        # ignoring Windows .lnk extension as extension:

        self.assertEqual(filetags.contains_tag('Some file name -- foo.jpeg.lnk', 'foo'), True)
        self.assertEqual(filetags.contains_tag('Some file name -- foo bar.jpeg.lnk', 'foo'), True)
        self.assertEqual(filetags.contains_tag('Some file name -- bar foo.jpeg.lnk', 'foo'), True)
        self.assertEqual(filetags.contains_tag('Some file name -- foobar.jpeg.lnk', 'foo'), False)
        self.assertEqual(filetags.contains_tag('Some file name -- foo.jpeg.lnk', 'bar'), False)
        self.assertEqual(filetags.contains_tag('Some foo file name -- bar.jpeg.lnk', 'foo'), False)

        # without tagname -> check if any tags are found:
        self.assertEqual(filetags.contains_tag('Some file name -- foo.jpeg.lnk'), True)
        self.assertEqual(filetags.contains_tag('Some file name -- foo bar.jpeg.lnk'), True)
        self.assertEqual(filetags.contains_tag('Some file name.jpeg.lnk'), False)

    def test_adding_tag_to_filename(self):

        self.assertEqual(filetags.adding_tag_to_filename('Some file name.jpeg', 'bar'),
                         'Some file name -- bar.jpeg')
        self.assertEqual(filetags.adding_tag_to_filename('Some file name -- foo.jpeg', 'bar'),
                         'Some file name -- foo bar.jpeg')
        self.assertEqual(filetags.adding_tag_to_filename('Some file name -- foo.jpeg', 'foo'),
                         'Some file name -- foo.jpeg')

        # ignoring Windows .lnk extension as extension:
        self.assertEqual(filetags.adding_tag_to_filename('Some file name.jpeg.lnk', 'bar'),
                         'Some file name -- bar.jpeg.lnk')
        self.assertEqual(filetags.adding_tag_to_filename('Some file name -- foo.jpeg.lnk', 'bar'),
                         'Some file name -- foo bar.jpeg.lnk')
        self.assertEqual(filetags.adding_tag_to_filename('Some file name -- foo.jpeg.lnk', 'foo'),
                         'Some file name -- foo.jpeg.lnk')

    def test_removing_tag_from_filename(self):

        self.assertEqual(filetags.removing_tag_from_filename('Some file name -- bar.jpeg', 'bar'),
                         'Some file name.jpeg')
        self.assertEqual(filetags.removing_tag_from_filename('Some file name -- foo bar.jpeg', 'bar'),
                         'Some file name -- foo.jpeg')
        self.assertEqual(filetags.removing_tag_from_filename('Some file name -- bar.jpeg', 'foo'),
                         'Some file name -- bar.jpeg')

        # ignoring Windows .lnk extension as extension:
        self.assertEqual(filetags.removing_tag_from_filename('Some file name -- bar.jpeg.lnk', 'bar'),
                         'Some file name.jpeg.lnk')
        self.assertEqual(filetags.removing_tag_from_filename('Some file name -- foo bar.jpeg.lnk', 'bar'),
                         'Some file name -- foo.jpeg.lnk')
        self.assertEqual(filetags.removing_tag_from_filename('Some file name -- bar.jpeg.lnk', 'foo'),
                         'Some file name -- bar.jpeg.lnk')

    def test_extract_tags_from_filename(self):
        self.assertEqual(filetags.extract_tags_from_filename('Some file name - bar.jpeg'), [])
        self.assertEqual(filetags.extract_tags_from_filename('-- bar.jpeg'), [])
        self.assertEqual(filetags.extract_tags_from_filename('Some file name.jpeg'), [])
        self.assertEqual(filetags.extract_tags_from_filename('Some file name - bar.jpeg'), [])
        self.assertEqual(filetags.extract_tags_from_filename('Some file name -- bar.jpeg'), ['bar'])
        self.assertEqual(filetags.extract_tags_from_filename('Some file name -- foo bar baz.jpeg'),
                         ['foo', 'bar', 'baz'])
        self.assertEqual(filetags.extract_tags_from_filename('Some file name -- foo bar baz'),
                         ['foo', 'bar', 'baz'])

        # ignoring Windows .lnk extension as extension:
        self.assertEqual(filetags.extract_tags_from_filename('Some file name - bar.jpeg.lnk'), [])
        self.assertEqual(filetags.extract_tags_from_filename('-- bar.jpeg.lnk'), [])
        self.assertEqual(filetags.extract_tags_from_filename('Some file name.jpeg.lnk'), [])
        self.assertEqual(filetags.extract_tags_from_filename('Some file name - bar.jpeg.lnk'), [])
        self.assertEqual(filetags.extract_tags_from_filename('Some file name -- bar.jpeg.lnk'), ['bar'])
        self.assertEqual(filetags.extract_tags_from_filename('Some file name -- foo bar baz.jpeg.lnk'),
                         ['foo', 'bar', 'baz'])

    def test_add_tag_to_countdict(self):
        self.assertEqual(filetags.add_tag_to_countdict('tag', {}), {'tag': 1})
        self.assertEqual(filetags.add_tag_to_countdict('tag', {'tag': 0}), {'tag': 1})
        self.assertEqual(filetags.add_tag_to_countdict('tag', {'tag': 1}), {'tag': 2})
        self.assertEqual(filetags.add_tag_to_countdict('newtag', {'oldtag': 1}), {'oldtag': 1, 'newtag': 1})
        self.assertEqual(filetags.add_tag_to_countdict('newtag', {'oldtag': 2}), {'oldtag': 2, 'newtag': 1})

    def test_find_similar_tags(self):

        self.assertEqual(filetags.find_similar_tags('xxx',
                                                    ['foobar', 'bar', 'baz', 'Frankenstein', 'parabol', 'Bah',
                                                     'paR', 'por', 'Schneewittchen']),
                         [])

        self.assertEqual(filetags.find_similar_tags('Simpson', ['foobar', 'Simson', 'simpson', 'Frankenstein',
                                                                'sumpson', 'Simpso', 'impson', 'mpson',
                                                                'Schneewittchen']),
                         ['impson', 'Simson', 'Simpso', 'simpson', 'mpson', 'sumpson'])

    def test_check_for_possible_shortcuts_in_entered_tags(self):

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['bar'],
                                                                               ['Frankenstein', 'Schneewittchen']),
                         ['bar'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['34'],
                                                                               ['Frankenstein', 'Schneewittchen',
                                                                                'baz', 'bar']),
                         ['baz', 'bar'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['12'],
                                                                               ['Frankenstein', 'Schneewittchen',
                                                                                'baz', 'bar']),
                         ['Frankenstein', 'Schneewittchen'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['59'],
                                                                               ['Frankenstein', 'Schneewittchen',
                                                                                'baz', 'bar']),
                         ['59'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['baz', '12', '88'],
                                                                               ['Frankenstein', 'Schneewittchen',
                                                                                'baz', 'bar']),
                         ['baz', 'Frankenstein', 'Schneewittchen', '88'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['19', '88', 'baz'],
                                                                               ['Frankenstein', 'Schneewittchen',
                                                                                'baz', 'bar']),
                         ['19', '88', 'baz'])

    def test_get_upto_nine_keys_of_dict_with_highest_value(self):

        self.assertEqual(filetags.get_upto_nine_keys_of_dict_with_highest_value({"key2": 45, "key1": 33}),
                         ["key1", "key2"])

        mydict = {"key1": 45, "key2": 33, "key3": 3, "key4": 1, "key5": 5, "key6": 159,
                  "key7": 0, "key8": 999, "key9": 42, "key10": 4242}
        myresult = ["key1", "key10", "key2", "key3", "key4", "key5", "key6", "key8", "key9"]
        self.assertEqual(filetags.get_upto_nine_keys_of_dict_with_highest_value(mydict), myresult)

        mydict = {"key1": 45, "key2": 33, "key3": 3, "key4": 1, "key5": 5, "key6": 159,
                  "key7": 0, "key8": 999, "key9": 42, "key10": 4242, "key11": 1234,
                  "key12": 1234, "key13": 1234, "key14": 1234}
        list_of_tags_to_omit = ['key11', 'key3', 'key7', 'key14']
        myresult = ["key1", "key10", "key12", "key13", "key2", "key5", "key6", "key8", "key9"]
        self.assertEqual(filetags.get_upto_nine_keys_of_dict_with_highest_value(mydict,
                                                                                list_of_tags_to_omit=list_of_tags_to_omit),
                         myresult)

    def test_get_common_tags_from_files(self):

        self.assertEqual(filetags.get_common_tags_from_files(['file1.txt']), [])
        self.assertEqual(filetags.get_common_tags_from_files(['file1 -- foo.txt']), ['foo'])
        self.assertSetEqual(set(filetags.get_common_tags_from_files(['file1 -- foo bar.txt'])), set(['foo', 'bar']))
        self.assertEqual(filetags.get_common_tags_from_files(['file1 -- foo.txt', 'file2.txt']), [])
        self.assertEqual(filetags.get_common_tags_from_files(['file1 -- foo.txt', 'file2 -- foo bar.txt']), ['foo'])
        self.assertEqual(filetags.get_common_tags_from_files(['file1 -- baz foo.txt',
                                                              'file2 -- foo bar.txt'
                                                              'file3 -- foo bar baz.txt'
                                                              'file4 -- foo bar jodel.txt']), ['foo'])
        self.assertSetEqual(set(filetags.get_common_tags_from_files(['file1 -- common baz foo.txt',
                                                                     'file2 -- common foo bar.txt'
                                                                     'file3 -- common foo bar baz.txt'
                                                                     'file4 -- common foo bar jodel.txt'])),
                            set(['common', 'foo']))
        # ignoring Windows .lnk extension as extension:
        self.assertSetEqual(set(filetags.get_common_tags_from_files(['file1 -- common baz foo.txt.lnk',
                                                                     'file2 -- common foo bar.txt.lnk'
                                                                     'file3 -- common foo bar baz.txt.lnk'
                                                                     'file4 -- common foo bar jodel.txt.lnk'])),
                            set(['common', 'foo']))

    def test_extract_tags_from_path(self):
        self.assertEqual(set(filetags.extract_tags_from_path('/a/path/without/tags')), set([]))
        self.assertEqual(set(filetags.extract_tags_from_path('/path -- ptag1/with -- ptag1 ptag2/tags')),
                         set(['ptag1', 'ptag2']))
        self.assertEqual(set(filetags.extract_tags_from_path('/path -- ptag1/with -- ptag1 ptag2/tags -- ftag1')),
                         set(['ptag1', 'ptag2', 'ftag1']))

    def test_extract_iso_datestamp_from_filename(self):
        self.assertEqual(filetags.extract_iso_datestamp_from_filename(''), [])
        self.assertEqual(filetags.extract_iso_datestamp_from_filename('foo'), [])
        self.assertEqual(filetags.extract_iso_datestamp_from_filename('9999-99-99 foo bar'), [])
        self.assertEqual(filetags.extract_iso_datestamp_from_filename('2018-03-18 foo bar'), ['2018', '03', '18'])
        self.assertEqual(filetags.extract_iso_datestamp_from_filename('2018-03-18_foo bar'), ['2018', '03', '18'])
        self.assertEqual(filetags.extract_iso_datestamp_from_filename('2018-03-18-foo bar'), ['2018', '03', '18'])
        self.assertEqual(filetags.extract_iso_datestamp_from_filename('2018-03-18T23.59 foo bar'),
                         ['2018', '03', '18'])

    def tearDown(self):

        pass


class TestLocateAndParseControlledVocabulary(unittest.TestCase):

    """
    The following directory structure applies:

    tempdir
          |
          `- .filetags [4]
           - .filetags [5] (symlink to subdir2/.filetags)
           - .filetags.lnk [6] (Windows only)
           - subdir1
                   |
                   `- test file for tagging.txt
                    - .filetags [1]
                    - .filetags [2] (symlink to subdir2/.filetags)
                    - .filetags.lnk [3] (Windows only)
           - subdir2
                   |
                   `- .filetags
           - subdir3   --> the working directory

    The numbers in the brackets reflect the priority of the controlled
    vocabulary (CV) file found. Of course, symbolic link files only apply to
    non-Windows platforms and .lnk files only apply to Windows.

    setUp creates:

    tempdir
          |
          `- .filetags [2]
           - subdir1
                   |
                   `- test file for tagging.txt
                    - .filetags [1]
           - subdir2
                   |
                   `- .filetags  --> the link destination (original file)
           - subdir3   --> the working directory

    In the test routine, the other .filetags link files are
    created (or deleted) accordingly.
    """

    # the temporary direcories holding the files for these tests:
    tempdir = None
    subdir1 = None
    subdir2 = None

    # each .filetags file gets one unique tag so that I can
    # check which controlled vocabulary was used:
    tempdir_cv = 'tag_from_tempdir_CV'
    subdir1_cv = 'tag_from_subdir1_CV'
    subdir2_cv = 'tag_from_subdir2_CV'
    subdir2b_cv = 'tag_from_subdir2b_CV'

    tempdir_file = None
    subdir1_file = None
    subdir2_file = None
    subdir2b_file = None

    # we need this for specifying a file to tag in a subdir:
    subdir1_test_file = None
    tagging_test_file = 'test file for tagging.txt'

    def setUp(self):

        # create temporary directories:
        self.tempdir = tempfile.mkdtemp(prefix='TestControlledVocabulary_')
        print("\nTestControlledVocabulary: tempdir: " + self.tempdir + '  <<<' + '#' * 10)
        self.subdir1 = os.path.join(self.tempdir, 'subdir1')
        os.makedirs(self.subdir1)
        self.subdir2 = os.path.join(self.tempdir, 'subdir2')
        os.makedirs(self.subdir2)
        self.subdir3 = os.path.join(self.tempdir, 'subdir3')
        os.makedirs(self.subdir3)
        os.chdir(self.subdir3)

        assert(os.path.isdir(self.tempdir))
        assert(os.path.isdir(self.subdir1))
        assert(os.path.isdir(self.subdir2))

        # create Controlled vocabulary files:
        self.tempdir_file = os.path.join(self.tempdir, '.filetags')
        self.subdir1_file = os.path.join(self.subdir1, '.filetags')
        self.subdir2_file = os.path.join(self.subdir2, 'filetags_subdir2')
        self.subdir2b_file = os.path.join(self.subdir2, 'filetags_subdir2b')
        self.create_file(self.tempdir_file, self.tempdir_cv)
        self.create_file(self.subdir1_file, self.subdir1_cv)
        self.create_file(self.subdir2_file, self.subdir2_cv)
        self.create_file(self.subdir2b_file, self.subdir2b_cv)
        assert(os.path.isfile(self.tempdir_file))
        assert(os.path.isfile(self.subdir1_file))
        assert(os.path.isfile(self.subdir2_file))
        assert(os.path.isfile(self.subdir2b_file))

        # one normal file:
        self.subdir1_test_file = os.path.join(self.subdir1, self.tagging_test_file)
        self.create_file(self.subdir1_test_file, 'this is a test file')
        assert(os.path.isfile(self.subdir1_test_file))

        if platform.system() != 'Windows':
            os.sync()

    def tearDown(self):

        if platform.system() != 'Windows':
            # 2018-04-05: disabled until I find a solution for:
            # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'C:\\Users\\KARL~1.VOI\\AppData\\Local\\Temp\\tmprfwup13z'
            rmtree(self.tempdir)

    def create_file(self, name, content):

        assert(os.path.isdir(os.path.dirname(name)))
        with open(name, 'w') as outputhandle:
            outputhandle.write(content)

    def test_find_cv_in_startfile_dir_instead_of_cwd(self):

        # Note: cwd = subdir3

        self.assertEqual(filetags.locate_and_parse_controlled_vocabulary(self.subdir1_test_file),
                         [self.subdir1_cv])

    def test_find_cv_as_link_in_startfile_dir_when_there_is_no_cv_as_file(self):

        # Note: cwd = subdir3

        os.remove(self.subdir1_file)  # removing the .filetags from the subdir1
        filetags.create_link(self.subdir2_file, self.subdir1_file)  # create link

        self.assertEqual(filetags.locate_and_parse_controlled_vocabulary(self.subdir1_test_file),
                         [self.subdir2_cv])

    def test_find_cv_as_file_in_tempdir_when_startfile_dir_has_nothing(self):

        # Note: cwd = subdir3

        os.remove(self.subdir1_file)  # removing the .filetags from the subdir1
        self.assertEqual(filetags.locate_and_parse_controlled_vocabulary(self.subdir1_test_file),
                         [self.tempdir_cv])

    def test_find_cv_as_link_in_tempdir_when_startfile_dir_has_nothing(self):

        # Note: cwd = subdir3

        os.remove(self.subdir1_file)  # removing the .filetags from the subdir1
        os.remove(self.tempdir_file)  # removing the .filetags from the tempdir
        filetags.create_link(self.subdir2_file, self.tempdir_file)  # create link

        self.assertEqual(filetags.locate_and_parse_controlled_vocabulary(self.subdir1_test_file),
                         [self.subdir2_cv])

    def test_find_cv_in_cwd_as_first_fallback_when_no_startfile_is_given(self):

        # Note: cwd = subdir3

        os.remove(self.subdir1_file)  # removing the .filetags from the subdir1
        os.remove(self.tempdir_file)  # removing the .filetags from the tempdir
        filetags.create_link(self.subdir2_file, os.path.join(self.subdir3, '.filetags'))  # create link

        self.assertEqual(filetags.locate_and_parse_controlled_vocabulary(False),
                         [self.subdir2_cv])

    def test_Windows_piority_of_cv_files_as_files_and_lnk_files(self):

        if platform.system() != 'Windows':
            # This test only makes sense on Windows where .filetags can exist in same dir as .filetags.lnk
            return

        # Note: cwd = subdir3
        # Let's create all missing files in all dirs:
        filetags.create_link(self.subdir2_file, self.subdir1_file)  # create link
        filetags.create_link(self.subdir2b_file, self.tempdir_file)  # create link

        # prio 1 = .filetag file in startfile directory
        self.assertEqual(filetags.locate_and_parse_controlled_vocabulary(self.subdir1_test_file),
                         [self.subdir1_cv])

        # prio 2 = .filetag.lnk file in startfile directory
        os.remove(self.subdir1_file)  # removing the .filetags from the subdir1
        self.assertEqual(filetags.locate_and_parse_controlled_vocabulary(self.subdir1_test_file),
                         [self.subdir2_cv])

        # prio 3 = .filetag file in tempdir
        os.remove(self.subdir1_file + '.lnk')  # removing the .filetags link file from the subdir1
        self.assertEqual(filetags.locate_and_parse_controlled_vocabulary(self.subdir1_test_file),
                         [self.tempdir_cv])

        # prio 4 = .filetag.lnk file in tempdir
        os.remove(self.tempdir_file)  # removing the .filetags link file from the subdir1
        self.assertEqual(filetags.locate_and_parse_controlled_vocabulary(self.subdir1_test_file),
                         [self.subdir2b_cv])

    def NOtest_find_cv_in_home_as_last_fallback_when_no_other_cv_is_around(self):

        # Currently disabled because I don't want to mess around in $HOME for testing purposes.
        pass

    def test_comment_line_in_cv(self):
        """
        This tests does not use the setup from the test class. However, it does use several
        other util functions defined in this class. Therefore, I set up a different test
        case here and re-use the util functions.

        Test CV file looks like:

        foo
        # comment
        bar
        ## another comment
        baz
        #
        tag #inline-comment

        This should result in following CV: ["foo", "bar", "baz", "tag"] and not more.

        """

        tempdir = tempfile.mkdtemp(prefix='TestControlledVocabulary_Comments_line_')
        print("\ntempdir: " + tempdir + '  <<<' + '#' * 10)
        assert(os.path.isdir(tempdir))

        # create Controlled vocabulary files:
        cv_file = os.path.join(tempdir, '.filetags')
        self.create_file(cv_file, "foo\n# comment\nbar\n## another comment\nbaz\n#\ntag #inline-comment\n\n")
        assert(os.path.isfile(cv_file))

        # setup complete

        cv = filetags.locate_and_parse_controlled_vocabulary(cv_file)
        self.assertEqual(set(cv), set(["foo", "bar", "baz", "tag"]))


    def test_include_lines_in_cv_not_circular(self):
        """
        This tests does not use the setup from the test class. However, it does use several
        other util functions defined in this class. Therefore, I set up a different test
        case here and re-use the util functions.

        Setup looks like this:
        tmpdir
             `- subdir1
                      |
                       `- .filetags with a reference to subdir2/included.filetags
              - subdir2
                      |
                       `- included_filetags with additional tags
        """
        tempdir = tempfile.mkdtemp(prefix="TestControlledVocabulary_Include")
        print("\ntempdir: " + tempdir + '  <<<' + '#' * 10)

        subdir1 = os.path.join(tempdir, "subdir1")
        os.makedirs(subdir1)
        assert(os.path.exists(subdir1))

        subdir2 = os.path.join(tempdir, "subdir2")
        os.makedirs(subdir2)
        assert(os.path.exists(subdir2))

        include_cv = """
        tag_from_include_before_CV
        #include ../subdir2/included.filetags
        tag_from_include_after_CV
        """
        include_file = os.path.join(subdir1, '.filetags')
        self.create_file(include_file, include_cv)
        assert(os.path.isfile(include_file))

        included_cv = 'tag_from_included_CV'
        included_file = os.path.join(subdir2, 'included.filetags')
        self.create_file(included_file, included_cv)
        assert(os.path.isfile(included_file))

        if platform.system() != 'Windows':
            os.sync()

        # setup complete

        cv = filetags.locate_and_parse_controlled_vocabulary(include_file)
        self.assertEqual(set(cv), set(["tag_from_include_before_CV", "tag_from_include_after_CV", "tag_from_included_CV"]))

    def test_include_lines_in_cv_circular(self):
        """
        This tests does not use the setup from the test class. However, it does use several
        other util functions defined in this class. Therefore, I set up a different test
        case here and re-use the util functions.

        Setup looks like this:
        tmpdir
             `- subdir1
                      |
                       `- .filetags with a reference to subdir2/included.filetags
              - subdir2
                      |
                       `- included.filetags with additional tags and reference to subdir1/.filetags
        """
        tempdir = tempfile.mkdtemp(prefix="TestControlledVocabulary_Include")
        print("\ntempdir: " + tempdir + '  <<<' + '#' * 10)

        subdir1 = os.path.join(tempdir, "subdir1")
        os.makedirs(subdir1)
        assert(os.path.exists(subdir1))

        subdir2 = os.path.join(tempdir, "subdir2")
        os.makedirs(subdir2)
        assert(os.path.exists(subdir2))

        circular1_cv = """
        tag_from_first_before_CV
        #include ../subdir2/included.filetags
        tag_from_first_after_CV
        """
        circular1_file = os.path.join(subdir1, '.filetags')
        self.create_file(circular1_file, circular1_cv)
        assert(os.path.isfile(circular1_file))

        circular2_cv = """
        tag_from_second_before_CV
        #include ../subdir1/.filetags
        tag_from_second_after_CV
        """
        circular2_file = os.path.join(subdir2, 'included.filetags')
        self.create_file(circular2_file, circular2_cv)
        assert(os.path.isfile(circular2_file))

        if platform.system() != 'Windows':
            os.sync()

        # setup complete

        cv = filetags.locate_and_parse_controlled_vocabulary(circular1_file)
        self.assertEqual(set(cv), set(["tag_from_first_before_CV", "tag_from_first_after_CV", "tag_from_second_before_CV", "tag_from_second_after_CV"]))

class TestFileWithoutTags(unittest.TestCase):

    tempdir = None
    testfilename = 'a test file . for you.txt'

    def setUp(self):

        # create temporary directory:
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        print("\nTestFileWithoutTags: temporary directory: " + self.tempdir)

        # create set of test files:
        self.create_tmp_file(self.testfilename)

        # double-check set-up:
        self.assertTrue(self.file_exists(self.testfilename))

        if platform.system() != 'Windows':
            os.sync()

    def create_tmp_file(self, name):

        with open(os.path.join(self.tempdir, name), 'w') as outputhandle:
            outputhandle.write('This is a test file for filetags unit testing')

    def file_exists(self, name):

        return os.path.isfile(os.path.join(self.tempdir, name))

    def test_handle_file_with_nonexistent_filename(self):

         with self.assertRaises(FileNotFoundError):
             filetags.handle_file(os.path.join(self.tempdir, 'this filename does not exist - ' + self.testfilename),
                                  ['bar'],
                                  do_remove=False, do_filter=False, dryrun=False)

    def test_add_and_remove_tags(self):

        # adding a tag to a file without any tags:
        filetags.handle_file(os.path.join(self.tempdir, self.testfilename),
                             ['bar'],
                             do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists('a test file . for you -- bar.txt'), True)

        # adding a second tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- bar.txt'),
                             ['foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists('a test file . for you -- bar foo.txt'), True)

        # adding two tags:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- bar foo.txt'),
                             ['one', 'two'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists('a test file . for you -- bar foo one two.txt'), True)

        # simulating another tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- bar foo one two.txt'),
                             ['one', 'two'], do_remove=False, do_filter=False, dryrun=True)
        self.assertEqual(self.file_exists('a test file . for you -- bar foo one two.txt'), True)

        # removing three tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- bar foo one two.txt'),
                             ['bar', 'one', 'foo'], do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists('a test file . for you -- two.txt'), True)

        # removing last tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- two.txt'),
                             ['two'], do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists('a test file . for you.txt'), True)

    def test_unique_tags(self):

        # Note: default unique_tags is a hard-coded list of u'teststring1' and u'teststring2'

        # adding a unique tag to a file without any tags:
        dummy_filename = filetags.handle_file(os.path.join(self.tempdir, self.testfilename),
                                              ['teststring1'],
                                              do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists('a test file . for you -- teststring1.txt'), True)

        # adding a second unique tag - first one should be gone:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- teststring1.txt'),
                             ['teststring2'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists('a test file . for you -- teststring2.txt'), True)

        # adding non-unique tags:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- teststring2.txt'),
                             ['one', 'two'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists('a test file . for you -- teststring2 one two.txt'), True)

        # removing unique tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- teststring2 one two.txt'),
                             ['teststring2', 'one'], do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists('a test file . for you -- two.txt'), True)

    def test_adding_a_tag_to_file_without_extension(self):

        filename = "file without extension"
        self.create_tmp_file(filename)
        filetags.handle_file(os.path.join(self.tempdir, filename),
                             ['foo'],
                             do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(filename + ' -- foo'), True)

    # there is no such function: filetags.list_tags_by_number()
    def NOtest_list_tags_by_number(self):

        # starting with no file with tags:
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {})

        # adding a file tag:
        filetags.handle_file(os.path.join(self.tempdir, self.testfilename),
                             ['bar'],
                             do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {'bar': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=0), {'bar': 1})

        # adding a another file tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- bar.txt'),
                             ['foo'],
                             do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {'bar': 1, 'foo': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=0), {'bar': 1, 'foo': 1})

        # adding a another file:
        self.create_tmp_file('a second file')
        filetags.handle_file(os.path.join(self.tempdir, 'a second file'),
                             ['foo'],
                             do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {'bar': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {'bar': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=0), {'bar': 1, 'foo': 2})

    # there is no such function: filetags.list_tags_by_aphabet()
    def NOtest_list_tags_by_alphabet(self):

        # starting with no file with tags:
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})

        # adding a file tag:
        filetags.handle_file(os.path.join(self.tempdir, self.testfilename),
                             ['similar1'],
                             do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False), {'similar1': 1})

        # adding a file tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- similar1.txt'),
                             ['foo'],
                             do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False),
                         {'foo': 1, 'similar1': 1})

        # adding a another file:
        self.create_tmp_file('a second file')
        filetags.handle_file(os.path.join(self.tempdir, 'a second file'),
                             ['foo'],
                             do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False),
                         {'foo': 2, 'similar1': 1})

        # adding similar tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a second file -- foo'),
                             ['similar2'],
                             do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True),
                         {'similar1': 1, 'similar2': 1})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False),
                         {'foo': 2, 'similar1': 1, 'similar2': 1})

    def tearDown(self):

        if platform.system() != 'Windows':
            # 2018-04-05: disabled until I find a solution for:
            # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'C:\\Users\\KARL~1.VOI\\AppData\\Local\\Temp\\tmprfwup13z'
            rmtree(self.tempdir)


class TestHierarchyWithFilesAndFolders(unittest.TestCase):

    tempdir = None
    subdir1 = None
    subdir2 = None

    def setUp(self):
        """This setup function creates following dir/file structure:

        tempdir   (via tempfile.mkdtemp())
          |_ "foo1 -- bar.txt"
          |_ "foo2 -- bar baz.txt"
          |_ "foo3 -- baz teststring1.txt"
          |_ sub dir 1/
               |_ "foo4 -- bar.txt"
               |_ "foo5.txt"
               |_ "foo6 -- baz teststring1.txt"
               |_ "foo7 -- teststring1.txt"
               |_ "foo8 -- baz.txt"
               |_ "foo9 -- baz bar.txt"
          |_ sub dir 2/  (empty)
        """

        # create temporary directory:
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        print("\nTestHierarchyWithFilesAndFolders: temporary directory: " + self.tempdir)

        # initial tests without files:
        self.assertEqual(filetags.get_tags_from_files_and_subfolders(self.tempdir, use_cache=False), {})

        # create set of test files:
        self.create_tmp_file(self.tempdir, "foo1 -- bar.txt")
        self.create_tmp_file(self.tempdir, "foo2 -- bar baz.txt")
        self.create_tmp_file(self.tempdir, "foo3 -- baz teststring1.txt")

        # create first sub directory and its files:
        self.subdir1 = os.path.join(self.tempdir, "sub dir 1")
        os.makedirs(self.subdir1)
        self.create_tmp_file(self.subdir1, "foo4 -- bar.txt")
        self.create_tmp_file(self.subdir1, "foo5.txt")
        self.create_tmp_file(self.subdir1, "foo6 -- baz teststring1.txt")
        self.create_tmp_file(self.subdir1, "foo7 -- teststring1.txt")
        self.create_tmp_file(self.subdir1, "foo8 -- baz.txt")
        self.create_tmp_file(self.subdir1, "foo9 -- baz bar.txt")

        # create second sub directory (empty)
        self.subdir2 = os.path.join(self.tempdir, "sub dir 2")
        os.makedirs(self.subdir2)

        if platform.system() != 'Windows':
            os.sync()

    def create_tmp_file(self, directory, name):

        with open(os.path.join(directory, name), 'w') as outputhandle:
            outputhandle.write('This is a test file for filetags unit testing')

    def file_exists(self, name):

        return os.path.isfile(os.path.join(self.tempdir, name))

    def test_vocabulary_in_real_world_example(self):

        print("FIXXME: test_vocabulary_in_real_world_example needs vocabulary + tests")

    def test_get_tags_from_files_and_subfolders(self):

        self.assertEqual(filetags.get_tags_from_files_and_subfolders(self.tempdir, use_cache=False),
                         {'baz': 2, 'bar': 2, 'teststring1': 1})

        # FIXXME: write test which tests the cache

    def test_list_unknown_tags(self):

        print("FIXXME: test_list_unknown_tags() not implemented yet")

    def test_handle_tag_gardening(self):

        print("FIXXME: test_handle_tag_gardening() not implemented yet")

    def test_locate_and_parse_controlled_vocabulary(self):

        print("FIXXME: test_locate_and_parse_controlled_vocabulary() not implemented yet")

    def test_tag_file_in_subdir(self):

        # adding a tag
        filetags.handle_file(os.path.join(self.tempdir, 'sub dir 1', 'foo4 -- bar.txt'),
                             ['testtag'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(os.path.join(self.tempdir, 'sub dir 1', 'foo4 -- bar testtag.txt')), True)
        
    def test_tagtrees_with_tagfilter_and_no_filtertag(self):

        filetags.generate_tagtrees(directory=self.subdir2,
                                   maxdepth=5,
                                   ignore_nontagged=False,
                                   nontagged_subdir='nontagged_items',
                                   link_missing_mutual_tagged_items=False,
                                   filtertags=None)

        self.assertEqual(len(os.listdir(self.subdir2)), 5)  # 5 entries in this directory

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'bar')))
        self.assertEqual(set(os.listdir(os.path.join(self.subdir2, 'bar'))),
                         set(['baz', 'foo1 -- bar.txt', 'foo2 -- bar baz.txt']))

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'baz')))
        self.assertEqual(set(os.listdir(os.path.join(self.subdir2, 'baz'))),
                         set(['bar', 'teststring1', 'foo2 -- bar baz.txt', 'foo3 -- baz teststring1.txt']))

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'teststring1')))
        self.assertEqual(set(os.listdir(os.path.join(self.subdir2, 'teststring1'))),
                         set(['baz', 'foo3 -- baz teststring1.txt']))

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'nontagged_items')))


    def test_tagtrees_with_tagfilter_and_one_filtertag(self):

        filetags.generate_tagtrees(directory=self.subdir2,
                                   maxdepth=5,
                                   ignore_nontagged=False,
                                   nontagged_subdir='nontagged_items',
                                   link_missing_mutual_tagged_items=False,
                                   filtertags=['teststring1'])

        self.assertEqual(len(os.listdir(self.subdir2)), 4)  # 4 entries in this directory

        self.assertFalse(os.path.isdir(os.path.join(self.subdir2, 'bar')))

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'baz')))
        self.assertEqual(set(os.listdir(os.path.join(self.subdir2, 'baz'))),
                         set(['teststring1', 'foo3 -- baz teststring1.txt']))

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'teststring1')))
        self.assertEqual(set(os.listdir(os.path.join(self.subdir2, 'teststring1'))),
                         set(['baz', 'foo3 -- baz teststring1.txt']))

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'nontagged_items')))


    def test_tagtrees_with_tagfilter_and_multiple_filtertags(self):

        filetags.generate_tagtrees(directory=self.subdir2,
                                   maxdepth=5,
                                   ignore_nontagged=False,
                                   nontagged_subdir='nontagged_items',
                                   link_missing_mutual_tagged_items=False,
                                   filtertags=['teststring1', 'baz'])

        self.assertEqual(set(os.listdir(self.subdir2)),
                         set(['.filetags_tagtrees', 'teststring1', 'baz', 'nontagged_items']))

        self.assertFalse(os.path.isdir(os.path.join(self.subdir2, 'bar')))

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'baz')))
        self.assertEqual(set(os.listdir(os.path.join(self.subdir2, 'baz'))),
                         set(['teststring1', 'foo3 -- baz teststring1.txt']))

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'teststring1')))

        self.assertTrue(os.path.isdir(os.path.join(self.subdir2, 'nontagged_items')))


    def test_tagtrees_overwrites_old_default_directory(self):

        with open(os.path.join(self.subdir2, 'boring tagtrees data.txt'), 'w'):
            pass

        filetags.generate_tagtrees(directory=self.subdir2,
                                   maxdepth=5,
                                   ignore_nontagged=False,
                                   nontagged_subdir='nontagged_items',
                                   link_missing_mutual_tagged_items=False,
                                   filtertags=None)


    def test_tagtrees_overwrites_known_tagtrees(self):

        filetags.options.tagtrees_directory = self.subdir2

        with open(os.path.join(self.subdir2, '.filetags_tagtrees'), 'w'):
            pass

        filetags.generate_tagtrees(directory=self.subdir2,
                                   maxdepth=5,
                                   ignore_nontagged=False,
                                   nontagged_subdir='nontagged_items',
                                   link_missing_mutual_tagged_items=False,
                                   filtertags=None)

        filetags.options.tagtrees_directory = None


    def test_tagtrees_overwrites_nonempty_foreign_directory(self):

        filetags.options.tagtrees_directory = self.subdir2

        with open(os.path.join(self.subdir2, 'critical data.txt'), 'w'):
            pass

        with self.assertRaises(SystemExit):
            filetags.generate_tagtrees(directory=self.subdir2,
                                       maxdepth=5,
                                       ignore_nontagged=False,
                                       nontagged_subdir='nontagged_items',
                                       link_missing_mutual_tagged_items=False,
                                       filtertags=None)

        filetags.options.tagtrees_directory = None


    def test_tagtrees_overwrites_empty_foreign_directory(self):

        filetags.options.tagtrees_directory = self.subdir2

        filetags.generate_tagtrees(directory=self.subdir2,
                                   maxdepth=5,
                                   ignore_nontagged=False,
                                   nontagged_subdir='nontagged_items',
                                   link_missing_mutual_tagged_items=False,
                                   filtertags=None)

        filetags.options.tagtrees_directory = None


    def tearDown(self):

        if platform.system() != 'Windows':
            # 2018-04-05: disabled until I find a solution for:
            # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'C:\\Users\\KARL~1.VOI\\AppData\\Local\\Temp\\tmprfwup13z'
            rmtree(self.tempdir)


class TestReplacingLinkSourceAndTarget(unittest.TestCase):

    tempdir = None

    SOURCEFILE1 = 'source file 1 - same tags -- bar.txt'
    LINKFILE1 = 'link file 1 - same tags -- bar.txt'

    SOURCEFILE2 = 'source file 2 - source has tag and link not -- baz.txt'
    LINKFILE2 = 'link file 2 - source has tag and link not.txt'

    SOURCEFILE3 = 'source file 3 - source no tags and link has.txt'
    LINKFILE3 = 'link file 3 - source no tags and link has -- baz.txt'

    SOURCEFILE4 = 'link and source same name.txt'
    LINKFILE4 = 'link and source same name.txt'

    if platform.system() == 'Windows':
        LINKFILE1 = LINKFILE1 + '.lnk'
        LINKFILE2 = LINKFILE2 + '.lnk'
        LINKFILE3 = LINKFILE3 + '.lnk'
        LINKFILE4 = LINKFILE4 + '.lnk'

    def setUp(self):

        # create temporary directory for the source files:
        self.sourcedir = tempfile.mkdtemp(prefix='sources')
        self.linkdir = tempfile.mkdtemp(prefix='links')

        os.chdir(self.sourcedir)
        logging.info("\nTestReplacingLinkSourceAndTarget: sourcedir: " + self.sourcedir +
                     " and linkdir: " + self.linkdir)

        # create set of test files:
        self.create_source_file(self.SOURCEFILE1)
        self.create_source_file(self.SOURCEFILE2)
        self.create_source_file(self.SOURCEFILE3)
        self.create_source_file(self.SOURCEFILE3)
        self.create_source_file(self.SOURCEFILE4)

        # create symbolic links:
        self.create_link_file(self.SOURCEFILE1, self.LINKFILE1)
        self.create_link_file(self.SOURCEFILE2, self.LINKFILE2)
        self.create_link_file(self.SOURCEFILE3, self.LINKFILE3)
        self.create_link_file(self.SOURCEFILE4, self.LINKFILE4)

        if platform.system() != 'Windows':
            os.sync()

    def create_source_file(self, name):

        with open(os.path.join(self.sourcedir, name), 'w') as outputhandle:
            outputhandle.write('This is a test file for filetags unit testing')

    def create_link_file(self, source, destination):

        filetags.create_link(os.path.join(self.sourcedir, source), os.path.join(self.linkdir, destination))

    def source_file_exists(self, name):

        return os.path.isfile(os.path.join(self.sourcedir, name))

    def link_file_exists(self, name):

        if platform.system() == 'Windows' and not name.endswith('.lnk'):
            name += '.lnk'
        return os.path.isfile(os.path.join(self.linkdir, name))

    def is_broken_link(self, name):

        # This function determines if the given name points to a file
        # that is a broken link. It returns False for any other cases
        # such as non existing files and so forth.

        return filetags.is_broken_link(os.path.join(self.linkdir, name))

    def tearDown(self):

        if platform.system() != 'Windows':
            # 2018-04-05: disabled until I find a solution for:
            # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'C:\\Users\\KARL~1.VOI\\AppData\\Local\\Temp\\tmprfwup13z'
            rmtree(self.sourcedir)
            rmtree(self.linkdir)

    def test_adding_tags_to_links(self):

        self.assertEqual(self.link_file_exists(self.LINKFILE1), True)
        logging.info('#' * 90)
        filetags.handle_file_and_optional_link(os.path.join(self.linkdir, self.LINKFILE1),
                                               ['foo'],
                                               do_remove=False, do_filter=False, dryrun=False)
        logging.info('only the link gets this tag because basenames differ:')
        self.assertEqual(self.link_file_exists('link file 1 - same tags -- bar foo.txt'), True)
        self.assertEqual(self.source_file_exists(self.SOURCEFILE1), True)

        logging.info('basenames are same, so both files should get the tag:')
        filetags.handle_file_and_optional_link(os.path.join(self.linkdir, self.LINKFILE4),
                                               ['foo'],
                                               do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.link_file_exists('link and source same name -- foo.txt'), True)
        self.assertEqual(self.source_file_exists('link and source same name -- foo.txt'), True)

    def test_adding_tag_to_an_original_file_causing_broken_link(self):

        self.assertFalse(self.is_broken_link(self.LINKFILE4))
        filetags.handle_file_and_optional_link(os.path.join(self.sourcedir, self.SOURCEFILE4),
                                               ['foo'],
                                               do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.source_file_exists('link and source same name -- foo.txt'), True)
        self.assertTrue(self.is_broken_link(self.LINKFILE4))

    def test_removing_tags(self):

        logging.info('removing a non existing tag should not change anything at all:')
        filetags.handle_file_and_optional_link(os.path.join(self.linkdir, self.LINKFILE4),
                                               ['foo'],
                                               do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.source_file_exists(self.SOURCEFILE4), True)
        self.assertEqual(self.link_file_exists(self.LINKFILE4), True)

        logging.info('adding tags just for the next tests:')
        filetags.handle_file_and_optional_link(os.path.join(self.linkdir, self.LINKFILE4),
                                               ['foo', 'bar'],
                                               do_remove=False, do_filter=False, dryrun=False)

        self.assertEqual(self.link_file_exists('link and source same name -- foo bar.txt'), True)
        self.assertEqual(self.source_file_exists('link and source same name -- foo bar.txt'), True)

        logging.info('removing tags which only exists partially:')
        filename = 'link and source same name -- foo bar.txt'
        if platform.system() == 'Windows':
            filename += '.lnk'
        filetags.handle_file_and_optional_link(os.path.join(self.linkdir, filename),
                                               ['baz', 'bar'],
                                               do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.link_file_exists('link and source same name -- foo.txt'), True)
        self.assertEqual(self.source_file_exists('link and source same name -- foo.txt'), True)

        logging.info('removing tags using minus-notation like "-foo"')
        filename = 'link and source same name -- foo.txt'
        if platform.system() == 'Windows':
            filename += '.lnk'
        filetags.handle_file_and_optional_link(os.path.join(self.linkdir, filename),
                                               ['-foo', 'bar'],
                                               do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.link_file_exists('link and source same name -- bar.txt'), True)
        self.assertEqual(self.source_file_exists('link and source same name -- bar.txt'), True)

if __name__ == '__main__':
    unittest.main()

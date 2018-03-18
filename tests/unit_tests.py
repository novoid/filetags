#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2018-03-18 11:00:42 vk>

# invoke tests using following command line:
# ~/src/vktag % PYTHONPATH="~/src/filetags:" tests/unit_tests.py --verbose

import unittest
import os
import filetags
import tempfile
import os.path
import logging
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

    def test_adding_tag_to_filename(self):

        self.assertEqual(filetags.adding_tag_to_filename('Some file name.jpeg', 'bar'),
                         'Some file name -- bar.jpeg')
        self.assertEqual(filetags.adding_tag_to_filename('Some file name -- foo.jpeg', 'bar'),
                         'Some file name -- foo bar.jpeg')
        self.assertEqual(filetags.adding_tag_to_filename('Some file name -- foo.jpeg', 'foo'),
                         'Some file name -- foo.jpeg')

    def test_removing_tag_from_filename(self):

        self.assertEqual(filetags.removing_tag_from_filename('Some file name -- bar.jpeg', 'bar'),
                         'Some file name.jpeg')
        self.assertEqual(filetags.removing_tag_from_filename('Some file name -- foo bar.jpeg', 'bar'),
                         'Some file name -- foo.jpeg')
        self.assertEqual(filetags.removing_tag_from_filename('Some file name -- bar.jpeg', 'foo'),
                         'Some file name -- bar.jpeg')

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

    def test_add_tag_to_countdict(self):
        self.assertEqual(filetags.add_tag_to_countdict('tag', {}), {'tag': 1})
        self.assertEqual(filetags.add_tag_to_countdict('tag', {'tag': 0}), {'tag': 1})
        self.assertEqual(filetags.add_tag_to_countdict('tag', {'tag': 1}), {'tag': 2})
        self.assertEqual(filetags.add_tag_to_countdict('newtag', {'oldtag': 1}), {'oldtag': 1, 'newtag': 1})
        self.assertEqual(filetags.add_tag_to_countdict('newtag', {'oldtag': 2}), {'oldtag': 2, 'newtag': 1})

    def test_find_similar_tags(self):

        self.assertEqual(filetags.find_similar_tags('xxx', ['foobar', 'bar', 'baz', 'Frankenstein', 'parabol', 'Bah', 'paR', 'por', 'Schneewittchen']), [])

        self.assertEqual(filetags.find_similar_tags('Simpson', ['foobar', 'Simson', 'simpson', 'Frankenstein', 'sumpson', 'Simpso', 'impson', 'mpson', 'Schneewittchen']),
                         ['impson', 'Simson', 'Simpso', 'simpson', 'mpson', 'sumpson'])

    def test_check_for_possible_shortcuts_in_entered_tags(self):

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['bar'],
                                                                               ['Frankenstein', 'Schneewittchen']),
                         ['bar'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['34'],
                                                                               ['Frankenstein', 'Schneewittchen', 'baz', 'bar']),
                         ['baz', 'bar'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['12'],
                                                                               ['Frankenstein', 'Schneewittchen', 'baz', 'bar']),
                         ['Frankenstein', 'Schneewittchen'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['59'],
                                                                               ['Frankenstein', 'Schneewittchen', 'baz', 'bar']),
                         ['59'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['baz', '12', '88'],
                                                                               ['Frankenstein', 'Schneewittchen', 'baz', 'bar']),
                         ['baz', 'Frankenstein', 'Schneewittchen', '88'])

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags(['19', '88', 'baz'],
                                                                               ['Frankenstein', 'Schneewittchen', 'baz', 'bar']),
                         ['19', '88', 'baz'])

    def test_get_upto_nine_keys_of_dict_with_highest_value(self):

        self.assertEqual(filetags.get_upto_nine_keys_of_dict_with_highest_value({"key2": 45, "key1": 33}), ["key1", "key2"])

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
                                                                     'file4 -- common foo bar jodel.txt'])), set(['common', 'foo']))

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
        self.assertEqual(filetags.extract_iso_datestamp_from_filename('2018-03-18T23.59 foo bar'), ['2018', '03', '18'])

    def tearDown(self):

        pass


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

        os.sync()

    def create_tmp_file(self, name):

        with open(os.path.join(self.tempdir, name), 'w') as outputhandle:
            outputhandle.write('This is a test file for filetags unit testing')

    def file_exists(self, name):

        return os.path.isfile(os.path.join(self.tempdir, name))

    def test_add_and_remove_tags(self):

        # adding a tag to a file without any tags:
        filetags.handle_file(os.path.join(self.tempdir, self.testfilename), ['bar'], do_remove=False, do_filter=False, dryrun=False)
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
        dummy_filename = filetags.handle_file(os.path.join(self.tempdir, self.testfilename), ['teststring1'], do_remove=False, do_filter=False, dryrun=False)
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
        filetags.handle_file(os.path.join(self.tempdir, filename), ['foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(filename + ' -- foo'), True)

    # there is no such function: filetags.list_tags_by_number()
    def NOtest_list_tags_by_number(self):

        # starting with no file with tags:
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {})

        # adding a file tag:
        filetags.handle_file(os.path.join(self.tempdir, self.testfilename), ['bar'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {'bar': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=0), {'bar': 1})

        # adding a another file tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- bar.txt'), ['foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {'bar': 1, 'foo': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=0), {'bar': 1, 'foo': 1})

        # adding a another file:
        self.create_tmp_file('a second file')
        filetags.handle_file(os.path.join(self.tempdir, 'a second file'), ['foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {'bar': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {'bar': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=0), {'bar': 1, 'foo': 2})

    # there is no such function: filetags.list_tags_by_aphabet()
    def NOtest_list_tags_by_alphabet(self):

        # starting with no file with tags:
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})

        # adding a file tag:
        filetags.handle_file(os.path.join(self.tempdir, self.testfilename), ['similar1'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False), {'similar1': 1})

        # adding a file tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a test file . for you -- similar1.txt'), ['foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False), {'foo': 1, 'similar1': 1})

        # adding a another file:
        self.create_tmp_file('a second file')
        filetags.handle_file(os.path.join(self.tempdir, 'a second file'), ['foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False), {'foo': 2, 'similar1': 1})

        # adding similar tag:
        filetags.handle_file(os.path.join(self.tempdir, 'a second file -- foo'), ['similar2'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {'similar1': 1, 'similar2': 1})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False), {'foo': 2, 'similar1': 1, 'similar2': 1})

    def tearDown(self):

        rmtree(self.tempdir)


class TestHierarchyWithFilesAndFolders(unittest.TestCase):

    tempdir = None

    def setUp(self):

        # create temporary directory:
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        print("\nTestHierarchyWithFilesAndFolders: temporary directory: " + self.tempdir)

        # initial tests without files:
        self.assertEqual(filetags.get_tags_from_files_and_subfolders(self.tempdir, use_cache=False), {})

        # create set of test files:
        self.create_tmp_file("foo1 -- bar.txt")
        self.create_tmp_file("foo2 -- bar baz.txt")
        self.create_tmp_file("foo3 -- bar baz teststring1.txt")

        os.sync()

    def create_tmp_file(self, name):

        with open(os.path.join(self.tempdir, name), 'w') as outputhandle:
            outputhandle.write('This is a test file for filetags unit testing')

    def file_exists(self, name):

        return os.path.isfile(os.path.join(self.tempdir, name))

    def test_vocabulary_in_real_world_example(self):

        print("FIXXME: test_vocabulary_in_real_world_example needs vocabulary + tests")

    def test_get_tags_from_files_and_subfolders(self):

        self.assertEqual(filetags.get_tags_from_files_and_subfolders(self.tempdir, use_cache=False), {'baz': 2, 'bar': 3, 'teststring1': 1})

        # FIXXME: write test which tests the cache

    def test_list_unknown_tags(self):

        print("FIXXME: test_list_unknown_tags() not implemented yet")

    def test_handle_tag_gardening(self):

        print("FIXXME: test_handle_tag_gardening() not implemented yet")

    def test_locate_and_parse_controlled_vocabulary(self):

        print("FIXXME: test_locate_and_parse_controlled_vocabulary() not implemented yet")

    def tearDown(self):

        rmtree(self.tempdir)


class TestReplacingSymlinkSourceAndTarget(unittest.TestCase):

    tempdir = None

    SOURCEFILE1 = 'source file 1 - same tags -- bar.txt'
    LINKFILE1 = 'symlink file 1 - same tags -- bar.txt'

    SOURCEFILE2 = 'source file 2 - source has tag and symlink not -- baz.txt'
    LINKFILE2 = 'symlink file 2 - source has tag and symlink not.txt'

    SOURCEFILE3 = 'source file 3 - source no tags and symlink has.txt'
    LINKFILE3 = 'symlink file 3 - source no tags and symlink has -- baz.txt'

    TESTFILE1 = 'symlink and source same name.txt'

    def setUp(self):

        # create temporary directory for the source files:
        self.sourcedir = tempfile.mkdtemp(prefix='sources')
        self.symlinkdir = tempfile.mkdtemp(prefix='symlinks')

        os.chdir(self.sourcedir)
        logging.info("\nTestReplacingSymlinkSourceAndTarget: sourcedir: " + self.sourcedir + " and symlinkdir: " + self.symlinkdir)

        # create set of test files:
        self.create_source_file(self.SOURCEFILE1)
        self.create_source_file(self.SOURCEFILE2)
        self.create_source_file(self.SOURCEFILE3)
        self.create_source_file(self.SOURCEFILE3)
        self.create_source_file(self.TESTFILE1)

        # create symbolic links:
        self.create_symlink_file(self.SOURCEFILE1, self.LINKFILE1)
        self.create_symlink_file(self.SOURCEFILE2, self.LINKFILE2)
        self.create_symlink_file(self.SOURCEFILE3, self.LINKFILE3)
        self.create_symlink_file(self.TESTFILE1, self.TESTFILE1)

        os.sync()

    def create_source_file(self, name):

        with open(os.path.join(self.sourcedir, name), 'w') as outputhandle:
            outputhandle.write('This is a test file for filetags unit testing')

    def create_symlink_file(self, source, destination):

        os.symlink(os.path.join(self.sourcedir, source), os.path.join(self.symlinkdir, destination))

    def source_file_exists(self, name):

        return os.path.isfile(os.path.join(self.sourcedir, name))

    def symlink_file_exists(self, name):

        return os.path.isfile(os.path.join(self.symlinkdir, name))

    def is_broken_link(self, name):

        # This function determines if the given name points to a file
        # that is a broken link. It returns False for any other cases
        # such as non existing files and so forth.

        if self.symlink_file_exists(name):
            return False

        try:
            return not os.path.exists(os.readlink(os.path.join(self.symlinkdir, name)))
        except FileNotFoundError:
            return False

    def tearDown(self):

        rmtree(self.sourcedir)
        rmtree(self.symlinkdir)

    def test_adding_tags_to_symlinks(self):

        filetags.handle_file_and_symlink_source_if_found(os.path.join(self.symlinkdir, self.LINKFILE1), ['foo'], do_remove=False, do_filter=False, dryrun=False)
        logging.info('only the symlink gets this tag because basenames differ:')
        self.assertEqual(self.symlink_file_exists('symlink file 1 - same tags -- bar foo.txt'), True)
        self.assertEqual(self.source_file_exists(self.SOURCEFILE1), True)

        logging.info('basenames are same, so both files should get the tag:')
        filetags.handle_file_and_symlink_source_if_found(os.path.join(self.symlinkdir, self.TESTFILE1), ['foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.symlink_file_exists('symlink and source same name -- foo.txt'), True)
        self.assertEqual(self.source_file_exists('symlink and source same name -- foo.txt'), True)

    def test_adding_tag_to_an_original_file_causing_broken_symlink(self):

        self.assertFalse(self.is_broken_link(self.TESTFILE1))
        filetags.handle_file_and_symlink_source_if_found(os.path.join(self.sourcedir, self.TESTFILE1), ['foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.source_file_exists('symlink and source same name -- foo.txt'), True)
        self.assertTrue(self.is_broken_link(self.TESTFILE1))

    def test_removing_tags(self):

        logging.info('removing a non existing tag should not change anything at all:')
        filetags.handle_file_and_symlink_source_if_found(os.path.join(self.symlinkdir, self.TESTFILE1), ['foo'], do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.source_file_exists(self.TESTFILE1), True)
        self.assertEqual(self.symlink_file_exists(self.TESTFILE1), True)

        logging.info('adding tags just for the next tests:')
        filetags.handle_file_and_symlink_source_if_found(os.path.join(self.symlinkdir, self.TESTFILE1), ['foo', 'bar'], do_remove=False, do_filter=False, dryrun=False)

        self.assertEqual(self.symlink_file_exists('symlink and source same name -- foo bar.txt'), True)
        self.assertEqual(self.source_file_exists('symlink and source same name -- foo bar.txt'), True)

        logging.info('removing tags which only exists partially:')
        filetags.handle_file_and_symlink_source_if_found(os.path.join(self.symlinkdir, 'symlink and source same name -- foo bar.txt'), ['baz', 'bar'], do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.symlink_file_exists('symlink and source same name -- foo.txt'), True)
        self.assertEqual(self.source_file_exists('symlink and source same name -- foo.txt'), True)

        logging.info('removing tags using minus-notation like "-foo"')
        filetags.handle_file_and_symlink_source_if_found(os.path.join(self.symlinkdir, 'symlink and source same name -- foo.txt'), ['-foo', 'bar'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.symlink_file_exists('symlink and source same name -- bar.txt'), True)
        self.assertEqual(self.source_file_exists('symlink and source same name -- bar.txt'), True)

if __name__ == '__main__':
    unittest.main()

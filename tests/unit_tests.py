#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2017-08-27 17:12:59 vk>

# invoke tests using following command line:
# ~/src/vktag % PYTHONPATH="~/src/filetags:" tests/unit_tests.py --verbose

import unittest
import os
import filetags
import tempfile
import os.path
from shutil import rmtree


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

    def create_tmp_file(self, name):

        open(os.path.join(self.tempdir, name), 'w')

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

    def create_tmp_file(self, name):

        open(os.path.join(self.tempdir, name), 'w')

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


if __name__ == '__main__':
    unittest.main()

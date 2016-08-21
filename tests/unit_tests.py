#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2016-08-21 18:51:58 vk>

## invoke tests using following command line:
## ~/src/vktag % PYTHONPATH="~/src/filetags:" tests/unit_tests.py --verbose

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

        self.assertEqual(filetags.contains_tag(u'Some file name -- foo.jpeg', u'foo'), True)
        self.assertEqual(filetags.contains_tag(u'Some file name -- foo bar.jpeg', u'foo'), True)
        self.assertEqual(filetags.contains_tag(u'Some file name -- bar foo.jpeg', u'foo'), True)
        self.assertEqual(filetags.contains_tag(u'Some file name -- foobar.jpeg', u'foo'), False)
        self.assertEqual(filetags.contains_tag(u'Some file name -- foo.jpeg', u'bar'), False)
        self.assertEqual(filetags.contains_tag(u'Some foo file name -- bar.jpeg', u'foo'), False)

        ## without tagname -> check if any tags are found:
        self.assertEqual(filetags.contains_tag(u'Some file name -- foo.jpeg'), True)
        self.assertEqual(filetags.contains_tag(u'Some file name -- foo bar.jpeg'), True)
        self.assertEqual(filetags.contains_tag(u'Some file name.jpeg'), False)

    def test_adding_tag_to_filename(self):

        self.assertEqual(filetags.adding_tag_to_filename(u'Some file name.jpeg', u'bar'),
                         u'Some file name -- bar.jpeg')
        self.assertEqual(filetags.adding_tag_to_filename(u'Some file name -- foo.jpeg', u'bar'),
                         u'Some file name -- foo bar.jpeg')
        self.assertEqual(filetags.adding_tag_to_filename(u'Some file name -- foo.jpeg', u'foo'),
                         u'Some file name -- foo.jpeg')

    def test_removing_tag_from_filename(self):

        self.assertEqual(filetags.removing_tag_from_filename(u'Some file name -- bar.jpeg', u'bar'),
                         u'Some file name.jpeg')
        self.assertEqual(filetags.removing_tag_from_filename(u'Some file name -- foo bar.jpeg', u'bar'),
                         u'Some file name -- foo.jpeg')
        self.assertEqual(filetags.removing_tag_from_filename(u'Some file name -- bar.jpeg', u'foo'),
                         u'Some file name -- bar.jpeg')

    def test_extract_tags_from_filename(self):
        self.assertEqual(filetags.extract_tags_from_filename(u'Some file name - bar.jpeg'), [])
        self.assertEqual(filetags.extract_tags_from_filename(u'-- bar.jpeg'), [])
        self.assertEqual(filetags.extract_tags_from_filename(u'Some file name.jpeg'), [])
        self.assertEqual(filetags.extract_tags_from_filename(u'Some file name - bar.jpeg'), [])
        self.assertEqual(filetags.extract_tags_from_filename(u'Some file name -- bar.jpeg'), [u'bar'])
        self.assertEqual(filetags.extract_tags_from_filename(u'Some file name -- foo bar baz.jpeg'),
                         [u'foo', u'bar', u'baz'])
        self.assertEqual(filetags.extract_tags_from_filename(u'Some file name -- foo bar baz'),
                         [u'foo', u'bar', u'baz'])

    def test_add_tag_to_countdict(self):
        self.assertEqual(filetags.add_tag_to_countdict(u'tag', {}), {u'tag': 1})
        self.assertEqual(filetags.add_tag_to_countdict(u'tag', {u'tag': 0}), {u'tag': 1})
        self.assertEqual(filetags.add_tag_to_countdict(u'tag', {u'tag': 1}), {u'tag': 2})
        self.assertEqual(filetags.add_tag_to_countdict(u'newtag', {u'oldtag': 1}), {u'oldtag': 1, u'newtag': 1})
        self.assertEqual(filetags.add_tag_to_countdict(u'newtag', {u'oldtag': 2}), {u'oldtag': 2, u'newtag': 1})

    def test_find_similar_tags(self):

        self.assertEqual(filetags.find_similar_tags(u'xxx', [u'foobar', u'bar', u'baz', u'Frankenstein', u'parabol', u'Bah', u'paR', u'por', u'Schneewittchen']), [])

        self.assertEqual(filetags.find_similar_tags(u'Simpson', [u'foobar', u'Simson', u'simpson', u'Frankenstein', u'sumpson', u'Simpso', u'impson', u'mpson', u'Schneewittchen']), \
                                                    [u'impson', u'Simson', u'Simpso', u'simpson', u'mpson', u'sumpson'])

    def test_check_for_possible_shortcuts_in_entered_tags(self):

        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags([u'bar'], [u'Frankenstein', u'Schneewittchen']), [u'bar'])
        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags([u'34'], [u'Frankenstein', u'Schneewittchen', u'baz', u'bar']), [u'baz', u'bar'])
        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags([u'12'], [u'Frankenstein', u'Schneewittchen', u'baz', u'bar']), [u'Frankenstein', u'Schneewittchen'])
        self.assertEqual(filetags.check_for_possible_shortcuts_in_entered_tags([u'39'], [u'Frankenstein', u'Schneewittchen', u'baz', u'bar']), [u'39'])

    def test_get_upto_nine_keys_of_dict_with_highest_value(self):

        self.assertEqual(filetags.get_upto_nine_keys_of_dict_with_highest_value({ "key2":45, "key1": 33}), [ "key1", "key2" ])
        self.assertEqual(filetags.get_upto_nine_keys_of_dict_with_highest_value({ "key1":45, "key2": 33, "key3": 3, "key4": 1, "key5": 5, "key6": 159, "key7": 0, "key8": 999, "key9": 42, "key10": 4242}), \
                         [ "key1", "key10", "key2", "key3", "key4", "key5", "key6", "key8", "key9"])

    def tearDown(self):

        pass


class TestFileWithoutTags(unittest.TestCase):

    tempdir = None
    testfilename = 'a test file . for you.txt'

    def setUp(self):

        ## create temporary directory:
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        print "\nTestFileWithoutTags: temporary directory: " + self.tempdir

        ## create set of test files:
        self.create_tmp_file(self.testfilename)

        ## double-check set-up:
        self.assertTrue(self.file_exists(self.testfilename))

    def create_tmp_file(self, name):

        open(os.path.join(self.tempdir, name), 'w')

    def file_exists(self, name):

        return os.path.isfile(os.path.join(self.tempdir, name))

    def test_add_and_remove_tags(self):

        ## adding a tag to a file without any tags:
        filetags.handle_file(os.path.join(self.tempdir, self.testfilename), [u'bar'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- bar.txt'), True)

        ## adding a second tag:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar.txt'),
                            [u'foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- bar foo.txt'), True)

        ## adding two tags:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar foo.txt'),
                            [u'one', u'two'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- bar foo one two.txt'), True)

        ## simulating another tag:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar foo one two.txt'),
                            [u'one', u'two'], do_remove=False, do_filter=False, dryrun=True)
        self.assertEqual(self.file_exists(u'a test file . for you -- bar foo one two.txt'), True)

        ## removing three tag:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar foo one two.txt'),
                            [u'bar', u'one', u'foo'], do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- two.txt'), True)

        ## removing last tag:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- two.txt'),
                            [u'two'], do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you.txt'), True)

    def test_unique_tags(self):

        ## Note: default unique_tags is a hard-coded list of u'teststring1' and u'teststring2'

        ## adding a unique tag to a file without any tags:
        new_filename = filetags.handle_file(os.path.join(self.tempdir, self.testfilename), [u'teststring1'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- teststring1.txt'), True)

        ## adding a second unique tag - first one should be gone:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- teststring1.txt'),
                            [u'teststring2'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- teststring2.txt'), True)

        ## adding non-unique tags:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- teststring2.txt'),
                            [u'one', u'two'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- teststring2 one two.txt'), True)

        ## removing unique tag:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- teststring2 one two.txt'),
                            [u'teststring2', u'one'], do_remove=True, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- two.txt'), True)

    def test_adding_a_tag_to_file_without_extension(self):

        filename = u"file without extension"
        self.create_tmp_file(filename)
        filetags.handle_file(os.path.join(self.tempdir, filename), [u'foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(self.file_exists(filename + u' -- foo'), True)

    def test_list_tags_by_number(self):

        ## starting with no file with tags:
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {})

        ## adding a file tag:
        filetags.handle_file(os.path.join(self.tempdir, self.testfilename), [u'bar'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {u'bar': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=0), {u'bar': 1})

        ## adding a another file tag:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar.txt'), [u'foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {u'bar': 1, u'foo': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=0), {u'bar': 1, u'foo': 1})

        ## adding a another file:
        self.create_tmp_file(u'a second file')
        filetags.handle_file(os.path.join(self.tempdir, u'a second file'), [u'foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {u'bar': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=1), {u'bar': 1})
        self.assertEqual(filetags.list_tags_by_number(max_tag_count=0), {u'bar': 1, u'foo': 2})

    def test_list_tags_by_alphabet(self):

        ## starting with no file with tags:
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})

        ## adding a file tag:
        filetags.handle_file(os.path.join(self.tempdir, self.testfilename), [u'similar1'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False), {u'similar1': 1})

        ## adding a file tag:
        filetags.handle_file(os.path.join(self.tempdir, u'a test file . for you -- similar1.txt'), [u'foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False), {u'foo': 1, u'similar1': 1})

        ## adding a another file:
        self.create_tmp_file(u'a second file')
        filetags.handle_file(os.path.join(self.tempdir, u'a second file'), [u'foo'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False), {u'foo': 2, u'similar1': 1})

        ## adding similar tag:
        filetags.handle_file(os.path.join(self.tempdir, u'a second file -- foo'), [u'similar2'], do_remove=False, do_filter=False, dryrun=False)
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=True), {u'similar1': 1, u'similar2': 1})
        self.assertEqual(filetags.list_tags_by_alphabet(only_with_similar_tags=False), {u'foo': 2, u'similar1': 1, u'similar2': 1})

    def tearDown(self):

        rmtree(self.tempdir)


class TestHierarchyWithFilesAndFolders(unittest.TestCase):

    tempdir = None

    def setUp(self):

        ## create temporary directory:
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        print "\nTestHierarchyWithFilesAndFolders: temporary directory: " + self.tempdir

        ## initial tests without files:
        self.assertEqual(filetags.get_tags_from_files_and_subfolders(self.tempdir, False, False), {})

        ## create set of test files:
        self.create_tmp_file("foo1 -- bar.txt")
        self.create_tmp_file("foo2 -- bar baz.txt")
        self.create_tmp_file("foo3 -- bar baz teststring1.txt")

    def create_tmp_file(self, name):

        open(os.path.join(self.tempdir, name), 'w')

    def file_exists(self, name):

        return os.path.isfile(os.path.join(self.tempdir, name))

    def test_vocabulary_in_real_world_example(self):

        print "FIXXME: test_vocabulary_in_real_world_example needs vocabulary + tests"

    def test_get_tags_from_files_and_subfolders(self):

        self.assertEqual(filetags.get_tags_from_files_and_subfolders(self.tempdir, False, False), {u'baz': 2, u'bar': 3, u'teststring1': 1})

    def test_list_unknown_tags(self):

        print "FIXXME: test_list_unknown_tags() not implemented yet"

    def test_handle_tag_gardening(self):

        print "FIXXME: test_handle_tag_gardening() not implemented yet"

    def test_locate_and_parse_controlled_vocabulary(self):

        print "FIXXME: test_locate_and_parse_controlled_vocabulary() not implemented yet"


    def tearDown(self):

        rmtree(self.tempdir)


if __name__ == '__main__':
    unittest.main()

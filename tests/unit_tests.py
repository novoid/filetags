#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2014-12-20 22:21:19 vk>

## invoke tests using following command line:
## ~/src/vktag % PYTHONPATH="~/src/filetag:" tests/unit_tests.py --verbose

import unittest
import os
import filetag
import tempfile
import os.path
from shutil import rmtree


class TestMethods(unittest.TestCase):

    def setUp(self):
        pass

    def test_contains_tag(self):

        self.assertEqual(filetag.contains_tag(u'Some file name -- foo.jpeg', u'foo'), True)
        self.assertEqual(filetag.contains_tag(u'Some file name -- foo bar.jpeg', u'foo'), True)
        self.assertEqual(filetag.contains_tag(u'Some file name -- bar foo.jpeg', u'foo'), True)
        self.assertEqual(filetag.contains_tag(u'Some file name -- foobar.jpeg', u'foo'), False)
        self.assertEqual(filetag.contains_tag(u'Some file name -- foo.jpeg', u'bar'), False)
        self.assertEqual(filetag.contains_tag(u'Some foo file name -- bar.jpeg', u'foo'), False)

        ## without tagname -> check if any tags are found:
        self.assertEqual(filetag.contains_tag(u'Some file name -- foo.jpeg'), True)
        self.assertEqual(filetag.contains_tag(u'Some file name -- foo bar.jpeg'), True)
        self.assertEqual(filetag.contains_tag(u'Some file name.jpeg'), False)

    def test_adding_tag_to_filename(self):

        self.assertEqual(filetag.adding_tag_to_filename(u'Some file name.jpeg', u'bar'),
                         u'Some file name -- bar.jpeg')
        self.assertEqual(filetag.adding_tag_to_filename(u'Some file name -- foo.jpeg', u'bar'),
                         u'Some file name -- foo bar.jpeg')
        self.assertEqual(filetag.adding_tag_to_filename(u'Some file name -- foo.jpeg', u'foo'),
                         u'Some file name -- foo.jpeg')

    def test_removing_tag_from_filename(self):

        self.assertEqual(filetag.removing_tag_from_filename(u'Some file name -- bar.jpeg', u'bar'),
                         u'Some file name.jpeg')
        self.assertEqual(filetag.removing_tag_from_filename(u'Some file name -- foo bar.jpeg', u'bar'),
                         u'Some file name -- foo.jpeg')
        self.assertEqual(filetag.removing_tag_from_filename(u'Some file name -- bar.jpeg', u'foo'),
                         u'Some file name -- bar.jpeg')

    def test_extract_tags_from_filename(self):
        self.assertEqual(filetag.extract_tags_from_filename(u'Some file name - bar.jpeg'), [])
        self.assertEqual(filetag.extract_tags_from_filename(u'-- bar.jpeg'), [])
        self.assertEqual(filetag.extract_tags_from_filename(u'Some file name.jpeg'), [])
        self.assertEqual(filetag.extract_tags_from_filename(u'Some file name - bar.jpeg'), [])
        self.assertEqual(filetag.extract_tags_from_filename(u'Some file name -- bar.jpeg'), [u'bar'])
        self.assertEqual(filetag.extract_tags_from_filename(u'Some file name -- foo bar baz.jpeg'),
                         [u'foo', u'bar', u'baz'])
        self.assertEqual(filetag.extract_tags_from_filename(u'Some file name -- foo bar baz'),
                         [u'foo', u'bar', u'baz'])

    def test_add_tag_to_countdict(self):
        self.assertEqual(filetag.add_tag_to_countdict(u'tag', {}), {u'tag': 1})
        self.assertEqual(filetag.add_tag_to_countdict(u'tag', {u'tag': 0}), {u'tag': 1})
        self.assertEqual(filetag.add_tag_to_countdict(u'tag', {u'tag': 1}), {u'tag': 2})
        self.assertEqual(filetag.add_tag_to_countdict(u'newtag', {u'oldtag': 1}), {u'oldtag': 1, u'newtag': 1})
        self.assertEqual(filetag.add_tag_to_countdict(u'newtag', {u'oldtag': 2}), {u'oldtag': 2, u'newtag': 1})

    def tearDown(self):

        pass


class TestFileWithoutTags(unittest.TestCase):

    tempdir = None
    testfilename = 'a test file . for you.txt'

    def setUp(self):

        ## create temporary directory:
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        print "\ntemporary directory: " + self.tempdir

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
        filetag.handle_file(os.path.join(self.tempdir, self.testfilename), [u'bar'], False, False)
        self.assertEqual(self.file_exists(u'a test file . for you -- bar.txt'), True)

        ## adding a second tag:
        filetag.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar.txt'),
                            [u'foo'], do_remove=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- bar foo.txt'), True)

        ## adding two tags:
        filetag.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar foo.txt'),
                            [u'one', u'two'], do_remove=False, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- bar foo one two.txt'), True)

        ## simulating another tag:
        filetag.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar foo one two.txt'),
                            [u'one', u'two'], do_remove=False, dryrun=True)
        self.assertEqual(self.file_exists(u'a test file . for you -- bar foo one two.txt'), True)

        ## removing three tag:
        filetag.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar foo one two.txt'),
                            [u'bar', u'one', u'foo'], do_remove=True, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you -- two.txt'), True)

        ## removing last tag:
        filetag.handle_file(os.path.join(self.tempdir, u'a test file . for you -- two.txt'),
                            [u'two'], do_remove=True, dryrun=False)
        self.assertEqual(self.file_exists(u'a test file . for you.txt'), True)

    def test_adding_a_tag_to_file_without_extension(self):

        filename = u"file without extension"
        self.create_tmp_file(filename)
        filetag.handle_file(os.path.join(self.tempdir, filename), [u'foo'], False, False)
        self.assertEqual(self.file_exists(filename + u' -- foo'), True)

    def test_list_tags_by_number(self):

        ## starting with no file with tags:
        self.assertEqual(filetag.list_tags_by_number(max_tag_count=1), {})

        ## adding a file tag:
        filetag.handle_file(os.path.join(self.tempdir, self.testfilename), [u'bar'], False, False)
        self.assertEqual(filetag.list_tags_by_number(max_tag_count=1), {u'bar': 1})
        self.assertEqual(filetag.list_tags_by_number(max_tag_count=0), {u'bar': 1})

        ## adding a another file tag:
        filetag.handle_file(os.path.join(self.tempdir, u'a test file . for you -- bar.txt'), [u'foo'], False, False)
        self.assertEqual(filetag.list_tags_by_number(max_tag_count=1), {u'bar': 1, u'foo': 1})
        self.assertEqual(filetag.list_tags_by_number(max_tag_count=0), {u'bar': 1, u'foo': 1})

        ## adding a another file:
        self.create_tmp_file(u'a second file')
        filetag.handle_file(os.path.join(self.tempdir, u'a second file'), [u'foo'], False, False)
        self.assertEqual(filetag.list_tags_by_number(max_tag_count=1), {u'bar': 1})
        self.assertEqual(filetag.list_tags_by_number(max_tag_count=1), {u'bar': 1})
        self.assertEqual(filetag.list_tags_by_number(max_tag_count=0), {u'bar': 1, u'foo': 2})

    def test_list_tags_by_alphabet(self):

        ## starting with no file with tags:
        self.assertEqual(filetag.list_tags_by_alphabet(only_with_similar_tags=True), {})

        ## adding a file tag:
        filetag.handle_file(os.path.join(self.tempdir, self.testfilename), [u'similar1'], False, False)
        self.assertEqual(filetag.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetag.list_tags_by_alphabet(only_with_similar_tags=False), {u'similar1': 1})

        ## adding a file tag:
        filetag.handle_file(os.path.join(self.tempdir, u'a test file . for you -- similar1.txt'), [u'foo'], False, False)
        self.assertEqual(filetag.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetag.list_tags_by_alphabet(only_with_similar_tags=False), {u'foo': 1, u'similar1': 1})

        ## adding a another file:
        self.create_tmp_file(u'a second file')
        filetag.handle_file(os.path.join(self.tempdir, u'a second file'), [u'foo'], False, False)
        self.assertEqual(filetag.list_tags_by_alphabet(only_with_similar_tags=True), {})
        self.assertEqual(filetag.list_tags_by_alphabet(only_with_similar_tags=False), {u'foo': 2, u'similar1': 1})

        ## adding similar tag:
        filetag.handle_file(os.path.join(self.tempdir, u'a second file -- foo'), [u'similar2'], False, False)
        self.assertEqual(filetag.list_tags_by_alphabet(only_with_similar_tags=True), {u'similar1': 1, u'similar2': 1})
        self.assertEqual(filetag.list_tags_by_alphabet(only_with_similar_tags=False), {u'foo': 2, u'similar1': 1, u'similar2': 1})

    def tearDown(self):

        rmtree(self.tempdir)


if __name__ == '__main__':
    unittest.main()

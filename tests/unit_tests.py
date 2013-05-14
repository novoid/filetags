#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2013-05-14 18:21:24 vk>

## invoke tests using following command line:
## ~/src/vktag % PYTHONPATH="~/src/vktag:" tests/unit_tests.py --verbose

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

        self.assertEqual(filetag.adding_tag_to_filename(u'Some file name.jpeg', u'bar'), \
                             u'Some file name -- bar.jpeg')
        self.assertEqual(filetag.adding_tag_to_filename(u'Some file name -- foo.jpeg', u'bar'), \
                             u'Some file name -- foo bar.jpeg')
        self.assertEqual(filetag.adding_tag_to_filename(u'Some file name -- foo.jpeg', u'foo'), \
                             u'Some file name -- foo.jpeg')


    def test_removing_tag_from_filename(self):

        self.assertEqual(filetag.removing_tag_from_filename(u'Some file name -- bar.jpeg', u'bar'), \
                             u'Some file name.jpeg')
        self.assertEqual(filetag.removing_tag_from_filename(u'Some file name -- foo bar.jpeg', u'bar'), \
                             u'Some file name -- foo.jpeg')
        self.assertEqual(filetag.removing_tag_from_filename(u'Some file name -- bar.jpeg', u'foo'), \
                             u'Some file name -- bar.jpeg')


    def tearDown(self):
        
        pass
        

class NO_TestFiles(unittest.TestCase):

    tempdir = None
    testfile_without_tags = 'file_without_tags.txt'
    testfile_with_multiple_dots_and_no_tags = 'file.without.tags.txt'
    testfile_with_tag_foo = 'filename -- foo.txt'
    testfile_with_tag_bar = 'filename -- bar.txt'

    def setUp(self):

        ## create temporary directory:
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        print "\ntemporary directory: " + self.tempdir

        ## create set of test files:
        self.create_tmp_file(self.testfile_without_tags)
        self.create_tmp_file(self.testfile_with_multiple_dots_and_no_tags)
        self.create_tmp_file(self.testfile_with_tag_foo)
        self.create_tmp_file(self.testfile_with_tag_bar)

        ## double-check set-up:
        self.assertTrue(self.file_exists(self.testfile_without_tags))


    def create_tmp_file(self, name):
        
        open(os.path.join(self.tempdir, name), 'w')


    def file_exists(self, name):
        
        return os.path.isfile(os.path.join(self.tempdir, name))


    def test_all(self):

        print "testing: foo bar\n"
        self.assertEqual(3 * 4, 12)


    def tearDown(self):
        
        rmtree(self.tempdir)
        

if __name__ == '__main__':
    unittest.main()

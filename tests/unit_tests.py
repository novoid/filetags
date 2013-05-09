#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2013-05-09 17:41:54 vk>

## ~/src/vktag % PYTHONPATH="~/src/vktag:" tests/unit_tests.py --verbose

import unittest
import os
import filetag
import tempfile
import os.path
from shutil import rmtree

class TestFoo(unittest.TestCase):

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

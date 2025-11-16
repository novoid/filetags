# from distutils.core import setup

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

# workaround from https://github.com/pypa/setuptools/issues/308 to avoid "normalizing" version "2018.01.09" to "2018.1.9":
# 2019-03-08: got error
#    vk@sherri ~/src/filetags (git)-[master] % ./update_pip.sh
#    Traceback (most recent call last):
#      File "setup.py", line 11, in <module>
#        pkg_resources.extern.packaging.version.Version = pkg_resources.SetuptoolsLegacyVersion
#    AttributeError: module 'pkg_resources' has no attribute 'SetuptoolsLegacyVersion'
#    1 vk@sherri ~/src/filetags (git)-[master] %
#import pkg_resources
#pkg_resources.extern.packaging.version.Version = pkg_resources.SetuptoolsLegacyVersion

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
#with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
#    long_description = f.read()

setup(
    name="filetags",
    version="2024.02.12.1",
    description="Management of simple tags within file names",
    author="Karl Voit",
    author_email="tools@Karl-Voit.at",
    url="https://github.com/novoid/filetags",
    download_url="https://github.com/novoid/filetags/zipball/master",
    keywords=["tagging", "tags", "file managing", "file management", "files", "tagtrees", "tagstore", "tag-based navigation", "tag-based filter"],
    packages=find_packages(), # Required
    package_data={'filetags': ['Register_filetags_for_Windows_context_menu_TEMPLATE.reg']},
    install_requires=["colorama", "pyreadline3", "clint"],
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        ],
    entry_points={  # Optional
        'console_scripts': [
            'filetags=filetags:main'
        ],
    },
#    long_description=long_description, # Optional
    long_description="""This Python script adds or removes tags to file names in the following
form:

- file without time stamp in name -- tag2.txt
- file name with several tags -- tag1 tag2.jpeg
- another example file name with multiple example tags -- fun videos kids.mpeg
- 2013-05-09 a file name with ISO date stamp in name -- tag1.jpg
- 2013-05-09T16.17 file name with time stamp -- tag3.csv

The script accepts an arbitrary number of files (see your shell for
possible length limitations).

- Target group: users who are able to use command line tools and who
  are using tags in file names.
- Hosted and documented on github: https://github.com/novoid/filetags
"""
)

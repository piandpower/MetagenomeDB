#!/usr/bin/env python

from distutils.core import setup
from glob import glob

setup(
	name = "MetagenomeDB",
	description = "Metagenome sequences and annotations database",
	long_description = open("README.rst").read(),
	classifiers = [
		"Development Status :: 4 - Beta",
		"Environment :: Console",
		"Intended Audience :: Science/Research",
		"License :: OSI Approved :: MIT License",
		"Natural Language :: English",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 2.6",
		"Topic :: Database :: Front-Ends",
		"Topic :: Scientific/Engineering :: Bio-Informatics",
	],
	version = "0.2.0b",
	license = "LICENSE.txt",
	author = "Aurelien Mazurie",
	author_email = "ajmazurie@oenone.net",
	url = "https://github.com/ajmazurie/MetagenomeDB",
	packages = ["MetagenomeDB"],
	scripts = glob("tools/*"),
)


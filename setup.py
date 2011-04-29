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
	version = open("VERSION.txt").read().strip(),
	license = open("LICENSE.txt").read(),
	author = "Aurelien Mazurie",
	author_email = "ajmazurie@oenone.net",
	url = "https://github.com/BioinformaticsCore/MetagenomeDB",
	packages = ["MetagenomeDB", "MetagenomeDB.utils"],
	package_dir = {'': "lib"},
	scripts = glob("tools/*"),
)


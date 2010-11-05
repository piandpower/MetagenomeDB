#!/usr/bin/env python

from distutils.core import setup

setup(
	name = "MetagenomeDB",
	description = "Metagenome sequences and annotations database",
	version = "0.1.8960110",
	author = "Aurelien Mazurie",
	author_email = "ajmazurie@oenone.net",
	url = "https://github.com/ajmazurie/MetagenomeDB",
	packages = ["MetagenomeDB"],
	data_files = [("/usr/bin", ["tools/mdb-add"])]
)


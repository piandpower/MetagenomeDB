#!/usr/bin/env python

# Example: retrieval of all sequence alignments using MetagenomeDB

import MetagenomeDB as mdb

for alignment in mdb.Relationship.select(type = "similar-to"):

	# retrieve the two sequence objects
	source = alignment["source"]
	target = alignment["target"]

	# list the collection(s) these sequences belong to
	source_collections = []
	for (collection, relationship) in source.get_collections():
		source_collections.append(collection["name"])

	target_collections = []
	for (collection, relationship) in target.get_collections():
		target_collections.append(collection["name"])

	algorithm = alignment["run.algorithm.name"]

	print "Alignment of %s (%s) against %s (%s) using %s:" % (
		source["name"], ', '.join(source_collections),
		target["name"], ', '.join(target_collections),
		algorithm
	)

	print "\n  %s %s" % (alignment["alignment.source"], alignment["source-coordinates"])
	print "  %s" % alignment["alignment.conservation"]
	print "  %s %s" % (alignment["alignment.target"], alignment["target-coordinates"])

	print "\n  E-value: %s, Fraction identical: %s\n" % (
		alignment["score.expectation.e-value"],
		alignment["score.fraction-conserved"]
	)

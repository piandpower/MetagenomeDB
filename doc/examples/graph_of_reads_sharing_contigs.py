#!/usr/bin/env python

### Parameters for this script; you can modify them at will:
# collection of contigs to extract a network from
contigs_collection = "my collection"

# filename for the Cytoscape-formatted network
network_fn = "network.sif"

# filename for the edges annotations (fraction of shared reads, as the Jaccard similarity)
edges_annotations_fn = "edges_annotations.txt"

# filename for the vertices annotations (length of the contig)
vertices_annotations_fn = "vertices_annotations.txt"
###

# first step, we import the MetagenomeDB API.
import MetagenomeDB as mdb

# we also import some other libraries
import sys

# then we check if the contigs' collection exists
cc = mdb.Collection.find_one({"name": contigs_collection})

if (cc == None):
	print >>sys.stderr, "ERROR: no collection found with name '%s'" % contigs_collection
	sys.exit(1)

# we retrieve a list of all contigs in this collection; in our
# example we request all sequences in the collection with a value
# 'contig' for the property 'class'. However, this is optional if
# you do know your collection only contains contigs.
contigs = list(cc.list_sequences({"class": "contig"}))

print "number of contigs to consider: %s" % len(contigs)

# we create a dictionary to store edges
edges = {}

def order (a, b):
	if (a > b):
		return b, a
	else:
		return a, b

# we now iterate through all non-redundant pairs of contigs:
n = len(contigs) * (len(contigs) - 1) / 2
c = 0

print "number of pairs of contigs to consider: %s" % n

for i, contig_a in enumerate(contigs):

	# for each contig in contig_a we request the list of the
	# reads that has been used for its assembly. Those are
	# sequences that are related to the contig and have (for
	# example) a value 'read' for the property 'class'
	reads_a = contig_a.list_related_sequences(mdb.Direction.INGOING, {"class": "read"})

	for contig_b in contigs[i+1:]:

		# similarily, we request the reads for contig_b
		reads_b = contig_b.list_related_sequences(mdb.Direction.INGOING, {"class": "read"})

		# for speed purpose in the computation below we will
		# transform this later list of reads into a dictionary
		reads_b = {}.fromkeys(reads_b)

		# we then check if those two lists overlap; we also
		# calculate the Jaccard similarity, as the cardinal
		# of the intersection of the two lists divided by
		# the cardinal of their union.
		union, intersection = {}, {}

		for item in reads_a:
			if (item in reads_b):
				intersection[item] = True

			union[item] = True

		for item in reads_b:
			union[item] = True

		jaccard_similarity = 100.0 * len(intersection) / len(union)

		# if we do have some overlap, then we store this edge
		if (jaccard_similarity > 0):
			edges[order(contig_a, contig_b)] = jaccard_similarity

		# we display some information about our progress
		c += 1
		p = 100.0 * c / n
		if (p % 5 == 0):
			print "%d%% done" % p

# we now save those edges and their annotations (Jaccard similarity)
network_fh = open(network_fn, 'w')
edges_annotations_fh = open(edges_annotations_fn, 'w')
print >>edges_annotations_fh, "shared_reads"

nodes = {}
for (contig_a, contig_b) in sorted(edges.keys()):
	print >>network_fh, "%s	shared_reads	%s" % (contig_a["name"], contig_b["name"])
	print >>edges_annotations_fh, "%s (shared_reads) %s = %s" % (contig_a["name"], contig_b["name"], edges[(contig_a, contig_b)])

	nodes[contig_a] = True
	nodes[contig_b] = True

# finally, we store the nodes annotations (contigs' length)
vertices_annotations_fh = open(vertices_annotations_fn, 'w')
print >>vertices_annotations_fh, "contig_length"

for contig in sorted(nodes.keys()):
	print >>vertices_annotations_fh, "%s = %s" % (contig["name"], contig["length"])

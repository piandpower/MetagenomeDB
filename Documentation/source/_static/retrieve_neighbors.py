#!/usr/bin/env python

# Example: retrieval of all sequences a sequence is linked with using
# MetagenomeDB, and representation as a Cytoscape directed graph.

# TODO: Improve this example by also generating edge and node properties
# (e.g., size of the sequence, and E-value of the alignment)

import MetagenomeDB as mdb

# retrieve all collections a sequence belong to
def collections (sequence):
	collections = []
	for collection, relationship in sequence.get_collections():
		collections.append(collection["name"])

	return ', '.join(sorted(collections))

o = open("retrieve_neighbors.sif", 'w')

Nodes, Edges = {}, {}

for sequence in mdb.Sequence.select():
	sequence_id = "%s (%s)" % (sequence["name"], collections(sequence))

	for outgoing_sequence, relationship in sequence.get_refereed_sequences():
		outgoing_sequence_id = "%s (%s)" % (outgoing_sequence["name"], collections(outgoing_sequence))

		print >>o, "%s	%s	%s" % (
			sequence_id,
			relationship["type"],
			outgoing_sequence_id
		)

		if (relationship["type"] == "similar-to"):
			pass

		Edges[(sequence_id, outgoing_sequence_id)] = True

		Nodes[outgoing_sequence_id] = True

	Nodes[sequence_id] = True

print "%s nodes, %s edges" % (len(Nodes), len(Edges))

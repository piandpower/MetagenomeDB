Creating a graph of contigs sharing reads
=========================================

Whenever you import relationships between reads and contigs (such as an ACE file using the ``mdb-import-ACE-alignments`` tool; see :doc:`../tools/mdb_import_ace_alignments`) you may end up with cases where two contigs share a same read read. I.e., the same read was used to assemble two (or more) contigs.

This situation can arise when the assembly algorithm couldn't decide in which contig to assign a read. MetagenomeDB can easily track those events and allow you to visualize them with additional tools, such as `Cytoscape <http://www.cytoscape.org/>`_. Here is an example of such a visualization; each node is a contig, and each edge is a case of those two contigs sharing at least one read. The thicker the edge is, the more reads are shared:

.. image:: graph_of_reads_sharing_contigs.png
	:align: center

There are two ways to detect cases of contigs sharing a same read; below is a code to implement those two ways:

Method #1: Starting with contigs
--------------------------------

The first method is to go through all possible pairs of contigs. For each contig, we then extract the list of reads related to it. Finally, for each pair of contigs we look at any potential overlap in the two lists of reads. The commented code below implements this approach, and generate files that can be opened with Cytoscape::

	# Parameters for the script:

	# name of the collection containing the contigs
	contigs_collection_name = "my collection"

	# name of the file to receive the graph in Cytoscape format
	# see http://cytoscape.org/manual/Cytoscape2_8Manual.html#SIF%20Format
	network_edges_fn = "network.sif"

	# name of the file to receive the graph's edge annotations in Cytoscape format
	# see http://www.cytoscape.org/manual/Cytoscape2_8Manual.html#Cytoscape%20Attribute%20File%20Format
	network_edges_annotations_fn = "network.eda"

	# name of the file to receive the graph's node annotations in Cytoscape format
	network_nodes_annotations_fn = "network.noa"

	#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

	# first step, we import the MetagenomeDB API, as well as some other libraries
	import MetagenomeDB as mdb
	import sys

	# then we check if the contigs' collection exists
	contigs_collection_o = mdb.Collection.find_one({"name": contigs_collection_name})

	if (contigs_collection_o == None):
		print >>sys.stderr, "ERROR: no collection found with name '%s'" % contigs_collection_name
		sys.exit(1)

	# we retrieve a list of all contigs in this collection; in our
	# example we request all sequences in the collection with a value
	# 'contig' for the property 'class'. However, this is optional if
	# you do know your collection only contains contigs.
	contigs = list(contigs_collection_name.list_sequences({"class": "contig"}))

	print "number of contigs to consider: %s" % len(contigs)

	# we create a dictionary to store the graph's edges
	edges = {}

	def order (a, b):
		if (a > b):
			return b, a
		else:
			return a, b

	# we now iterate through all non-redundant pairs of contigs; the
	# number of all possible pairs is given by the following formula:
	n = len(contigs) * (len(contigs) - 1) / 2

	print "number of pairs of contigs to consider: %s" % n

	c = 0
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
	edges_fh = open(network_edges_fn, 'w')
	edges_annotations_fh = open(network_edges_annotations_fn, 'w')
	print >>edges_annotations_fh, "NumberOfSharedReads"

	nodes = {}
	for (contig_a, contig_b) in sorted(edges.keys()):
		print >>network_fh, "%s	shared_reads	%s" % (contig_a["name"], contig_b["name"])
		print >>edges_annotations_fh, "%s (shared_reads) %s = %s" % (
			contig_a["name"],
			contig_b["name"],
			edges[(contig_a, contig_b)]
		)

		nodes[contig_a] = True
		nodes[contig_b] = True

	# finally, we store the nodes annotations (contigs' length)
	nodes_annotations_fh = open(network_nodes_annotations_fn, 'w')
	print >>nodes_annotations_fh, "ContigLength"

	for contig in sorted(nodes.keys()):
		print >>nodes_annotations_fh, "%s = %s" % (contig["name"], contig["length"])

This code is also available as a :download:`download <graph_of_reads_sharing_contigs,1.py>`.

Once this script is executed the resulting ``network.sif`` file can be loaded into Cytoscape, and the graph decorated using the annotations stored in ``network.eda`` and ``network.noa``.

Method #2: Starting with reads
------------------------------

A second, faster approach is to start from the reads. For each read that have been used in an assembly, we can request the list of contigs it was associated to. If this list contains at least two contigs, then we can link those contigs in a graph::

	# Parameters for the script:

	# name of the collection containing the reads
	reads_collection_name = "NL10_0910_vRNA_MSU_WTA:reads-clust"

	# name of the file to receive the graph in Cytoscape format
	# see http://cytoscape.org/manual/Cytoscape2_8Manual.html#SIF%20Format
	network_edges_fn = "network.sif"

	# name of the file to receive the graph's edge annotations in Cytoscape format
	# see http://www.cytoscape.org/manual/Cytoscape2_8Manual.html#Cytoscape%20Attribute%20File%20Format
	network_edges_annotations_fn = "network.eda"

	#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

	import MetagenomeDB as mdb
	import sys

	mdb.connect(db = "myDB:R1:bbolduc", user = '')

	read_collection_o = mdb.Collection.find_one({"name": reads_collection_name})

	if (read_collection_o == None):
		print >>sys.stderr, "ERROR: no collection found with name '%s'" % reads_collection_name
		sys.exit(1)

	# we create a dictionary to store the graph's edges
	edges = {}

	def order (a, b):
		if (a > b):
			return b, a
		else:
			return a, b

	# for each read in the collection,
	for read_o in read_collection_o.list_sequences():

		# we retrieve a list of all contigs this read is associated to
		contigs = list(read_o.list_related_sequences(mdb.Direction.OUTGOING, {"class": "contig"}))

		# if this list has more than one contig,
		if (len(contigs) > 1):

			# then for each pair of contigs in this list ...
			for i, contig_a_o in enumerate(contigs):
				contig_a_key = contig_a_o["name"]
				for contig_b_o in contigs[i+1:]:
					contig_b_key = contig_b_o["name"]

					# ... we store the pair in 'edges', together
					# with a count of how many times this pair has
					# been seen. This count is the number of reads
					# that connect those two contigs
					edge_key = order(contig_a_key, contig_b_key)

					if (edge_key in edges):
						edges[edge_key] += 1
					else:
						edges[edge_key] = 1

	# finally we store those edges and their annotations
	n = open(network_edges_fn, 'w')
	e = open(network_edges_annotations_fn, 'w')
	print >>e, "NumberOfSharedReads"

	for (node_a, node_b), count in edges.iteritems():
		print >>n, "%s	share_reads	%s" % (node_a, node_b)
		print >>e, "%s (share_reads) %s = %s" % (node_a, node_b, count)

This code is also available as a :download:`download <graph_of_reads_sharing_contigs,2.py>`.

.. toctree::
	:hidden:

Importing CD-HIT deduplication information: mdb-import-CD-HIT-alignments
========================================================================

``cd-hit`` is part of the `CD-HIT <http://weizhong-lab.ucsd.edu/cd-hit/>`_ toolkit. The purpose of this tool is to process a set of sequences and identify duplicates. Sequence clusters are returned by the tool, with the longest sequence being set as the representative.

``mdb-import-CD-HIT-alignments`` will import the output of ``cd-hit`` and create relationships between sequences belonging to a same cluster. Specifically, each sequence in a cluster will be related to its representative sequence; the relationship will contain all informations about the sequence similarity, coordinates, and parameters used for the ``cd-hit`` run.

Syntax
------

The syntax of this command-line tool is the following::

	Usage: mdb-import-CD-HIT-alignments [options]

	Part of the MetagenomeDB toolkit. Imports sequences deduplication information
	generated by CD-HIT into the database.

	Options:
	  -h, --help            show this help message and exit
	  -v, --verbose         
	  --no-progress-bar     
	  --dry-run             
	  --version             

	  Input:
	    -i FILENAME, --input=FILENAME
	                        File with the clusters assigned by CD-HIT (mandatory).
	                        Do not use the file with a '.bak.clstr' extension but
	                        the one with '.clstr'.
	    -l FILENAME, --input-log=FILENAME
	                        File with the log from the CD-HIT run (mandatory).
	    -C STRING, --collection=STRING
	                        Name of the collection that contains the sequences
	                        that have been processed by CD-HIT (mandatory).
	    --id-getter=PYTHON CODE
	                        Python code to reformat sequence identifers
	                        (optional); '%' will be replaced by the sequence
	                        identifier. Default: %

	  Connection:
	    --host=HOSTNAME     Host name or IP address of the MongoDB server
	                        (optional). Default: 'host' property in
	                        ~/.MetagenomeDB, or 'localhost' if not found.
	    --port=INTEGER      Port of the MongoDB server (optional). Default: 'port'
	                        property in ~/.MetagenomeDB, or 27017 if not found.
	    --db=STRING         Name of the database in the MongoDB server (optional).
	                        Default: 'db' property in ~/.MetagenomeDB, or
	                        'MetagenomeDB' if not found.
	    --user=STRING       User for the MongoDB server connection (optional).
	                        Default: 'user' property in ~/.MetagenomeDB, or none
	                        if not found.
	    --password=STRING   Password for the MongoDB server connection (optional).
	                        Default: 'password' property in ~/.MetagenomeDB, or
	                        none if not found.

For a description of the ``--id-getter`` option and its syntax, please refer to :doc:`id_getters`.

Usage
-----

``mdb-import-CD-HIT-alignments`` require at least the three following: the log file of a ``cd-hit`` run (``-l|--input-log`` option), the output file (``.clstr`` extension; ``-i|--input`` option), and the name of the collection the reads belong to (``-C|--collection`` option). 

The ``cd-hit`` log file contains all information about the run date, as well as the ``cd-hit`` parameters and version number. However, ``cd-hit`` does not provide a direct way to create this log file; you will need to capture what it prints on the screen::

	$ cd-hit -i my_reads.fasta -o my_clusters -c 0.95 > my_log.log

Alternatively, you can use the ``tee`` executable to have the output both on screen and in a log file::

	$ cd-hit -i my_reads.fasta -o my_clusters -c 0.95 | tee my_log.log

Once ``cd-hit`` done processing your reads, you can import the results by typing e.g. ::

	$ mdb-import-CD-HIT-alignments -i my_clusters.bak.clstr -l my_log.log -C my_reads
	
Any sequence A found to be better represented by a larger sequence B (i.e., A and B are in a same cluster, and B is set by ``cd-hit`` as the cluster representative) will result in a relationship being created from A to B. This relationship has the following properties:

================================ =====
Property                         Value
================================ =====
``type``                         Type of relationship (always 'similar-to')
``run.date.year``                Year the cd-hit run was completed
``run.date.month``               Month the cd-hit run was completed
``run.date.day``                 Day the cd-hit run was completed
``run.algorithm.name``           Name of the algorithm (always 'cd-hit')
``run.algorithm.version``        Version of the algorithm, as a string
``run.algorithm.parameters``     Parameters used for the cd-hit run
``score.percent_identity``       Percent of identity between A and B
``alignment.source_coordinates`` Coordinates of the alignment in A
``alignment.target_coordinates`` Coordinates of the alignment in B
================================ =====

Querying the results
--------------------

Once imported, deduplication information can be queried through the relationships between sequences. For example, to select only those reads in a collection that are representative of other reads, ::

	import MetagenomeDB as mdb

	# we first select the collection containing the reads
	collection = mdb.Collection.find_one({"name": "my_reads"})

	# then, for all sequences in this collection,
	for read in collection.list_sequences():

		# we will ask for any outgoing relationship between this sequence
		# and a possible representative identified by cd-hit, by preparing
		# the following filter:
		f = {
			"type": "similar-to",
			"run.algorithm.name": "cd-hit",
			"score.percent_identity": {"$gte": 95}
		}
		# note that this filter not only request relationships annotated by
		# a cd-hit run, but also that the two sequences share at least
		# 95% sequence identity

		# we now ask if there is any representative sequence that the current
		# read is related to with such a relationship
		representatives = list(read.list_related_sequences(mdb.Direction.OUTGOING, relationship_filter = f))

		# if yes, then this read is better represented by one (or more) representatives sequences
		if (len(representatives) > 0):
			print "%s is better represented by the following sequence(s): %s" % (
				read["name"],
				', '.join([representative["name"] for representative in representatives])
			)
			continue

		# if no, then this sequence has no duplicate; we can
		# list any sequence this sequence represents, if any
		print "%s has no representant" % read["name"]

		represented = list(read.list_related_sequences(mdb.Direction.INGOING, relationship_filter = f))

		if (len(represented) > 0):
			print "however, it represents the following sequence(s): %s" % ', '.join([sequence["name"] for sequence in represented])

.. toctree::
	:hidden:

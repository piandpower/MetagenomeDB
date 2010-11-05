MetagenomeDB
============

MetagenomeDB is a Python_ library acting as an abstraction layer on top of a MongoDB_ database. Its purpose is to simplify the storage, annotation and querying of metagenomic data. It achieves this by exposing two Python classes representing the following biological information:

- **sequences** (``Sequence`` class); e.g., reads, contigs, PCR clones
- **collections** of sequences (``Collection`` class); e.g., reads resulting from the sequencing of a sample, contigs assembled from a set of reads, PCR library

Any object can be annotated using a dictionary-like syntax:

	import MetagenomeDB as mdb
	s = mdb.Sequence(name = "My sequence", sequence = "atgc")
	print s["length"]
	s["type"] = "read"
	s.commit()

Objects of type ``Sequence`` or ``Collection`` can be connected to each other in order to represent various metagenomic datasets. Examples include, but are not limited to:

- collection of reads resulting from a sequencing run (relationship between multiple ``Sequence`` objects and one ``Collection``)
- set of contigs resulting from the assembly of a set of reads (relationship between two ``Collection`` objects)
- reads that are part of a contig (relationship between multiple ``Sequence`` objects and one ``Sequence``)
- sequence that is similar to another sequence (relationship between two ``Sequence`` objects)
- collection that is part of a bigger collection (relationship between two ``Collection`` objects)

The result is a network of sequences and collection, which can be browsed using dedicated methods; i.e.g., ``Collection.list_sequences()``, ``Sequence.list_collections()``, ``Sequence.list_related_sequences()``. Each one of those methods allow for sophisticated filters:

	# list all collections of type 'collection_of_reads'
	# this sequence belong to
	s.list_collections({"type": "collection_of_reads"})

	# list all sequences that also belong to these collections
	# with a length of at least 50 bp
	for c in s.list_collections():
		print c.list_sequences({"length": {"$gt": 50}})

MetagenomeDB also provides a set of command-line tools to import nucleotide sequences, protein sequences, BLAST and FASTA alignment algorithms output, and ACE assembly files. Other tools are provided to add or remove multiple objects, or to annotate them.

Keywords
--------

Metagenomic, Bioinformatics, Python, MongoDB

Contact
-------

Aurelien Mazurie, ajmazurie@oenone.net

Getting started
---------------

- Install a MongoDB_ server, version 1.2.1 or above and start the server
- Install the Pymongo_ library, version 1.6 or above
- Install MetagenomeDB so that it is visible from your ``PYTHONPATH``
- Rename ``MetagenomeDB/connection.cfg.edit_me`` to ``MetagenomeDB/connection.cfg`` and edit it so that it properly describe how to connect to the MongoDB server

From then you only have to import ``MetagenomeDB`` to start storing and retrieving objects::

	import MetagenomeDB as mdb

	c = mdb.Collection.find({"name": "my_collection"})

	for sequence in c.list_sequences():
		print sequence["name"], sequence["sequence"]

.. _Python: http://www.python.org/
.. _MongoDB: http://www.mongodb.org/
.. _Pymongo: http://api.mongodb.org/python
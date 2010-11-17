MetagenomeDB |release| Documentation
====================================

Overview
--------
**MetagenomeDB** is a Python_-based toolkit designed to easily store, retrieve and annotate metagenomic sequences. MetagenomeDB act as an abstraction layer on top of a MongoDB_ database. It provides an API to create and modify and connect two types of objects, namely sequences and collections:

- **Sequences** (:class:`~objects.Sequence` class) can be reads, contigs, PCR clones, etc.
- **Collections** (:class:`~objects.Collection` class) represents sets of sequences; e.g., reads resulting from the sequencing of a sample, contigs assembled from a set of reads, PCR library

Any object can be annotated using a dictionary-like syntax::

	# first, we import the library
	import MetagenomeDB as mdb

	# then we create a new Sequence object with two
	# (mandatory) properties, 'name' and 'sequence'
	s = mdb.Sequence({"name": "My sequence", "sequence": "atgc"})

	# the object can now be annotated
	print s["length"]
	s["type"] = "read"

	# once modified, the object need to be committed
	# to the database for the modifications to remain
	s.commit()

Objects of type **Sequence** or **Collection** can be connected to each other in order to represent various metagenomic datasets. Examples include, but are not limited to:

- collection of reads resulting from a sequencing run (relationship between multiple :class:`~objects.Sequence` objects and one :class:`~objects.Collection`)
- set of contigs resulting from the assembly of a set of reads (relationship between two :class:`~objects.Collection` objects)
- reads that are part of a contig (relationship between multiple :class:`~objects.Sequence` objects and one :class:`~objects.Sequence`)
- sequence that is similar to another sequence (relationship between two :class:`~objects.Sequence` objects)
- collection that is part of a bigger collection (relationship between two :class:`~objects.Collection` objects)

The result is a network of sequences and collection, which can be explored using dedicated methods; i.e.g., :func:`Collection.list_sequences() <objects.Collection.list_sequences>`, :func:`Sequence.list_collections() <objects.Sequence.list_collections>`, :func:`Sequence.list_related_sequences() <objects.Sequence.list_related_sequences>`. Each one of those methods allow for sophisticated filters using the MongoDB `querying syntax <http://www.mongodb.org/display/DOCS/Advanced+Queries>`_::

	# list all collections of type 'collection_of_reads'
	# the sequence 's' belong to
	collections = s.list_collections({"type": "collection_of_reads"})
	
	# list all sequences that also belong to these collections
	# with a length of at least 50 bp
	for c in collections:
		print c.list_sequences({"length": {"$gt": 50}})

MetagenomeDB also provides a set of command-line tools to import nucleotide sequences, protein sequences, BLAST and FASTA alignment algorithms output, and ACE assembly files. Other tools are provided to add or remove multiple objects, or to annotate them.

Content
-------

:doc:`installation`
  How to install the MetagenomeDB toolkit.

:doc:`api/index`
  Documentation for the MetagenomeDB Python library, with tutorial and examples.

:doc:`tools/index`
  Documentation for the command-line tools, with tutorial and examples.

.. toctree::
   :hidden:

   installation
   api/index
   tools/index

.. _Python: http://www.python.org/
.. _MongoDB: http://www.mongodb.org/

Introduction
============

The MetagenomeDB Toolkit
------------------------

**MetagenomeDB** is a bioinformatics toolkit which can be used to store, annotate and query metagenomic sequences, or any sequences produced by a sequencing, assembly or annotation project.

MetagenomeDB provides both an API (to use in your Python programs) and a set of command-line tools (to automatize basic tasks, such as importing sequences or BLAST results). Behind the scene, all data are managed by a MongoDB_ server, a high-performance document-oriented database.

MetagenomeDB represents metagenomic data with two types of objects: **sequences**, and **collections**. Sequences can be reads, contigs, PCR clones, etc. Collections are sets of sequences; e.g., reads resulting from a sequencing run, contigs assembled from a set of reads, PCR libraries.

API
---

MetagenomeDB provides a Python_ API to manipulate sequences and collections. Two classes, :class:`~objects.Sequence` and :class:`~objects.Collection` are available for this. For example, creating a sequence is as simple as::

	# first, we import the library
	import MetagenomeDB as mdb

	# then we create a new Sequence object with two
	# (mandatory) properties, 'name' and 'sequence'
	s = mdb.Sequence({"name": "My sequence", "sequence": "atgc"})

Each object (sequence or collection) in MetagenomeDB can be **annotated** with arbitrary properties (see :doc:`api/annotations`). For example, a sequence can be annotated with information about its type (contig, read, etc.), or with results of some bioinformatics analyses (presence of CRISPRs, evidence of bacterial contamination, etc.). Similarly, a collection can be annotated with information about how the set of sequence was collected; e.g., details about the sequencing technology (for collections of reads) or the assembly algorithm (for collections of contigs) used. Once annotated, objects can be queried for their properties.

Finally, objects in MetagenomeDB can be **related** to each other (see :doc:`api/relationships`). Sequences can belong to a collection, and collections can be grouped into super-collections (e.g., all sets of contigs resulting from various assembly techniques of a same set of reads). Sequences can also be related to other sequences, to express similarity (e.g., as shown by a BLAST alignment) or to represent sub-sequences (e.g., reads that are part of a contig).

Once objects are annotated and related to each other, MetagenomeDB offers powerful query capabilities to retrieve information of interest (see :doc:`api/queries`). For example, all contigs collected at a given date with a coverage (expressed as the number of reads used to assemble it) above a minimum threshold.

The documentation for the API is available in :doc:`this section <api/index>`.

Tools
-----

MetagenomeDB provides a set of command-line tools to import nucleotide sequences, protein sequences, BLAST and FASTA alignment algorithms output, ACE assembly files, and CRISPRfinder annotations. Other tools are provided to add or remove multiple objects, or to annotate them.

Those tools are complements of the API, to quickly store information in the database. Once this information is stored, the API can be used to query it.

The documentation for those tools is available in :doc:`this section <tools/index>`.

.. _Python: http://www.python.org/
.. _MongoDB: http://www.mongodb.org/

.. toctree::
   :hidden:

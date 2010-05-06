MetagenomeDB
============

MetagenomeDB is a Python_ library acting as an abstraction layer on top of a MongoDB_ database. Its purpose is to simplify the storage and querying of metagenomic data. It achieves this by exposing three Python classes representing the following biological information:

- sequences (``Sequence`` class); e.g., reads, contigs, PCR clones
- collections of sequences (``Collection`` class); e.g., reads resulting from the sequencing of a sample, contigs assembled from a set of reads, PCR library
- relationships between sequences and/or collections (``Relationship`` class)

Each object of type ``Sequence`` or ``Collection`` can be connected through a ``Relationship`` to represent various metagenomic data. Examples include, but are not limited to:

- collection of reads resulting from a sequencing run (relationship between multiple ``Sequence`` objects and one ``Collection``)
- set of contigs resulting from the assembly of a set of reads (relationship between two ``Collection`` objects)
- reads that are part of a contig (relationship between multiple ``Sequence`` objects and one ``Sequence``)
- sequence that is similar to another sequence (relationship between two ``Sequence`` objects)
- collection that is part of a bigger collection (relationship between two ``Collection`` objects)

Connections between objects are accessible using dedicated methods; e.g., method ``get_sequences()`` of object ``Collection``, or ``get_collections()`` of object ``Sequence``.

Each of the three base objects can receive arbitrary annotations, in addition to mandatory properties. For example, a ``Relationship`` object must describe the semantic of the link between two objects (e.g., 'part of' or 'similar to'), while a ``Sequence`` object must receive a sequence.

MetagenomeDB is provided with a set of command-line tools to import sequences in many format, and BLAST and FASTA alignment algorithms output. Other tools are provided to quickly add or remove objects, and to annotate them.

Getting started
---------------

- Install a MongoDB_ server, version 1.2.1 or above
- Install the Pymongo_ library, version 1.6 or above
- Install MetagenomeDB so that it is visible from your ``PYTHONPATH``

From then you only have to import ``MetagenomeDB`` to start storing and retrieving objects::

  import MetagenomeDB as mdb

  c = mdb.Collection.select(name = "my_collection")

  for sequence, relationship in c.get_sequences():
    print sequence["name"], sequence["sequence"]

    sequence["my_property"] = "my_value"
    sequence.commit()

.. _Python: http://www.python.org/
.. _MongoDB: http://www.mongodb.org/
.. _Pymongo: http://api.mongodb.org/python
MetagenomeDB
============

**MetagenomeDB** is a Python_-powered toolkit designed to easily store, retrieve and annotate genomic and metagenomic sequences. It is especially useful when dealing with large amount of sequences (e.g., reads and contigs resulting from several runs of sequencing and assembly), and offers a clean, programmatic interface to manage and query this information.

The web site for this project is http://metagenomedb.org/

MetagenomeDB acts as an abstraction layer on top of a MongoDB_ database. It provides an API to create and modify and connect two types of objects, namely sequences and collections. Sequences (``Sequence`` class) can be reads, contigs, PCR clones, etc. Collections (``Collection`` class) are sets of sequences; e.g., reads resulting from the sequencing of a sample, contigs assembled from a set of reads, PCR library.

Any sequence or collection can be annotated using a dictionary-like syntax::

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

Objects of type ``Sequence`` or ``Collection`` can be connected to each other in order to represent various metagenomic datasets. Examples include, but are not limited to:

- collection of reads resulting from a sequencing run (relationship between multiple ``Sequence`` objects and one ``Collection``)
- set of contigs resulting from the assembly of a set of reads (relationship between two ``Collection`` objects)
- reads that are part of a contig (relationship between multiple ``Sequence`` objects and one ``Sequence``)
- sequence that is similar to another sequence (relationship between two ``Sequence`` objects)
- collection that is part of a bigger collection (relationship between two ``Collection`` objects)

The result is a network of sequences and collection, which can be explored using dedicated methods; e.g., ``Collection.list_sequences()``, ``Sequence.list_collections()``, ``Sequence.list_related_sequences()``. Each one of those methods allow for sophisticated filters using the MongoDB `querying syntax <http://www.mongodb.org/display/DOCS/Advanced+Queries>`_::

	# list all collections of type 'collection_of_reads'
	# the sequence 's' belong to
	collections = s.list_collections({"type": "collection_of_reads"})
	
	# list all sequences that also belong to these collections
	# with a length of at least 50 bp
	for c in collections:
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

MetagenomeDB relies on another Python library to function, Pymongo_ (version 1.9 or above). The latest version of Pymongo must be installed, for example by typing ``sudo easy_install Pymongo`` on the command line.

That's it. The only other requirement is, of course, a working MongoDB_ server, either on your computer or on a computer that can be accessed through TCP/IP.

MetagenomeDB can be installed using two methods:

Using GitHub
''''''''''''

All versions of MetagenomeDB, including the latest developer releases, can be downloaded at https://github.com/BioinformaticsCore/MetagenomeDB

Once the archive in your computer, installing it can be done by typing ``sudo easy_install [path to your archive]`` in a console (see the ``easy_install`` documentation: http://packages.python.org/distribute/easy_install.html).

If you want more control (such as requesting the library and the tools to be installed in specific directories), you should first unzip the archive, then type ``sudo python setup.py`` plus any needed option from the archive's content directory (see the ``setup.py`` documentation: http://docs.python.org/install/index.html). For example, to ensure the various mdb-* tools are installed in /usr/local/bin/ you can type ``sudo python setup.py install --install-scripts=/usr/local/bin/``.

GitHub is the preferred source if you are interested in the most recent, albeit potentially unstable, releases of MetagenomeDB.

Using PyPI
''''''''''

All production-ready versions of MetagenomeDB are registered against the PyPI_ package manager. Thanks to this, you can install the toolkit by typing ``sudo easy_install MetagenomeDB`` on the command line.

Final step
''''''''''

By default MetagenomeDB will read a file named ``.MetagenomeDB`` in your home directory to know how to access the MongoDB database. A template file named ``doc/installation/MetagenomeDB_configuration.txt`` is provided. Change its name to ``.MetagenomeDB``, move it in your home directory, then update it with your own parameters.

Optionally, you can provide those information when importing MetagenomeDB in your script::

	import MetagenomeDB as mdb

	mdb.connect(host = "localhost", port = 1234, database = "MyDatabase")

From then you can store and retrieve objects::

	c = mdb.Collection.find_one({"name": "my_collection"})

	for sequence in c.list_sequences():
		print sequence["name"], sequence["sequence"]

.. _Python: http://www.python.org/
.. _MongoDB: http://www.mongodb.org/
.. _Pymongo: http://api.mongodb.org/python
.. _PyPI: http://pypi.python.org/
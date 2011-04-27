Importing sequencing parameters from Newbler: mdb-import-454AssemblyProject-annotations
=======================================================================================

``mdb-import-sequences`` (:doc:`mdb_import_sequences`) can be used to import, among else, contigs produced by an assembly run. If this assembly was performed using the `Newbler <http://en.wikipedia.org/wiki/Newbler>`_ (or gsAssembler) software, all configuration parameters are stored in a file called ``454AssemblyProject.xml``.

``mdb-import-454AssemblyProject-annotations`` can automatically annotate a collection of contigs with parameters extracted from this file.

Syntax
------

The syntax of this command-line tool is the following::

	Usage: mdb-import-454AssemblyProject-annotations [options]

	Part of the MetagenomeDB toolkit. Annotate a collection with sequencing
	information from a 454AssemblyProject.xml file.

	Options:
	  -h, --help            show this help message and exit
	  -i FILENAME, --input=FILENAME
	                        Path to a 454AssemblyProject.xml file (mandatory).
	  -C STRING, --collection=STRING
	                        Name of the collection to annotate (mandatory).
	  --root-property=STRING
	                        Root of the property tree to annotate the collection
	                        (optional). Default: assembly.algorithm.parameters
	  -v, --verbose         
	  --dry-run             
	
	  Connection:
	    --host=HOSTNAME     Host name or IP address of the MongoDB server
	                        (optional). Default: localhost
	    --port=INTEGER      Port of the MongoDB server (optional). Default: 27017
	    --db=STRING         Name of the database in the MongoDB server (optional).
	                        Default: 'MetagenomeDB'
	    --user=STRING       User for the MongoDB server connection (optional).
	                        Default: ''
	    --password=STRING   Password for the MongoDB server connection (optional).
	                        Default: ''

Usage
-----

Let us consider a set of contigs assembled by Newbler and stored in a FASTA-formatted file ``contigs.fasta``. First, these contigs need to be imported using ``mdb-import-sequences``, for example in a collection name 'Contigs'::

	$ mdb-import-sequences -i contigs.fasta -C Contigs

Annotating this 'Contigs' collection with the content of a ``454AssemblyProject.xml`` file is then as easy as::

	$ mdb-import-454AssemblyProject-annotations -i 454AssemblyProject.xml -C Contigs

By default all annotations are stored as sub-properties of a ``assembly.algorithm.parameters`` property. This root property can be changed using the ``--root-property`` option.

The properties can then be accessed using the API (see :doc:`../api/annotations`)::

	import MetagenomeDB as mdb

	c = mdb.Collection.find_one({"name": "Contigs"})

	# print all assembly parameters
	print c["assembly.algorithm.parameters"]

	# print only some parameters
	print c["assembly.algorithm.parameters.overlapMinMatchIdentity"]

.. toctree::
	:hidden:

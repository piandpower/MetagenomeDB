Exporting sequences in various formats: mdb-export-sequences
============================================================

``mdb-export-sequences`` exports sequences previously stored in collections as files in many format, including FASTA (for a complete list of the formats supported, see `http://biopython.org/wiki/SeqIO <http://biopython.org/wiki/SeqIO>`_).

Syntax
------

::

	Usage: mdb-export-sequences [options]

	Part of the MetagenomeDB toolkit. Export nucleotide or aminoacid sequences
	from the database. Those sequences can be in any format supported by Biopython
	(see http://biopython.org/wiki/SeqIO).

	Options:
	  -h, --help            show this help message and exit
	  -C STRING, --collection=STRING
				Name of the collection to retrieve the sequences from
				(mandatory).
	  -r, --recursive       By default only the sequences belonging to the
				collection provided are exported. If set, this option
				will force all sequences belonging to sub-collections
				to be exported as well.
	  -o FILENAME, --output=FILENAME
				Destination for the sequences (optional). Default:
				standard output.
	  -f STRING, --format=STRING
				Format of the sequences (optional). Default: fasta
				(see http://biopython.org/wiki/SeqIO for a list of the
				formats supported)
	  -v, --verbose         
	  --no-progress-bar     
	  --dry-run             

	  Filtering:
		-p KEY VALUE, --property-filter=KEY VALUE
				Filter the sequences according to a given key and
				value. If several filters are declared, only sequences
				satisfying them all will be returned (optional).
		-w FILENAME, --white-list=FILENAME
				Text file to read sequence names from (one name per
				line). Only sequences with names found in this file
				will be returned (optional).
		-b FILENAME, --black-list=FILENAME
				Text file to read sequence names from (one name per
				line). Only sequences with names not found in this
				file will be returned (optional).

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

``mdb-export-sequences`` exports sequences belonging to any collection provided by the ``-C`` (or ``--collection``) option. Additional option ``-r`` (``--recursive``) will exports sequences from all sub-collections as well.

Sequences can be exported to a file (which name can be provided with the ``-o`` or ``--output`` option) in any format supported by the Biopython library; by default, the format is FASTA. A complete list of formats available can be found at `http://biopython.org/wiki/SeqIO <http://biopython.org/wiki/SeqIO>`_.

Filtering
---------

Sequences from the collection(s) can be filtered out by using a combination of the ``-p`` (``--property-filter``), ``-w`` (``--white-list``) and/or ``-b`` (``--black-list``) options:

- the ``-p`` option will only keep sequences with a given property and value. E.g., ``-p class read`` will only keep sequences from the collection(s) with a property ``class`` set to the value ``read``.
- the ``-w`` option will read sequence names from a provided file, and exclude all sequences which name is not in this file (white list).
- the ``-b`` option will read sequence names from a provided file, and exclude all sequences which name is in this file (black list).

.. toctree::
	:hidden:

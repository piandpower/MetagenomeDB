MetagenomeDB Tutorial
=====================

This is a tutorial for the `MetagenomeDB <http://github.com/ajmazurie/MetagenomeDB>`_ toolkit. MetagenomeDB allows to represent, manipulate and query metagenomic data using the `Python <http://www.python.org>`_ programming language. All the data are transparently handled by a `MongoDB <http://www.mongodb.org>`_ server, a professional-grade `document-oriented <http://en.wikipedia.org/wiki/Document-oriented_database>`_ database. This database is invisible for the user, who interacts with a high-level Python API. MetagenomeDB is also provided with a set of command-line tools to quickly add, remove and annotate objects in the database.

1. Fundamentals: sequences, collections and relationships
---------------------------------------------------------

Imported as a Python library, MetagenomeDB exposes four classes: ``Object``, ``Sequence``, ``Collection`` and ``Relationship``, which allow for the representation of virtually any kind of metagenomic data.

1.1. Sequences (``Sequence`` class)
...................................

1.1.1. Annotations
''''''''''''''''''

The ``Sequence`` class stores sequences of any type (DNA, RNA or protein). In order to create a ``Sequence`` object, a sequence and a name must be provided as arguments::

	$ python
	Python 2.6.4 (r264:75821M, Oct 27 2009, 19:48:32) 
	[GCC 4.0.1 (Apple Inc. build 5493)] on darwin
	Type "help", "copyright", "credits" or "license" for more information.
	>>> import MetagenomeDB as mdb
	>>> sequence = mdb.Sequence(sequence = "atgc", name = "my sequence")

Our sequence has now been declared. It has two properties: ``sequence``, which is a string that represents its sequence, and ``name``, which is whatever identifier you want to give it. The ``get_properties()`` method will list all properties of this object::

	>>> print sequence.get_properties()
	{'length': 4, 'name': 'my sequence', 'sequence': 'atgc'}

Note that a third property, ``length`` has been added; it is automatically inferred from the sequence when not explicitly provided.

A ``Sequence`` object (and whatever object in MetagenomeDB) is not limited to those three properties. You can add and modify any property by manipulating your object as a `dictionary <http://docs.python.org/tutorial/datastructures.html#dictionaries>`_::

	>>> sequence["my_property"] = 3
	>>> print sequence["my_property"]
	3
	>>> sequence["my_property"] = [1,2,3]
	>>> print sequence.get_properties()
	{'my_property': [1,2,3], 'length': 4, 'name': 'my sequence', 'sequence': 'atgc'}
	>>> "my_property" in sequence
	True
	>>> del sequence["my_property"]

MetagenomeDB supports nested properties; i.e., properties that are children of other properties. Creating such a nested property requires the use of the dot notation::

	>>> sequence["my_property.my_subproperty"] = "something"
	>>> print sequence.get_properties()
	>>> {'my_property': {'my_subproperty': 'something'}, 'length': 4, 'name': 'my sequence', 'sequence': 'atgc'}

Note that the property ``my_property`` now has a sub-property ``my_subproperty``. Accessing and modifying this sub-property can be done user either the dot notation or a more traditional Python dictionary notation::

	>>> print sequence["my_property"]["my_subproperty"]
	'something'
	>>> print sequence["my_property.my_subproperty"]
	'something'
	>>> sequence["my_property"]["my_subproperty"] = "something else"
	>>> sequence["my_property.my_subproperty"] = "something different"

Such nested properties are useful to group related properties; e.g., information about who produced this sequence, and how::

	>>> sequence["author.name"] = "me"
	>>> sequence["author.institution"] = "my employer"
	>>> print sequence["author"]
	{'name': 'me', 'institution': 'my employer'}

1.1.2. Commit
'''''''''''''

At this stage the sequence object you created and annotated exists only in the memory of your computer. It is `uncommitted`, as shown when printing the sequence description::

	>>> print sequence
	<Sequence id:none name:'my sequence' length:4 state:'uncommitted'>

To `commit` this object to the database, just call its ``commit()`` method::

	>>> sequence.commit()
	>>> print sequence
	<Sequence id:4be9b417aeba8aa576000000 name:'my sequence' length:4 state:'committed'>

Your object received an internal identifier, which prove it was stored into the database. If you happen to modify this object `after` it is committed, you will need to commit it again to store the modifications::

	>>> del sequence["author"]
	>>> print sequence
	<Sequence id:4be9b417aeba8aa576000000 name:'my sequence' length:4 state:'uncommitted'>
	>>> sequence.commit()
	>>> print sequence
	<Sequence id:4be9b417aeba8aa576000000 name:'my sequence' length:4 state:'committed'>

To know if an object was committed after its latest modification, you can either read its description or call ``is_committed()``::

	>>> print sequence.is_committed()
	True

1.1.3. Querying
'''''''''''''''

Sequences that have been committed can be queried based on any of their properties. It is important to note that uncommitted objects are `not` visible by those queries.

Two methods of the ``Sequence`` class are available to query sequences: ``find()``, and ``find_one()``. The former returns all sequences that match the query, while the latter returns only the first. This can be useful when you know there is only one sequence that can match your query.

Queries are expressed as a filter; i.e., you provide a set of properties and the values you are looking for, and MetagenomeDB will return the sequences that match::

	>>> mdb.Sequence.find_one(name = "my sequence")
	<Sequence id:4be9b417aeba8aa576000000 state:committed name:'my sequence' len:4>
	>>> list(mdb.Sequence.find(length = 4))
	[<Sequence id:4be9b417aeba8aa576000000 state:committed name:'my sequence' len:4>]

Note: the ``find_one()`` method returns the object that match your query, or ``None`` if there is none. However the ``find()`` method returns a list of objects as a Python `generator <http://en.wikipedia.org/wiki/Iterator#Python>`_::

	>>> for s in mdb.Sequence.find(length = 4):
	>>>	print s
	<Sequence id:4be9b417aeba8aa576000000 state:committed name:'my sequence' len:4>

You can query for several properties at once::

	>>> list(mdb.Sequence.find(length = 4, my_property = "something"))

Note: Due to technical limitations, nested properties cannot be queried using dot notation::

	>>> list(mdb.Sequence.find(my_property.my_subproperty = "something"))
	  File "<stdin>", line 1
	SyntaxError: keyword can't be an expression

Instead, you must declare them as nested dictionaries::

	>>> list(mdb.Sequence.find(my_property = {"my_subproperty": "something"}}))

This command will select all sequences of which nested property ``my_property.my_subproperty`` is equal to 'something'.

`TODO: Do something about this; maybe by allowing some syntactic sugar?`

1.1.4. Related objects
''''''''''''''''''''''

A ``Sequence`` can be part of a ``Collection`` , or be related to other sequences 

1.2. Collections
................

The ``Collection`` object represents a collection of ``Sequence`` and/or ``Collection`` objects. In metagenomic a ``Collection`` will typically represents a collection of reads produced by a sequencing run, or a set of contigs produced by an assembly.

The only mandatory property when creating a ``Collection`` object is a ``name``::

	>>> c = mdb.Collection(name = "my collection")

In addition to the methods mentioned earlier, ``Collection`` classes have these additional methods:

``add_sequence()`` will add an existing ``Sequence`` object to the collection::

	>>> s = mdb.Sequence.find_one(name = "my_sequence")
	>>> c.add_sequence(s)

`TODO: to implement`

``remove_sequence()`` will remove an existing ``Sequence``::

	>>> c.remove_sequence(s)

`TODO: to implement`

1.3. Relationships
..................

Bla

1.4. Anonymous objects
......................

The ``Object`` class can be used to represent any biological object that would not be a ``Sequence``, ``Collection`` or ``Relationship``.

A typical example is a reference to a public database when importing BLAST results. Whenever a BLAST is performed against sequences that are not registered in MetagenomeDB, the resulting BLAST output cannot be interpreted as a ``Relationship`` between two ``Sequence`` objects. The reason is that either the query or the hit is a sequence unknown of MetagenomeDB; i.e., an 'anonymous' object.

To allow for the representation of those anonymous objects the ``Object`` class can be used. Its behavior is exactly the same at those of the other three object classes. I.e., an anonymous object can be annotated, committed to the database, and related to other objects (either anonymous, or other ``Sequence`` or ``Collection``).

Both ``import.FASTA`` and ``import.BLAST`` tools (see section X.X) use ``Object`` when importing alignments between sequences in the database and sequences outside of the database.

2. Importing and manipulating sequences
---------------------------------------

2.1. Importing sequences
........................

Let's consider the following `FASTA <http://en.wikipedia.org/wiki/FASTA_format>`_-formatted file ``my_sequences.fasta``::

	>contig00001  numreads=171
	TTCTTCACGTGGGAGTGCGTGTCCCACAAGGTCGCGGGTCTACCCTTACGGGAACCCCGC
	TTAAGTAGGAGTTAGTGCACAATAATTTAACGTTTTCGGTTCCTATACAGCTCAGAGCTG
	TAAGAAATAAAGTTTAAAACTGCAAATATAAAGCCATAACACATGAAAAAGATAACAATA
	AACATTGATGAAAAACTAAAGGAGGTTTTTTCTAGATTATGTGAAGAGGAAGGGGTAGAT
	ATGGCTCAGGGTATAAGGGAGTTAATTATTGAGGCAATAAATAGGGGCTATATAAACAAG
	CAGAGGAAAGAAGGCGTAGAAAAGGTGAGAAAAAACAAGTGAACAATCACACTTCGATTG
	TTTTGCAACTTAGGATACAAAAAGAACAGTGC
	>contig00002  numreads=13
	ttAGGGTTCTTTTCGGCGAGTTTTCTGGTATCCTCAATTTGTTCGTACAGTTCCTTGATA
	GGGTTCTCAAAATCAAGGAATTGTCTGTTTGGGTATTGGGGCATAATGATCGTTTAGAAC
	GGTAAAATTAGGGGTTCAGATTTTTtCCTGAAAaGATTtGTTTATGAAAAGTCTTTACCC
	TTATCTTTGCCGTCCCGAAAACGGACTGAAAGGGATGTTTTTAGGATGATATAACTGGTT
	TCCCAGTAATCACGGATCGGTAGTTCAGTTGGTTATCTCGCCTTAGGCGAGACGCCCTGA
	GAAAGGCTCTTTTAAATGATTATGTTCTATACTTACATCATAGTAAATAATGATGGTATA
	TTCTATAAGGGAAGTACCTCAGACTTTGAGAAAAGGTTAGAACAACACAACGCCGGACTC
	AGTCACTACACTAGAGGCAGAGGGCCTTGGAaGCTGGTTTTTGTTCAGGCTTTCtCTTCA
	CAAATTGAGGCTGAAGCCTTGGAAAAACGGCTAAAgCGTTGTAATAAAGATTATTTAAAC
	TGGTTAATTAAACAaCCAGTTAATATATTGGATCGGTAGTTCAGTTGGTTAGAATGCCG

In order to manipulate those sequences we first need to import them into the MetagenomeDB database. A utility, ``import.sequences`` is available in the ``Tools/`` subdirectory to do so. 

``import.sequences`` can read sequences in a variety of formats (see `here <http://www.biopython.org/wiki/SeqIO#File_Formats>`_ for a list); by default, it expects FASTA files. To list all its options, type ``./import.sequences --help``::

	$ cd path_to_metagenomedb_installation/Tools
	$ ./import.sequences --help
	Usage: import.sequences [options]
	
	Part of the MetagenomeDB toolkit. Imports nucleotide or aminoacid sequences
	into the database. Those sequences can be in any format supported by Biopython
	(see http://biopython.org/wiki/SeqIO).
	
	Options:
	  -h, --help            show this help message and exit
	  -v VERBOSITY, --verbosity=VERBOSITY
	
	  Sequences:
	    -i FILENAME, --input=FILENAME
	                        Sequences to import.
	    -f STRING, --format=STRING
	                        Format of the sequences file. Default: fasta
	    -s KEY VALUE, --sequence-property=KEY VALUE
	                        Custom sequence property (optional).
	
	  Collection:
	    -C STRING, --collection-name=STRING
	                        Name of the collection the sequences belong to.
	    -c KEY VALUE, --collection-property=KEY VALUE
	                        Description of the collection the sequences belong to,
	                        as a key/value (optional).
	    -r KEY VALUE, --relationship-property=KEY VALUE
	                        Custom sequence-to-collection relationship property
	                        (optional).

Two information must be provided to import sequences: the name of the sequence file (``-i`` or ``--input``), and the ``Collection`` the sequences will belong to. The ``Collection`` can be either pre-existing; in this case, you can provide its name with the ``-C`` or ``--collection-name`` option. Or it can be created on the fly, using your own definition (``-c`` or ``--collection-property`` option). Note: all sequences in the file will be assigned the same ``Collection``.

Let imagine a collection named ``my_collection`` already exists. Then importing ``my_sequences.fasta`` is then as easy as::

	$ ./import.sequences -i path_to/my_sequences.fasta -C my_collection

If ``my_collection`` didn't exist, you could have created it with the following command line::

	$ ./import.sequences -i path_to/my_sequences.fasta -c name my_collection

In this case, a collection with name 'my_collection' is created prior to the sequences importation. In case the collection already exists an error will be thrown::

	$ ./import.sequences -i path_to/my_sequences.fasta -c name my_collection

3. Importing and manipulating alignments
----------------------------------------

4. Advanced manipulations
-------------------------

- traverse neighbors (e.g., is there any sequence in any of my descendant collections that have such and such property?)

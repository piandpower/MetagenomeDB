MetagenomeDB
============

Welcome to the `MetagenomeDB <http://github.com/ajmazurie/MetagenomeDB>`_ toolkit documentation. MetagenomeDB allows to represent, manipulate and query metagenomic data using the `Python <http://www.python.org>`_ programming language. All the data are transparently handled by a `MongoDB <http://www.mongodb.org>`_ server, a professional-grade `document-oriented <http://en.wikipedia.org/wiki/Document-oriented_database>`_ database. This database is invisible for the user, who interacts with a high-level Python API. MetagenomeDB is also provided with a set of command-line tools to quickly add, remove and annotate objects in the database.

.. contents:: Contents:

.. sectnum::

Getting started
---------------

`TO DO: Short description of how to install MetagenomeDB and load the API`

Basics
------

Imported as a Python library, MetagenomeDB exposes three classes: ``Sequence``, ``Collection`` and ``Relationship``, which allow for the representation of virtually any kind of metagenomic data.

``Sequence`` and ``Collection`` classes can be used to represent sequences and collection of sequences, respectively. ``Relationship`` objects can then be used to link sequences to collections, sequences to sequences (e.g., sequence similarity), or collections to collections (e.g., sub-collections).

A firth class, ``Object`` is also available to represent any information that wouldn't be a ``Sequence`` or a ``Collection``. It allows to extend MetagenomeDB to exotic data; e.g., expression data, or sequences that are not stored in other databases.

Sequences (``Sequence`` class)
..............................

Properties
__________

The ``Sequence`` class stores sequences of any type (DNA, RNA or protein). In order to create a ``Sequence`` object, a sequence and a name must be provided as arguments::

	$ python
	Python 2.6.4 (r264:75821M, Oct 27 2009, 19:48:32) 
	[GCC 4.0.1 (Apple Inc. build 5493)] on darwin
	Type "help", "copyright", "credits" or "license" for more information.
	>>> import MetagenomeDB as mdb
	>>> sequence = mdb.Sequence(sequence = "atgc", name = "my sequence")

Our sequence has now been declared. It has two properties: ``sequence``, which is a string that represents its sequence, and ``name``, which is any identifier you want to give it. The ``get_properties()`` method will list all properties of this object::

	>>> print sequence.get_properties()
	{'length': 4, 'name': 'my sequence', 'sequence': 'atgc'}

Note that a third property, ``length`` has been added; it is automatically inferred from the ``sequence`` property if you do not provide it.

A ``Sequence`` object is not limited to those three properties. You can add and modify any property by manipulating your object as a `dictionary <http://docs.python.org/tutorial/datastructures.html#dictionaries>`_::

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

Nested properties are useful to group related properties; e.g., information about who produced this sequence, and how::

	>>> sequence["author.name"] = "me"
	>>> sequence["author.institution"] = "my employer"
	>>> print sequence["author"]
	{'name': 'me', 'institution': 'my employer'}

Commit (``commit()`` method)
____________________________

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

Query (``find()`` and ``find_one()`` methods)
_____________________________________________

Sequences that have been committed can be queried based on any of their properties. It is important to note that uncommitted objects are `not` visible by those queries.

Two methods of the ``Sequence`` class are available to query sequences: ``find()``, and ``find_one()``. The former returns all sequences that match the query, while the latter returns only the first. This can be useful when you know there is only one sequence that can match your query, or if you only want one example of sequence that match this query.

Queries are expressed as a filter; i.e., you provide a set of properties and the values you are looking for, and MetagenomeDB will return the sequences that match::

	>>> mdb.Sequence.find_one(name = "my sequence")
	<Sequence id:4be9b417aeba8aa576000000 name:'my sequence' length:4 state:'committed'>
	>>> list(mdb.Sequence.find(length = 4))
	[<Sequence id:4be9b417aeba8aa576000000 name:'my sequence' length:4 state:'committed'>]

Note: the ``find_one()`` method returns the object that match your query, or ``None`` if there is none. However the ``find()`` method returns a list of objects as a Python `generator <http://en.wikipedia.org/wiki/Iterator#Python>`_::

	>>> for s in mdb.Sequence.find(length = 4):
	...	print s
	<Sequence id:4be9b417aeba8aa576000000 name:'my sequence' length:4 state:'committed'>

You can query for several properties at once::

	>>> list(mdb.Sequence.find(length = 4, my_property = "something"))

If no parameter is provided for ``find()`` or ``find_one()``, all objects or the first committed object are returned, respectively.

.. note::

   Due to technical limitations, nested properties cannot be queried using dot notation::

	>>> list(mdb.Sequence.find(my_property.my_subproperty = "something"))
	  File "<stdin>", line 1
	SyntaxError: keyword can't be an expression

   Instead, you must declare them as nested dictionaries::

	>>> list(mdb.Sequence.find(my_property = {"my_subproperty": "something"}}))

   This command will select all sequences of which nested property ``my_property.my_subproperty`` is equal to 'something'.

   `TODO: Do something about this; maybe by allowing some syntactic sugar?`

Related sequences
_________________

Two ``Sequence`` objects can be related because the sequences they represent are similar, or because one is a subsequence of another. The ``get_related_sequences()`` method gives access to these related sequences.

This method takes three arguments: a direction for the relationship (``direction``), a sequence filter (``sequence_filter``) and a relationship filter (``relationship_filter``).

Direction of the relation
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``direction`` argument is the direction of the relationship existing between the original ``Sequence`` and possible related sequences. The value ``Sequence.INGOING`` (or ``Sequence.REFERRING``) will select related sequences that `refers to` the original ``Sequence``::

	>>> for sequence, relationship in s.get_related_sequences(mdb.Sequence.INGOING):
	...    print sequence

Note that ``get_related_sequences()`` returns two objects at each iteration: the related sequence, and the relationship between this related sequence and the original ``Sequence``.

The value ``Sequence.OUTGOING`` (or ``Sequence.REFERRED``) will select related sequences that `are referred to` by the original ``Sequence``. Those two directions express different ways sequences can be related. For example, a sequence A can be a part of a sequence B, but not the opposite. Hence, A `refers to` B while B `is referred to` by A::

	>>> A = mdb.Sequence(sequence = "atgc", name = "a")
	>>> B = mdb.Sequence(sequence = "cgcatgccgc", name = "b")
	>>> r = mdb.Relationship(source = A, target = B, type = "part-of")
	>>> r.commit()
	>>> for sequence, relationship in A.get_related_sequences(mdb.Sequence.INGOING):
	...    print sequence
	>>> _

Nothing will be displayed here: no sequence `refers to` A. ::

	>>> for sequence, relationship in A.get_related_sequences(mdb.Sequence.OUTGOING):
	...    print sequence
	<Sequence id:4bfae082aeba8a6612000001 name:'b' length:10 state:'committed'>

However, B is `referred to` by A.

Conversely, for B::

	>>> for sequence, relationship in B.get_related_sequences(mdb.Sequence.INGOING):
	...    print sequence
	<Sequence id:4bfae081aeba8a6612000000 name:'a' length:4 state:'committed'>

The sequence A is indeed `referring to` B. ::

	>>> for sequence, relationship in B.get_related_sequences(mdb.Sequence.OUTGOING):
	...    print sequence
	>>> _

However, no sequence is `referred to` by B.

The value ``Sequence.BOTH`` will select all related sequences, regardless of the direction.

Filters
~~~~~~~

When looking for related sequences a filter can be applied at two levels: on the candidate related sequences, and on the relationship between the original ``Sequence`` and those candidates.

In both cases the filters are expressed as for the ``find()`` and ``find_one()`` methods; i.e., as a set of properties and values that the related sequences or their relationships must possess::

	>>> for s, relationship in A.get_related_sequences(mdb.Sequence.BOTH, sequence_filter = {"name": "b"}):
	...    print sequence
	<Sequence id:4bfae082aeba8a6612000001 name:'b' length:10 state:'committed'>
	>>> for s, relationship in A.get_related_sequences(mdb.Sequence.BOTH, relationship_filter = {"type": "part-of"}):
	...    print sequence
	<Sequence id:4bfae082aeba8a6612000001 name:'b' length:10 state:'committed'>

Deletion
________

A ``Sequence`` object can be removed from the database by calling its ``remove()`` method::

	>>> B.remove()
	>>> print B
	<Sequence id:none name:'b' length:10 state:'uncommitted'>

Note that the status for the sequence is now set to uncommitted.

`TO DO: For now the removal of an object does not remove the relationship it has with other objects. A general framework to detect such orphans should be implemented`

Collections (``Collection`` class)
..................................

The ``Collection`` object represents a collection of ``Sequence`` and/or ``Collection`` objects. In metagenomic a ``Collection`` will typically represents a collection of reads produced by a sequencing run, or a set of contigs produced by an assembly.

The only mandatory property when creating a ``Collection`` object is a ``name``::

	>>> c = mdb.Collection(name = "my collection")

In addition to the methods mentioned earlier, ``Collection`` classes have these additional methods:

Related collections
___________________

Related sequences
_________________

``add_sequence()`` will add an existing ``Sequence`` object to the collection::

	>>> s = mdb.Sequence.find_one(name = "my_sequence")
	>>> c.add_sequence(s)

By default, a ``Relationship`` object is created of type 'part-of' between this sequence and the collection. However, a custom ``Relationship`` object can be provided as an argument:

	>>> r = mdb.Relationship(type = "part-of", "my_property" = 1)
	>>> c.add_sequence(s, r)

``remove_sequence()`` will remove an existing ``Sequence``::

	>>> c.remove_sequence(s)

`TODO: to implement`

Accessing the collections a given sequence belong to is done by calling the ``get_collections()`` method::

	>>> s = mdb.Sequence.find_one()
	>>> for collection, relationship in s.get_collections():
	...    print collection["name"]

Note that the ``get_collections()`` method returns two objects at each iteration: one ``Collection`` the sequence belong to, and the ``Relationship`` that link those two objects. The ``Relationship`` object can contain additional information about why this sequence is thought to belong to this collection.

The ``get_collections()`` method accepts two arguments: a filter for the ``Collection`` objects (``collection_filter``), and one for the ``Relationship`` objects (``relationship_filter``). Hence, the following code will only select the collections that are of class 'contigs', and of which the sequence is linked through a relationship of type 'part-of'::

	>>> list(s.get_collections(collection_filter = {"class": "contigs"}, relationship_filter = {"type": "part-of"}})

Relationships (``Relationship`` class)
......................................

Bla


Tools
-----

In addition to the Python API provided by MetagenomeDB, several command-line tools are available to perform basic operations in batch.

Adding and removing objects
...........................

``add`` and ``remove`` utilities.

Annotating objects
..................

``annotate`` utility.

Importing sequences
...................

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

Importing sequence alignments
.............................

``import.BLAST`` and ``import.FASTA`` utilities.

- when either the query or hit collection is not provided, the query or hit object that will be registered is a custom object

- import.BLAST: several XML tags can be combined to generate either a query or hit id. Python code can also be used to modify the content on those tags on the fly:

Example 1::

	...
	<Iteration>
	  <Iteration_iter-num>1</Iteration_iter-num>
	  <Iteration_query-ID>1</Iteration_query-ID>
	  <Iteration_query-def>CH0704v-contig00010 length=3963   numreads=678</Iteration_query-def>
	  <Iteration_query-len>3963</Iteration_query-len>
	  <Iteration_hits>
	    ...

+	--query-id-getter "<Iteration_query-def>.split()[0]"

=	'CH0704v-contig00010' as the query identifier


Example 2::

	...
	<Hit>
	  <Hit_num>2</Hit_num>
	  <Hit_id>gi|9625521|ref|NP_039778.1|</Hit_id>
	  <Hit_def>putative integrase [Sulfolobus virus 1] &gt;gi|138570|sp|P20214.1|INTG_SSV1 RecName: Full=Probable integrase &gt;gi|46705|emb|CAA30211.1| ORF D-335 [Sulfolobus spindle-shaped virus 1]</Hit_def>
	  <Hit_accession>NP_039778</Hit_accession>
	  <Hit_len>335</Hit_len>
	  <Hit_hsps>
	    <Hsp>
	       ...

The following syntax, ``--hit-id-getter "{'id': <Hit_id>, 'definition': <Hit_def>, 'accession': <Hit_accession>}"`` together with no provided hit collection, will create custom objects as hits which will be a dictionary with the three keys 'id', 'definition' and 'accession'

Advanced manipulations
----------------------

- traverse neighbors (e.g., is there any sequence in any of my descendant collections that have such and such property?)

Future developments
-------------------

Data that are abstracted by the MetagenomeDB toolkit are for now handled by a document-oriented database. However metagenomic data are connected in nature (sequences to sequences, sequences to collections, collections to collections) and may be better handled by a graph database with a suitable query language. It would allow for a faster and more intuitive exploration of the data. E.g., some links may be transparently handled as undirected (sequences/collections) while other retain an orientation (sequence/sequence, collection/collection). It will also simplify the deletion of objects that are connected (would equal to the deletion of a subgraph).

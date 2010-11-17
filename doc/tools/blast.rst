Working with BLAST outputs
--------------------------

MetagenomeDB considers BLAST results as relationship between sequences; namely, between each query and its hits. Once BLAST results are imported in the database, you can ask for all hits that align against a given query sequence, or the opposite. The alignment itself (coordinates and sequence of the HSP) and the scores (E-value, percentage of identity) are stored and can be used to filter down your queries. Information about the BLAST run, such as the program used, its version, and the parameters are stored as well.

Importing BLAST outputs
.......................

The ``mdb-import-BLAST-alignments`` tool is provided to import NCBI BLAST outputs::

	$ mdb-import-BLAST-alignments --help
	Usage: mdb-import-BLAST-alignments [options]
	
	Part of the MetagenomeDB toolkit. Imports XML-formatted NCBI BLAST alignments
	into the database.
	
	Options:
	  -h, --help            show this help message and exit
	  -v, --verbose         
	  --dry-run             
	
	  Input:
	    -i FILENAME, --input=FILENAME
	                        XML-formatted output of a NCBI BLAST sequence
	                        alignment (mandatory).
	    -Q STRING, --query-collection=STRING
	                        Name of the collection the query sequences belong to
	                        (mandatory).
	    -H STRING, --hit-collection=STRING
	                        Name of the collection the hit sequences belong to
	                        (optional). If not provided, the hit sequences are
	                        assumed to be external to the database, and only a
	                        summary of those hits will be stored: hit identifer,
	                        description and E-value.
	    --date=YEAR MONTH DAY
	                        Date of the BLAST run (optional). By default, creation
	                        date of the input file.
	    --query-id-getter=PYTHON CODE
	                        Python code to reformat query identifers (optional);
	                        '%' will be replaced by the query identifier. Default:
	                        %.split()[0]
	    --hit-id-getter=PYTHON CODE
	                        Python code to reformat hit identifers (optional); '%'
	                        will be replaced by the hit identifier. Default:
	                        %.split()[0]
	    --no-check          If set, bypass the query and hit sequences identifier
	                        check (not recommended).
	
	  Input filtering:
	    --max-E-value=FLOAT
	                        If set, filter out all hits with a E-value above the
	                        provided cut-off.
	    --min-identity=INTEGER
	                        If set, filter out all hits with a percentage of
	                        identity below the provided cut-off.
	    --max-hits=INTEGER  If set, keep only the first '--max-hits' hits for each
	                        query.
	    --ignore-alignment  If set, will not store information about the sequence
	                        alignment (HSP coordinates and sequences).
	
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

This tool accepts XML-formatted NCBI BLAST outputs only. Those outputs can be concatenated (i.e., one XML file resulting from the concatenation of several BLAST outputs). Here is a review of the most important parameters:

Input sequences
~~~~~~~~~~~~~~~

There are two situations this tool can handle:

- Alignments among sequences that are already in the database. In this situation, both the query and hit sequences are objects present in the database. Options ``-Q`` (``--query-collection``) and ``-H`` (``--hits-collection``) are requested to known the name of the collections containing the query and hit sequences, respectively.

- Alignments against an external database. In this situation, the query sequences are objects present in the database while the hits are external to it (e.g., NR). Option ``-Q`` (``--query-collection``) must be provided.

Sequence identifiers
~~~~~~~~~~~~~~~~~~~~

The optional ``--query-id-getter`` and ``--hit-id-getter`` options can be used to modify query and hit identifiers on-the-fly, respectively. This is useful if you expect the BLAST XML output to contain sequence identifiers with some additional, unwanted characters.

For example, considering the following XML output::

	...
	<Iteration>
	  <Iteration_iter-num>1</Iteration_iter-num>
	  <Iteration_query-ID>1</Iteration_query-ID>
	  <Iteration_query-def>CH0704v-contig00010 length=3963   numreads=678</Iteration_query-def>
	  <Iteration_query-len>3963</Iteration_query-len>
	  <Iteration_hits>
	    ...

The query identifier that ``mdb-import-BLAST-alignments`` will consider is the whole string "CH0704v-contig00010 length=3963   numreads=678". If only the first element ("CH0704v-contig00010") is needed, you can use the following Python code for the ``--query-id-getter`` option::

	$ mdb-import-BLAST-alignments --query-id-getter "%.split()[0]"

Any '%' character in the string you provide will be replaced by the value of the query identifier. In this example, the short Python code used will split the original string (resulting in the list "CH0704v-contig00010", "length=3963", "numreads=678") and select the first element. The same approach applies for ``--hit-id-getter``.

Hits filtering
~~~~~~~~~~~~~~

The optional ``--max-E-value``, ``--min-identity`` and ``--max-hits`` options can be used to ignore some of the hits contained in the BLAST output.

- ``--max-E-value`` will filter out any hit with a E-value above a provided cut-off
- ``--min-identity`` will filter out any hit with a percentage of identity below a provided cut-off
- ``--max-hits`` will filter out any hit with position greater than a cut-off in the BLAST output

Connection
~~~~~~~~~~

The optional ``--host``, ``--port``, ``--db``, ``--user`` and ``--password`` options are common to all MetagenomeDB tools and can be used to bypass the default server connection information found in ``~/.MetagenomeDB``.

Querying BLAST results
......................

As introduced at the top of the document, ``mdb-import-BLAST-alignments`` convert BLAST outputs into relationship between query and hit sequences. In practice, those relationships are annotated with information about the alignment, such as various scores and the algorithm used.

Let us consider an alignment between two sequences A (query) and B (hit) in the database. After importing the BLAST output you could perform the following queries::

	# We select the sequence 'A'
	A = mdb.Sequence.find_one({"name": "A"})

	# We ask for all relationships of type 'part-of'
	# this sequence could have with other sequences
	for hit in A.list_related_sequences(mdb.Direction.INGOING, {"type": "part-of"}):
		print hit

Importing BLAST sequence alignments: mdb-import-BLAST-alignments
================================================================

Sequence alignments produced by `NCBI BLAST <http://www.ncbi.nlm.nih.gov/blast/Blast.cgi?CMD=Web&PAGE_TYPE=BlastDocs&DOC_TYPE=Download>`_ can be imported and manipulated in MetagenomeDB as relationships between query and hit sequences.

Relevant information about the alignment and HSPs are represented as annotations of these relationships. Those annotations include various scores (E-value, number of gaps, percentage of identity, etc.), the sequences and coordinates of the HSPs, as well as information about the database the BLAST was run against.

In this document you will find a description of how command-line tools can be used to import NCBI BLAST results. Examples of queries of best BLAST hits can be found in :doc:`../examples/index`.

Syntax
------

The ``mdb-import-BLAST-alignments`` command-line tool imports XML-formatted NCBI BLAST outputs::

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
	                        summary of those hits will be stored: hit identifier,
	                        description and E-value.
	    --date=YEAR MONTH DAY
	                        Date of the BLAST run (optional). By default, creation
	                        date of the input file.
	    --query-id-getter=PYTHON CODE
	                        Python code to reformat query identifiers (optional);
	                        '%' will be replaced by the query identifier. Default:
	                        %.split()[0]
	    --hit-id-getter=PYTHON CODE
	                        Python code to reformat hit identifiers (optional); '%'
	                        will be replaced by the hit identifier. Default:
	                        %.split()[0]
	    --no-check          If set, bypass the query and hit sequences identifier
	                        check (not recommended).
	
	  Input filtering:
	    --max-E-value=FLOAT
	                        If set, filter out all hits with a E-value above the
	                        provided cut-off.
	    --min-identity=INTEGER
	                        If set, filter out all hits with a percent of
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

.. note::
	``mdb-import-BLAST-alignments`` can import concatenated XML files resulting from different BLAST runs.

Internal versus external hits
-----------------------------

``mdb-import-BLAST-alignments`` expects query sequences to be stored in MetagenomeDB and to belong to a collection. The name of this collection must be provided using the ``-Q`` (``--query-collection``) option.

Hit sequences, however, may or may not be known of MetagenomeDB. If the hit sequences are in a collection the name of this collection can be provided using the ``-H`` (``--hits-collection``) option. Those hits will later be referenced to as **internal** hits (i.e., internal to the database).

If the hit sequences are not known of MetagenomeDB (e.g., sequences in a public database such as NR) the ``-H`` option can be ignored. In this case the hits will be referred to as **external** hits.

Alignments against internal and external hits are not stored the same way. Internal hits are represented as a relationship from the query to each hit, annotated with information about the HSP and BLAST run. External hits are represented as a list of information about the HSP and BLAST run stored under the property ``alignments`` of the query sequence.

Sequence identifiers
--------------------

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

Any '%' character in the string you provide will be replaced by the value of the query identifier. In this example, the short Python code used above will split the original string (resulting in the list "CH0704v-contig00010", "length=3963", "numreads=678") and select the first element. The same comments applies for ``--hit-id-getter``. For a more complete documentation, see :doc:`id_getters`.

Hits filtering
--------------

The optional ``--max-E-value``, ``--min-identity`` and ``--max-hits`` options can be used to ignore some of the hits contained in the BLAST output.

- ``--max-E-value`` will filter out any hit with a E-value above a provided cut-off
- ``--min-identity`` will filter out any hit with a percent of identity below a provided cut-off
- ``--max-hits`` will filter out any hit below the Nth one for a given query

Connection
----------

The optional ``--host``, ``--port``, ``--db``, ``--user`` and ``--password`` options are common to all MetagenomeDB tools and can be used to bypass the default server connection information found in ``~/.MetagenomeDB``.

.. toctree::
	:hidden:

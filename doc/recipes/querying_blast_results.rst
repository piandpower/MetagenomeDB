Querying BLAST results
======================

Once BLAST results are imported in the database using ``mdb-import-BLAST-alignments`` (see :doc:`../tools/mdb_import_blast_alignments`) the following examples will show you how to proceed to retrieve the best hits of any given sequence.

To understand those examples you need to know the difference between *internal* and *external* hits by reading the documentation of the ``mdb-import-BLAST-alignments`` tool.

Representation of BLAST results
-------------------------------

Any alignment between a query and a hit sequence will result in the following properties being stored:

======================================== =====
Property                                 Value
======================================== =====
``type``                                 Type of relationship (always 'similar-to')
``run.date.year``                        Year the BLAST run was completed
``run.date.month``                       Month the BLAST run was completed
``run.date.day``                         Day the BLAST run was completed
``run.algorithm.name``                   Name of the algorithm (e.g., 'BLASTX')
``run.algorithm.version``                Version of the algorithm (e.g., '2.2.22+')
``run.algorithm.parameters.expect``      Expect value cutoff (BLAST ``-e`` option)
``run.algorithm.parameters.matrix``      Matrix used (BLAST ``-M`` option)
``run.algorithm.parameters.gap_open``    Gap existence cost (BLAST ``-G`` option)
``run.algorithm.parameters.gap_extend``  Gap extension cost (BLAST ``-E`` option)
``run.algorithm.parameters.sc_match``    Match score for nucleotide-nucleotide comparison (BLAST ``-r`` option)
``run.algorithm.parameters.sc_mismatch`` Mismatch penalty for nucleotide-nucleotide comparison (BLAST ``-r`` option)
``run.algorithm.parameters.filter``      Filtering options (BLAST ``-F`` option)
``run.database.name``                    Database name
``run.database.number_of_sequences``     Database size, as the number of sequences
``run.database.number_of_letters``       Database size, as the number of letters
``score.percent_identity``               Percent of identities in the HSP
``score.percent_positives``              Percent of positive substitutions in the HSP
``score.e_value``                        Except value of the HSP
``score.gaps``                           Number of gaps in the HSP
``alignment.source_coordinates``         Coordinates of the alignment in the query sequence
``alignment.source``                     Alignment string for the query
``alignment.match``                      Formatting middle line
``alignment.target``                     Alignment string for the hit
``alignment.target_coordinates``         Coordinates of the alignment in the hit sequence
======================================== =====

Alignments against external hits will also include the following:

=================== =====
Property            Value
=================== =====
``hit.name``        Identifier of the hit
``hit.description`` Description of the hit
``hit.length``      Length of the hit
=================== =====

Alignments against internal hits are stored as properties of the relationship between the query and hit.

Alignments against external hits are stored as a list under the property ``alignments`` of the query sequence.

Iterating through internal hits
-------------------------------

Alignments against internal hits are stored as annotations of the relationship between the query and each hit::

	# we retrieve a sequence as our query
	query = mdb.Sequence.find_one({"name": "my query sequence 1"})

	# hits will be represented as related sequences; they can be accessed
	# by listing all sequences 'query' relates to. As we are interested in
	# alignments only, we filter those neighboring sequences to those with
	# a 'similar-to' type of relationship:
	for hit in query.list_related_sequences(mdb.Direction.OUTGOING, {}, {"type": "similar-to"}):
		# once a hit sequence located, each HSP is represented as a
		# distinct annotated relationship between 'query' and 'hit':
		for hsp in query.list_relationships_with(hit):
			# we print the hit name and the HSP E-value
			print "\nHit: '%s' (E-value: %.2g)" % (hit["name"], hsp["score"]["e_value"])

			# we retrieve the HSP sequences and coordinates
			print "%s %s" % (hsp["alignment"]["source"], hsp["alignment"]["source_coordinates"])
			print hsp["alignment"]["match"]
			print "%s %s" % (hsp["alignment"]["target"], hsp["alignment"]["target_coordinates"])

Iterating through external hits
-------------------------------

Alignments against external hits are stored as a ``alignments`` property of the query sequence::

	# we retrieve a sequence as our query, ensuring it does have a 'alignments' property
	query = mdb.Sequence.find_one({"alignments": {"$exists": True}})
	print "Query: '%s'" % query["name"]

	# for each HSP this query have with external hits,
	for hsp in query["alignments"]:
		# we print the hit name and the HSP E-value
		print "\nHit: '%s' (E-value: %.2g)" % (hsp["hit"]["name"], hsp["score"]["e_value"])
	
		# we retrieve the HSP sequences and coordinates
		print "%s %s" % (hsp["alignment"]["source"], hsp["alignment"]["source_coordinates"])
		print hsp["alignment"]["match"]
		print "%s %s" % (hsp["alignment"]["target"], hsp["alignment"]["target_coordinates"])

Output (excerpt)::

	Hit: 'gi|291327153|ref|ZP_06574216.1|' (E-value: 0.00018)
	MSAFSLPIPPRSLATPLHQLRERSAT--------ALSSPKLRWAA*APLHFPRRIA*PVSCYAFFK [182, 355]
	MSAF+L IPP  L   LH+L ERS T        A S   L     APLH PRR   PVS YAFFK
	MSAFALLIPPACLTAHLHRLTERSPTQQYLHIAAAASVHSL-----APLHLPRRPTRPVSYYAFFK [1, 61]
	
	Hit: 'gi|6460058|gb|AAF11800.1|AE002057_8' (E-value: 0.00018)
	TWFPSTTPFGLALGAG*PCAD*LYAGTLGLSARGSLTLFVATHVSILTSHTSTESRDSASPA*GTLRYRSF----EPEASVGGLSPVTF [228, 482]
	T  PS  PFGL LG   P AD    GTL L+A+  LT F+ TH  I TS  ST     ASP       R      E  ASV  LSP  F
	TCCPSAAPFGLTLGPDFPWADDPSPGTLVLTAKKILTSFIVTHAGIRTSVGSTTPSGMASPRTERSPTRQLASRVESIASVDHLSPDHF [2, 90]
	
	Hit: 'gi|6460058|gb|AAF11800.1|AE002057_8' (E-value: 0.0026)
	PRSLATPLHQLRERSATALSSPKLRWAA*APLHFPRRIA*PVSCYAFFK*WLLLSQHPGC [149, 328]
	PR+  +P  QL  R  +  S   L     +P HF R +  PVS YA F+ WLLLSQ PGC
	PRTERSPTRQLASRVESIASVDHL-----SPDHFRRIVTRPVSYYALFEGWLLLSQPPGC [62, 116]

.. note::
	The major difference between iterating through internal and external hits is the way multiple HSPs between a query and a hit are represented. For internal hits HSPs are represented as multiple relationships between a query and hit object. For external hits HSPs are represented as multiple entries in the ``alignments`` property of the query object. Another difference is, for the later case, the presence of the ``hit.name``, ``hit.description`` and ``hit.length`` properties.

Retrieving the best hit
-----------------------

To search for the best external hit of each query sequence among all BLAST runs that have been imported you can use the following code::

	# first, we select the collection that contains our queries
	queries = mdb.Collection.find_one({"name": "..."})

	# for each query sequence in 'queries' that have a 'alignments'
	# property (meaning it have been annotated with BLAST results against
	# sequences external to the database),
	for query in queries.list_sequences({"alignments": {"$exists": True}}):
		# we set an initial best E-value to an absurd high value
		# and prepare 'best_hit' to receive the best hit (and possible ties)
		best_evalue = 100
		best_hit = []

		# then, for each HSP against external hits (regardless of the BLAST run),
		for hsp in query["alignments"]:
			# we retrieve the E-value
			evalue = hsp["score"]["e_value"]

			# if this E-value is better (i.e., lower) than the
			# previously known best E-value we store the hit as
			# the new best one
			if (evalue < best_evalue):
				# if true, we store this new best hit
				best_hit = [hsp]
				best_evalue = evalue

			# if the E-value is the same as the best one known
			# so far, we store this hit as a tie
			elif (evalue == best_evalue):
				best_hit.append(hsp)

		# at this stage, 'best_hit' contains the best hit (or list
		# of best hits in case of ties) for the sequence in 'query':
		print "Best hit(s) for %s (with E-value %.2g):" % (query, best_evalue)
		print best_hit["hit"]["name"]

If you want to distinguish between BLAST runs the code becomes::

	import pickle

	# first, we select the collection that contains our queries
	queries = mdb.Collection.find_one({"name": "..."})

	# for each query sequence in 'queries' with known external hits,
	for query in queries.list_sequences({"alignments": {"$exists": True}}):
		# we create two dictionaries which, for each BLAST
		# run, will store the best hit and E-value
		best_hit = {}
		best_evalue = {}
	
		# for each HSP against an external hit,
		for hsp in query["alignments"]:
			# we create a BLAST run signature; i.e., a value that is
			# guaranteed to be uniquely associated to each run. This
			# signature will be used to keep track of the best hits
			# for each run
			run_signature = pickle.dumps(hsp["run"])
	
			# if we see this BLAST run for the first time, we set
			# its best hit to dummy values
			if (not run_signature in best_hit):
				best_hit[run_signature] = []
				best_evalue[run_signature] = 100
	
			evalue = hsp["score"]["e_value"]
	
			# if the E-value is lower than the previously known
			# best one, we store the new best hit for this run
			if (evalue < best_evalue[run_signature]):
				best_hit[run_signature] = [hsp]
				best_evalue[run_signature] = evalue
	
			# in case of tie, we store the additional best hit
			elif (evalue == best_evalue[run_signature]):
				best_hit[run_signature].append(hsp)
	
		# we can now print the best hit for each one of the BLAST
		# this query sequence has be run through:
		for run_signature in best_hit:
			run = pickle.loads(run_signature)
			print "Best hit(s) for %s according to run %s" % (query, run)
			print best_hit[run_signature]["hit"]["name"], best_evalue[run_signature]
	

Retrieving the best hits
------------------------

If you are interested in the *n* best hits (instead of just the best one) across all BLAST runs the code becomes::

	# number of best hits we want to keep
	N = 10
	
	# for each query sequence with known external hits,
	for query in queries.list_sequences({"alignments": {"$exists": True}}):
		best_hits = [[]]
		best_evalues = [100]
	
		# for each HSP against an external hit,
		for hsp in query["alignments"]:
			evalue = hsp["score"]["e_value"]
	
			# if the E-value of this HSP is lower than the worst
			# E-value among the N best hits stored in 'best_hits',
			if (evalue < max(best_evalues)):
				# we add this hit to the list of best ones
				best_hits.append([hsp])
				best_evalues.append(evalue)
	
			# if the E-value of this HSP is already part of the
			# best E-values,
			elif (evalue in best_evalues):
				# we find the one hit among the best ones
				# with the same E-value as the current hit,
				p = None
				for i in range(len(best_evalues)):
					if (best_evalues[i] == evalue):
						p = i
						break
				# then we store the current hit as a tie
				best_hits[p].append(hsp)
	
			# if the list of best hits is bigger than N,
			if (len(best_hits) > N):
				# we create a combined list of the best hits
				# and their E-values
				best = zip(best_hits, best_evalues)
				# and sort this list by increasing E-value
				best.sort(lambda x, y: cmp(x[1], y[1]))
				# then we remove all hits above the Nth
				best = list[:N]
				# finally, we repopulate 'best_hits' and
				# 'best_evalues' with the remainder
				best = [list(l) for l in zip(*best)]
				best_hits, best_evalues = best

		print "Best %s hits for %s:" % (N, query)
		for best_hit, best_evalue in zip(best_hits, best_evalues):
			print best_hit["hit"]["name"], best_evalue

As above, the code has to be modified if you want to distinguish between BLAST runs::

	N = 10
	
	for query in queries.list_sequences({"alignments": {"$exists": True}}):
		best_hits = {}
		best_evalues = {}
	
		for hsp in query["alignments"]:
			run_signature = pickle.dumps(hsp["run"])
	
			if (not run_signature in best_hits):
				best_hits[run_signature] = [[]]
				best_evalues[run_signature] = [100]
	
			evalue = hit["score"]["e_value"]
	
			if (evalue < max(best_evalues[run_signature])):
				best_hits[run_signature].append([hsp])
				best_evalues[run_signature].append(evalue)
	
			elif (evalue in best_evalues[run_signature]):
				p = None
				for i in range(len(best_evalues[run_signature])):
					if (best_evalues[run_signature][i] == evalue):
						p = i
						break
				best_hits[run_signature][p].append(hsp)
	
			if (len(best_hits[run_signature]) > N):
				best = zip(best_hits[run_signature], best_evalues[run_signature])
				best.sort(lambda x, y: cmp(x[1], y[1]))
				best = best[:N]
				best = [list(l) for l in zip(*best)]
				best_hits[run_signature], best_evalues[run_signature] = best
	
		for run_signature in best_hits:
			run = pickle.loads(run_signature)
			print "Best %s hits for %s according to run %s:" % (N, query, run)
			for best_hit, best_evalue in zip(best_hits[run_signature], best_evalues[run_signature]):
				print best_hit, best_evalue

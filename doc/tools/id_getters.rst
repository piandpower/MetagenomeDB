Sequence identifiers setters and getters
========================================

Some of the mdb tools (namely, ``mdb-import-ACE-alignments``, ``mdb-import-BLAST-alignments`` and ``mdb-import-CRISPRfinder-alignments``) have options with names ``--id-getter``, ``--read-id-getter``, etc. These 'getter' options allow on-the-fly modifications of sequence identifiers as they are read from the input files.

Getter options are useful when the input files and the sequence collections you are processing describe the same sequences, but with some minor differences in their names: additional prefixes, suffixes, lower case, etc.

Let us imagine a case where a user imported reads from the following FASTA file in a collection 'my_reads'::

	>eg:sequence_a
	actgatcgatcatcgatcatcga
	>eg:sequence_b
	gtctagcatgcatgcatatatgc

Notice the 'eg:' prefix in all sequence names.

The user now wants to connect those reads to some contigs in another collection ('my_contigs'). However, the ACE file was generated with another version of the FASTA file above, that didn't have the 'eg:' prefix.

Importing this ACE file directly will cause ``mdb-import-ACE-alignments`` to report an error about missing reads 'sequence_a' and 'sequence_b'. However, thanks to its ``--read-id-getter`` option we can correct these read names on-the-fly and append the prefix::

$ mdb-import-ACE-alignments -i my_ACE_file.ace --reads-collection my_reads --contigs-collection my_contigs --read-id-getter "'eg:'+%"

Syntax
------

Getter options expect a valid Python expression. Any occurrence of the symbol ``%`` in this expression will be replaced by the original sequence identifier. The final sequence identifier is then taken as the result of executing this Python expression. Hence, ::

	--read-id-getter "%"

will take the original sequence identifier, and return it unmodified. This is the default behavior for all getter options.

Within the Python expression, ``%`` is a string. As such, you have access to all string methods. For example, ::

	--read-id-getter "%.upper()"

will transform all read identifiers into their upper-case version.

The standard ``re`` library is available if you want to use regular expression; for example, ::

	--read-id-getter "re.search('F[0-9]{4}', %).group(0)"

will return the first occurrence of the pattern ``F[0-9]{4}`` (i.e., the letter 'F' followed by four digits; see this `documentation <http://docs.python.org/howto/regex.html#regex-howto>`_) found in the read identifier.

.. note::
	In some case you will want to use the character ``%`` in your Python expression; e.g., when using `string formatting <http://docs.python.org/release/2.5.2/lib/typesseq-strings.html>`_. To protect those symbols from being replaced by a sequence identifier, append a '\\'. For example, ::

		--read-id-getter "'\%s.\%s' \% (%[:3], %[5:])"

	will translate into the expression ``'%s.%s' % (name[:3], name[5:])`` with ``name`` being a variable containing the sequence identifier.

.. note::
	The Python expression must be quoted. In all examples given here, it is double-quoted; however you can use single-quotes as well. You must take care of distinguishing the quotes you use for the expression and the quotes you use *within* this expression when manipulating strings. Hence,  ::

		"'prefix' + %"

	is correct, because you used single-quotes for the string 'prefix' while using double-quotes for the Python expression itself. However, ::

		""prefix" + %"

	will fail because both quotes are mixed. If you want to use only double- (or single-) quotes, you must protect those *within* the expression::

		"\"prefix\" + %"

Examples
--------

Here are various examples of syntax, and how they modify the original sequence identifier:

================================================================ ===================================== ==================
Expression                                                       Original identifier                   Final identifier
================================================================ ===================================== ==================
``"'CH0704v-' + %"``                                             FGH9539234                            CH0704v-FGH9539234
``"%[:14]"``                                                     FKNZE9C02TIT1I(Rev-Comp)              FKNZE9C02TIT1I
``"%.split('.')[0]"``                                            GWERI32JK23JK.r1.rc                   GWERI32JK23JK
``"re.search('G[A-Z0-9]{13}', %).group(0)"``                     CH1002c-dr1_GHE03TT01A28PQ-length-254 GHE03TT01A28PQ
``"'\%s.\%s' \% re.search('(F[A-Z0-9]+)-([bg]1)', %).groups()"`` NL0708c-FUBF10638-b1(Rev-Comp)        FUBF10638.b1
================================================================ ===================================== ==================

.. toctree::
	:hidden:

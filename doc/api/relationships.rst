Relationships (INCOMPLETE)
==========================

This document contains important information about how relationships between objects are represented in the database, and how it affects the way queries about an object's neighbors will behave.

Relationships are directed
--------------------------

An important concept in MetagenomeDB is that a relationship between two objects is *directed*. I.e., in any relationship there is a *source* and a *target*. As such, linking a sequence A to another sequence B is different from linking the same sequence B to sequence A::

	>>> # we retrieve two sequences, 'sequence1' and 'sequence2'
	>>> s1 = mdb.Sequence.find_one({"name": "sequence1"})
	>>> s2 = mdb.Sequence.find_one({"name": "sequence2"})

	>>> # we link s1 to s2
	>>> s1.relate_to_sequence(s2)

	>>> # we also link s2 to s1
	>>> s2.relate_to_sequence(s1)

This concept is important when you search for objects that are related to a given object of interest (*neighbors*). Methods in the API allow you to distinguish between objects *pointing to* your object, and objects your object *points to*. A typical example are collections: a given collection may have super- and sub-collections.

Relationships can be annotated
------------------------------


Relationships must be committed
-------------------------------

Relationships between a source and a target object are considered a property of the *source* object. As such, and as a general rule, any source object that is connected to a target must be committed for this relationship to be acknowledged by the API.

There are some exceptions to this rule; i.e., in some situations you can query an object's neighbor without having this object committed. Those exceptions are:

Sequence.add_to_collection(): Until then calls to :meth:`Collection.list_sequences()
			  <objects.Collection.list_sequences>` and :meth:`Collection.count_sequences()
			  <objects.Collection.count_sequences>` will not acknowledge the new
			  relationship (although :meth:`~objects.Sequence.list_collections`
			  and :meth:`~objects.Sequence.count_collections` will as long as
			  their **relationship_filter** parameter is not set).

Sequence.relate_to_sequence(): Until then calls to **sequence.**:meth:`~objects.Sequence.list_related_sequences`
			  and **sequence.**:meth:`~objects.Sequence.count_related_sequences` 
			  with parameter **direction** set to :attr:`Direction.INGOING <objects.Direction.INGOING>`
			  will not acknowledge the new relationship (also :meth:`~objects.Sequence.list_related_sequences`
			  and :meth:`~objects.Sequence.count_related_sequences` will as long
			  as their **relationship_filter** parameter is not set).

			- If **relationship_filter** is set additional queries are issued
			  to the database, which require this sequence to be committed first.
			  If this is not the case, a :class:`~errors.UncommittedObjectError`
			  exception is thrown. See :doc:`relationships`.


.. toctree::
   :hidden:

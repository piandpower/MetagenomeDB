Relationships
=============

This document contains important information about how relationships between objects are represented in the database, and how it affects the way queries about an object's neighbors will behave.

Relationships are directed
--------------------------

An important concept in MetagenomeDB is that a relationship between two objects is always *directed*. I.e., in any relationship there is a *source* and a *target*. As such, linking for example a sequence A to another sequence B (using its :meth:`Sequence.relate_to_sequence() <objects.Sequence.relate_to_sequence>` method) doesn't imply that B is linked to A (as tested by the :meth:`~objects.CommittableObject.has_relationships_with` method)::

	>>> # we retrieve two sequences, 'sequence1' and 'sequence2'
	>>> s1 = mdb.Sequence.find_one({"name": "sequence1"})
	>>> s2 = mdb.Sequence.find_one({"name": "sequence2"})

	>>> # if we link s1 to s2,
	>>> s1.relate_to_sequence(s2)

	>>> # then a relationship from s1 to s2 do exists
	>>> print s1.has_relationships_with(s2)
	True

	>>> # however the opposite is not true
	>>> print s2.has_relationships_with(s1)
	False

This concept is important when you search for objects that are related to a given object of interest (*neighbors*). Methods in the API allow you to distinguish between objects *pointing to* your object, and objects your object *points to*:

- :meth:`Sequence.list_collections() <objects.Sequence.list_collections>` and :meth:`Sequence.count_collections() <objects.Sequence.count_collections>` will list (or count) all collections a given sequence is related to. There is no ambiguity here, as the reverse link (a collection linked to a sequence) makes no biological sense.
- :meth:`Sequence.list_related_sequences() <objects.Sequence.list_related_sequences()>` and :meth:`Sequence.count_related_sequences() <objects.Sequence.count_related_sequences()>` will list (or count) all sequences that are related to a given sequence, and/or the sequences a given sequence relates to (depending of the value set for the **direction** parameter). For example::

	>>> # if we list sequences related to s1, we find nothing:
	>>> print list(s1.list_related_sequences(mdb.Direction.INGOING))
	[]

	>>> # however, if we list sequences s1 relates to, we find s2:
	>>> print list(s1.list_related_sequences(mdb.Direction.OUTGOING))
	[<Sequence id:... name:'sequence2' length:4 state:'committed'>]

	>>> # by default, both directions are explored:
	>>> print list(s1.list_related_sequences())
	[<Sequence id:... name:'sequence2' length:4 state:'committed'>]

- :meth:`Collection.list_related_collections() <objects.Collection.list_related_collections()>` and :meth:`Collection.count_related_collections() <objects.Collection.count_related_collections()>` will list (or count) all collections that are related to this collection (*sub*-collections), and/or the collections this collection relates to (*super*-collections). Aliases are available to access sub- or super-collections (:meth:`Collection.list_sub_collections() <objects.Collection.list_sub_collections()>` is equivalent to calling :meth:`Collection.list_related_collections() <objects.Collection.list_related_collections()>` with **direction** set to ``mdb.Direction.INGOING``, while :meth:`Collection.list_super_collections() <objects.Collection.list_super_collections()>` is equivalent to calling :meth:`Collection.list_related_collections() <objects.Collection.list_related_collections()>` with **direction** set to ``mdb.Direction.OUTGOING``).

.. note::
	All those methods accept filters for both neighbor objects and the relationship between the current object and its neighbors. See :doc:`queries` for information about how to create filters.

Relationships can be annotated
------------------------------

All methods that create a relationship between objects (:meth:`Sequence.add_to_collection() <objects.Sequence.add_to_collection>`, :meth:`Sequence.relate_to_sequence() <objects.Sequence.relate_to_sequence>`, and :meth:`Collection.add_to_collection() <objects.Collection.add_to_collection>`) accept as a second argument a description of this relationship. This description is represented the same way as for objects' annotations; i.e., as a dictionary (see :doc:`annotations`)::

	>>> s1.relate_to_sequence(s2, {"property_of_relationship": "foo"})

As for objects' annotations, relationship descriptions can have nested properties, declared using either nested dictionaries or dot notation::

	>>> s1.relate_to_sequence(s2, {"monty": {"python": "bar"}})

Describing a relationship between objects is useful to explain why the *source* should be connected to its *target*. For example, a convention enforced by the mdb-tools (see :doc:`../tools/index`) is to annotate relationships between sequences with a property 'type', of which value is either 'part-of' (when a sequence is part of another sequence; e.g., a read that is part of a contig) or 'similar-to' (when a sequence is similar to another sequence; e.g., as shown by a BLAST run). Those same tools also add annotations about how the relationship was established, using which technique, any associated score, etc.

.. note::
	Two objects can be linked by more than one relationship, as long as their annotations are distinct. In the following example,

		>>> s1.relate_to_sequence(s2, {"relationship_property": "foo"})
		>>> s1.relate_to_sequence(s2, {"relationship_property": "bar"})
		>>> s1.relate_to_sequence(s2, {"relationship_property": "foo"})

	Only the two first instructions will result in the addition of a relationship between s1 and s2. The third is a duplicate of the first, and will be ignored.

Relationships must be committed
-------------------------------

Relationships between a source and a target object are stored as a property of the *source* object. As such, and as with any property an object is annotated with, this relationship will be lost if the source object is not committed before being discarded (see :doc:`annotations`).

There is another important consequence of not committing a new relationship: this relationship will be invisible to most methods that list or count neighbor objects::

	>>> # let's retrieve two collections, previously unrelated:
	>>> c1 = mdb.Collection.find_one({"name": "collection1"})
	>>> c2 = mdb.Collection.find_one({"name": "collection2"})

	>>> # if we create a link from c1 (source) to c2 (target), but do not commit it,
	>>> c1.add_to_collection(c2)
	>>> print c1.is_committed()
	False

	>>> # this relationship is only visible from c1:
	>>> print list(c1.list_related_collections(mdb.Direction.OUTGOING))
	[<Collection id:... name:'collection2' state:'committed'>]
	>>> print list(c1.list_super_collections())
	[<Collection id:... name:'collection2' state:'committed'>]

	>>> # but not from c2:
	>>> print list(c2.list_related_collections(mdb.Direction.INGOING))
	[]
	>>> print list(c2.list_sub_collections())
	[]

Knowing which method will or will not assess a new relationship can be confusing. As a general rule, you should always commit a source object after you connected it to a target object.

.. note::
	When creating a relationship between a *source* and a *target* object the target must have been committed at least once in the database. If not an exception will be thrown. The reason for this constraint is the need for the API to have an internal identifier in the database when linking both objects. This identifier is only created the first time an object is committed.

.. toctree::
   :hidden:

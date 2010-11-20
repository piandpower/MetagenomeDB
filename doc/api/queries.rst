Queries
=======

This document is an introduction on querying object with the MetagenomeDB API.

Both :class:`~objects.Sequence` and :class:`~objects.Collection` classes have a :meth:`~objects.CommittableObject.find` method to select, among all sequences or collections in the database, all those that match a specific *filter*. The :meth:`~objects.CommittableObject.count` method will return a count, rather than a list, of these objects.

Other methods, specific to :class:`~objects.Sequence` and :class:`~objects.Collection`, allow to select (or count) objects that are *related* to a given sequence or collection (see :doc:`relationships`). Those methods have parameters such as **collection_filter**, **sequence_filter** or **relationship_filter**; all of them use the same syntax, described below.

.. note::
   Similar to :meth:`~objects.CommittableObject.find` is :meth:`~objects.CommittableObject.find_one`, which return the first object that match your filter. This method is useful when you know there is only one object in the whole database that can match this filter. For example, only one collection in the whole database can have a given name (you cannot store two collections with the same name). As such, you can retrieve a collection by typing::

	>>> c = mdb.Collection.find_one({"name": "my collection"})

   :meth:`~objects.CommittableObject.find_one` is also useful when you want to pick an example of object that match a filter, even when you expect there are more in the database.

Basic filters
-------------

*Filters* are dictionaries with a set of properties and their associated values that objects have to match to be selected. For example, ``{"name": "foo"}`` will select only those objects with a value 'foo' for the property 'name'::

	>>> # select all sequences in the database with name 'foo'
	>>> print mdb.Sequence.find({"name": "foo"})

	>>> # count all sequences in the database with name 'bar'
	>>> print mdb.Sequence.count({"name": "bar"})

You can filter for more than one property at a time. For example, to select objects with value "foo" for property "property1" and "bar" for property "property2", you would type::

	>>> print mdb.Sequence.find({"property1": "foo", "property2": "bar"})

Finally, you can query nested properties (see :doc:`annotations`) by using either nested dictionaries or the dot-notation. If you are looking for all objects with value "foo" for the sub-property "python" of the property "monty", you can type either of the two following lines::

	>>> print mdb.Sequence.find({"monty": {"python": "foo"}})
	>>> print mdb.Sequence.find({"monty.python": "foo"})

.. note::
   An empty filter will select all objects in the database of the given type::

   	>>> # count the number of sequences in the whole database
   	>>> print mdb.Sequence.count()
   	>>> print mdb.Sequence.count({}) # alternative syntax

Advanced queries
----------------

*Filters* can use operators and modifiers from MongoDB (see MongoDB `documentation <http://www.mongodb.org/display/DOCS/Advanced+Queries>`_). For example, the **$or** modifier allows to search for objects that satisfy *any* (rather than *all*) of a list of properties and values::

	>>> # select all sequences with name 'foo' OR 'bar'
	>>> print mdb.Sequence.find({"$or": [{"name": "foo"}, {"name": "bar"}]})

	>>> # select all sequences with value 'foo' for property 'property1' OR value 'bar' for property 'property2'
	>>> print mdb.Sequence.find({"$or": [{"property1": "foo"}, {"property2": "bar"}]})

The MongoDB `documentation <http://www.mongodb.org/display/DOCS/Advanced+Queries>`_ list additional operators and modifiers. Among the most useful ones::

	>>> # select all sequences with value other than 'bar' for property 'property'
	>>> print mdb.Sequence.find({"property": {"$ne": "bar"}})

	>>> # select all sequences with length greater than or equal to 100
	>>> print mdb.Sequence.find({"length": {"$gte": 100}})

	>>> # select all sequences that have a 'property' property
	>>> print mdb.Sequence.find({"property": {"$exists": True}})


.. toctree::
   :hidden:

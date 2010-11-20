Annotations
===========

All objects in MetagenomeDB can be annotated with arbitrary values. MetagenomeDB uses the Python `dictionary <http://docs.python.org/tutorial/datastructures.html#dictionaries>`_ metaphor both for setting and for retrieving these annotations.

Setting annotations
-------------------

Once a object is created (or selected) it can be annotated using the Python ``[]`` dictionary-like syntax::

	>>> # we create a new sequence
	>>> s = mdb.Sequence({"name": "my sequence", "sequence": "atgc"})

	>>> # we assign 'read' as a value for a 'type' property
	>>> s["type"] = "read"

Any value already associated to a property 'type' is replaced by the new value. If this property doesn't exist for this object, it is created automatically.

Values can be of any type::

	>>> # assigning a number
	>>> s["a_number"] = 3

	>>> # assigning a boolean
	>>> s["a_boolean"] = True

	>>> # assigning a list
	>>> s["a_list] = [1, 2, 3]

Properties can be nested; i.e., the value for a property can be a set of other properties. This allow for the easy grouping of related properties, such as various scores for a given test. Nested properties can be set using either nested dictionaries or a *dot-notation*::

	>>> # store various scores for a given test using a dictionary notation
	>>> s["results"] = {
	...	"test1": True,
	...	"test2": "passed",
	...	"test3": 1e-6
	... }

	>>> # store various scores for a given test using a dot-notation
	>>> s["results.test1"] = True
	>>> s["results.test2"] = "passed"
	>>> s["results.test3"] = 1e-6

A good example of use of nested properties is the storage of a BLAST hit, as performed by ``mdb-import-BLAST-alignments`` (see :doc:`../tools/blast`).

.. note::
   For the dot-notation to be possible, property names have one restriction: they cannot contain a dot ('.').


Retrieving annotations
----------------------

All :class:`~objects.Sequence` and :class:`~objects.Collection` objects have two methods to retrieve annotations, :meth:`~objects.MutableObject.get_property` and :meth:`~objects.MutableObject.get_properties`. The former will retrieve the value for a given property (or a default value if this property is not set for this object), while the later return all properties of the object as a dictionary::

	>>> print s.get_property("a_number")
	3
	>>> print s.get_property("a_novel_property", "default value")
	'default value'
	>>> print s.get_properties()
	{'length': 4, '_relationship_with': [], 'name': 'my sequence', '_relationships': {},
	 'sequence': 'atgc', 'results': {'test1': True, 'test3': 1e-06, 'test2': 'passed'},
	 'a_number': 3, 'a_boolean': True, 'a_list': [1, 2, 3]}

.. note::
	- The properties returned by :meth:`~objects.MutableObject.get_properties` are shown in no particular order.
	- You can notice several properties that you never annotated the sequence with, such as ``_relationships``. All properties that start with a ``_`` are used internally by the MetagenomeDB toolkit and cannot be directly modified by the user.

Properties can also be directly accessed using the dictionary syntax::

	>>> print s["a_number"]
	3

.. note::
	The difference between using :meth:`~objects.MutableObject.get_property` and a dictionary syntax is that the former can be set to return a default value in case the property you are looking for has not been set for this object. If you use a dictionary syntax for an unknown property, an exception will be thrown:

		>>> print s["a_novel_property"]
		Traceback (most recent call last):
		  File "<stdin>", line 1, in <module>
		  File "/Users/ajmazurie/.lib/python/MetagenomeDB/objects.py", line 71, in __getitem__
		    return copy.deepcopy(tree.get(self._properties, key_))
		  File "/Users/ajmazurie/.lib/python/MetagenomeDB/utils/tree.py", line 49, in get
		    return d[key]
		KeyError: 'a_novel_property'

Finally, nested properties can be accessed using either :meth:`~objects.MutableObject.get_property` or the dictionary syntax::

		>>> print s.get_property("results.test1")
		True
		>>> print s["results.test1"]
		True
		>>> print s["results"]["test1"]
		True

Saving annotations
------------------

A very important concept in MetagenomeDB is that your objects exists in two locations: in the database, and in the memory of your computer. At first the memory of your computer is empty, but whenever you are creating an object or retrieving one from the database a copy of it is placed in this memory. When you are manipulating an object by annotating it you are modifying the copy **in memory**, and NOT the copy in the database.

As such, when you are done modifying an object you must **commit** it to the database. Only then this object will become queryable; i.e., visible for methods such as :meth:`~objects.CommittableObject.find` or :meth:`~objects.CommittableObject.count` (see :doc:`queries`).

Committing an object only requires to call its :meth:`~objects.CommittableObject.commit` method:

	>>> s.commit()

Remember, any modification you make to an object after it is retrieved from the database will be lost if you do not commit those changes. If an object is deleted before it is committed a warning will be displayed::

	>>> del s
	2010-11-19 16:16:29,964	WARNING: Object <Sequence id:none name:'my sequence' length:4
	state:'uncommitted'> has been destroyed without having been committed.	__del__() in
	objects.py, line 537

You can test if an object has been committed since its latest modification by calling its :meth:`~objects.CommittableObject.is_committed` method::

	>>> print s.is_committed()
	True

Objects that have been retrieved from the database after a query (see :doc:`queries`) are committed by default until they are modified. Objects that are created are uncommitted by default::

	>>> # we create a sequence 's1'
	>>> s1 = mdb.Sequence({"name": "a sequence", "sequence": "atgc"})

	>>> # we retrieve an existing sequence and assign it to 's2'
	>>> s2 = mdb.Sequence.find_one({"name": "another sequence"})

	>>> # s1 is not committed by default
	>>> print s1.is_committed()
	False

	>>> # while s2 is committed by default
	>>> print s2.is_committed()
	True

	>>> # however, if we modify s2,
	>>> s2["foo"] = "bar"

	>>> # it is no more committed
	>>> print s2.is_committed()
	False

.. toctree::
   :hidden:

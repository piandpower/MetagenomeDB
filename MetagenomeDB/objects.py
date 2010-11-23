# objects.py: object representation of the MongoDB content

import sys, datetime, itertools, copy, logging
import bson

import backend, errors
from utils import tree

logger = logging.getLogger("MetagenomeDB.objects")

def parse_properties (properties):
	properties_ = {}
	for key, value in properties.iteritems():
		key = tree.validate_key(key)
		tree.set(properties_, key, value)

	return properties_

class MutableObject (object):
	""" MutableObject: Base object that can receive arbitrary properties.
	"""

	def __init__ (self, properties):
		""" Create a new object.

		Parameters:
			- **properties** (optional): object annotations, as a dictionary.
			  Nested properties can be expressed using dot notation or by nested
			  dictionaries.
		"""
		self._properties = parse_properties(properties)
		self._modified = False

	def get_properties (self):
		""" Return a copy of all of this object's properties, as a dictionary.

		.. seealso::
			:meth:`~objects.MutableObject.get_property`
		"""
		return self._properties.copy()

	def get_property (self, key, default = None):
		""" Return the value for a given property.

		Parameters:
			- **key**: property to retrieve; see :doc:`annotations`.

		.. seealso::
			:meth:`~objects.MutableObject.get_properties`
		"""
		try:
			return copy.deepcopy(self.__getitem__(key))

		except KeyError:
			return default

	def __setitem__ (self, key, value):
		key_ = tree.validate_key(key)
		self._modified = False

		# discard 'phantom' modifications
		if tree.contains(self._properties, key_) and \
		   (value == tree.get(self._properties, key_)):
			return

		tree.set(self._properties, key_, value)
		self._modified = True

	def __getitem__ (self, key):
		key_ = tree.validate_key(key)
		return copy.deepcopy(tree.get(self._properties, key_))

	def __delitem__ (self, key):
		key_ = tree.validate_key(key)

		tree.delete(self._properties, key_)
		self._modified = True

	def __contains__ (self, key):
		key_ = tree.validate_key(key)
		return tree.contains(self._properties, key_)

class CommittableObject (MutableObject):
	""" CommittableObject: Object that can be committed to the backend database.
	"""

	def __init__ (self, indices, properties):
		""" Create a new object.

		Parameters:
			- **properties** (optional): object annotations, as a dictionary.
			  Nested properties can be expressed using dot notation or by nested
			  dictionaries.
		"""
		MutableObject.__init__(self, properties)

		# if the object is provided with an identifier,
		# we check if this identifier is present in the
		# object cache to know if it was committed.
		if ("_id" in self._properties):
			id = self._properties["_id"]

			if (type(id) == str):
				id = bson.objectid.ObjectId(id)
				self._properties["_id"] = id

			if (not backend.exists(id)):
				raise errors.MetagenomeDBError("Unknown object identifier '%s'." % id)

			self._committed = True
		else:
			self._committed = False

		if (not "_relationships" in self._properties):
			self._properties["_relationship_with"] = []
			self._properties["_relationships"] = {}

		self._indices = indices
		self._indices["_relationships_with"] = False

	def __setitem__ (self, key, value):
		key_ = tree.validate_key(key)

		if (key_[0].startswith('_')):
			raise errors.MetagenomeDBError("Property '%s' is reserved and cannot be modified." % key)

		MutableObject.__setitem__(self, key, value)
		self._committed = not self._modified

	def __delitem__ (self, key):
		key_ = tree.validate_key(key)

		if (key_[0].startswith('_')):
			raise errors.MetagenomeDBError("Property '%s' is reserved and cannot be modified." % key)

		MutableObject.__delitem__(self, key)
		self._committed = False

	def commit (self):
		""" Commit this object to the database.

		.. note::
			- The commit will not be performed if the object has already been
			  committed once and no modification (property manipulation) has
			  been performed since then.
			- If an object already exists in the database with the same values
			  for properties flagged as unique a :class:`~errors.DuplicateObjectError`
			  exception is thrown.

		.. seealso::
			:meth:`~objects.CommittableObject.is_committed`
		"""
		if (self._committed):
			return

		"""
		# pre-flight: if some patch needs to be applied on the object's
		# properties, we temporary store the old values
		tmp = {}
		for (key, value) in patch.iteritems():
			assert (key != "_id") ###
			tmp[key] = self._properties[key]
			self._properties[key] = value
		"""

		backend.commit(self)

		"""
		# post-flight: we restore the object's properties, if needed
		for (key, value) in tmp.iteritems():
			self._properties[key] = value
		"""

		self._committed = True

	def is_committed (self):
		""" Test if this object has been committed to the database since
			its latest modification.

		.. seealso::
			:meth:`~objects.CommittableObject.commit`
		"""
		return self._committed

	@classmethod
	def count (cls, filter = None):
		""" Count the number of objects of this type in the database.
		
		Parameters:
			- **filter**: filter for the objects to count (optional); see
			  :doc:`queries`.

		.. seealso::
			:meth:`~objects.CommittableObject.find`
		"""
		return backend.count(cls.__name__, query = filter)

	@classmethod
	def distinct (cls, property):
		""" For each value found in the database for a given property, return
		the number of objects that have this value.

		Parameters:
			- **property**: property to count objects for.

		Return:
			A dictionary with all values found for this property as keys, and
			number of objects having this value as values.
		"""
		return backend.distinct(cls.__name__, property)

	@classmethod
	def find (cls, filter = None):
		""" Find all objects of this type that match a query.
		
		Parameters:
			- **filter**: filter for the objects to select (optional); see
			  :doc:`queries`.

		Return:
			A generator.

		.. seealso::
			:meth:`~objects.CommittableObject.count`, :meth:`~objects.CommittableObject.find_one`
		"""
		return backend.find(cls.__name__, query = filter)

	@classmethod
	def find_one (cls, filter):
		""" Find the first (or only) object of this type that match a query.

		Parameters:
			- **filter**: filter for the object to select; see :doc:`queries`.

		Return:
			An object, or None if no object found.

		.. seealso::
			:meth:`~objects.CommittableObject.find`
		"""
		return backend.find(cls.__name__, query = filter, find_one = True)

	def _connect_to (self, target, relationship):
		""" Connect this object to another through a directed,
			annotated relationship (from this object to the target).

		.. note::
			- This method should not be called directly.
			- The target MUST have been committed at least once. However, the
			  source (i.e., the present object) can exist in memory only.
			- Throw a :class:`~errors.UncommittedObjectError` exception if the
			  target has never been committed.
		"""
		if (not "_id" in target._properties):
			raise errors.UncommittedObjectError("Cannot connect %s to %s: target has never been committed." % target)

		if (self == target):
			raise errors.MetagenomeDBError("Cannot connect %s to itself" % self)

		target_id = str(target._properties["_id"])

		if (relationship == None):
			relationship = {}
		else:
			relationship = parse_properties(relationship)

		# case where this object has no connection with the target yet
		if (not target_id in self._properties["_relationships"]):
			assert (not target_id in self._properties["_relationship_with"]) ###

			self._properties["_relationship_with"].append(target_id)
			self._properties["_relationships"][target_id] = [relationship]
			self._committed = False

			logger.debug("Initial relationship %s created between %s and %s." % (relationship, self, target))

		# case where this object has a connection with the target
		else:
			assert (target_id in self._properties["_relationship_with"]) ###

			if (relationship in self._properties["_relationships"][target_id]):
				logger.warning("A relationship %s already exists between objects %s and %s, and has been ignored." % (relationship, self, target))
				return

			self._properties["_relationships"][target_id].append(relationship)
			self._committed = False

			logger.debug("Relationship %s created between %s and %s." % (relationship, self, target))

	def _disconnect_from (self, target, relationship_filter):
		""" Disconnect this object from another.

		.. note::
			- This method should not be called directly.
			- The target MUST have been committed at least once. However, the
			  source (i.e., the present object) can exist in memory only.
			- Throw a :class:`~errors.UncommittedObjectError` exception if the
			  target has never been committed, or if attempting to use
			  **relationship_filter** while the source is not committed.
			- Throw a :class:`~errors.MetagenomeDBError` if the source is not
			  connected to the target.
		"""
		if (not "_id" in target._properties):
			raise errors.UncommittedObjectError("Cannot disconnect %s from %s: target has never been committed." % target)

		target_id = str(target._properties["_id"])

		if (not target_id in self._properties["_relationships"]):
			raise errors.MetagenomeDBError("%s is not connected to %s." % (self, target))

		# case 1: we remove all relationships between the object and target
		if (relationship_filter == None):
			del self._properties["_relationships"][target_id]
			self._properties["_relationship_with"].remove(target_id)
			self._committed = False

			logger.debug("Removed all relationships between %s and %s." % (self, target))

		# case 2: we remove all relationships matching a criteria
		else:
			if (not self._committed):
				raise errors.UncommittedObjectError("Cannot disconnect %s from %s: the source is not committed." % (self, target))

			n_relationships = len(self._properties["_relationships"][target_id])
			clazz = self.__class__.__name__
			to_remove = []

			for n in range(n_relationships):
				query = tree.traverse(
					parse_properties(relationship_filter),
					selector = lambda x: not x.startswith('$'),
					key_modifier = lambda x: "_relationships.%s.%s.%s" % (target_id, n, x)
				)

				query["_id"] = self._properties["_id"]

				if (backend.find(clazz, query, count = True) == 0):
					continue

				to_remove.append(n)

			if (len(to_remove) == 0):
				raise errors.MetagenomeDBError("%s is not connected to %s by any relationship matching %s." % (self, target, relationship_filter))

			for n in sorted(to_remove, reverse = True):
				logger.debug("Removed relationship %s between %s and %s." % (self._properties["_relationships"][target_id][n], self, target))

				del self._properties["_relationships"][target_id][n]

			if (len(to_remove) == n_relationships):
				del self._properties["_relationships"][target_id]
				self._properties["_relationship_with"].remove(target_id)

			self._committed = False

	def _in_vertices (self, neighbor_collection, neighbor_filter = None, relationship_filter = None, count = False):
		""" List (or count) all incoming relationships between objects and this object.
		
		.. note::
			This method should not be called directly.
		"""
		# if the present object has never been committed,
		# no object can possibly be linked to it.
		if (not "_id" in self._properties):
			logger.debug("Attempt to list in-neighbors of %s while this object has never been committed." % self)
			if (count):
				return 0
			else:
				return []

		object_id = str(self._properties["_id"])

		query = {"_relationship_with": object_id}

		if (relationship_filter != None):
			query["_relationships.%s" % object_id] = {"$elemMatch": parse_properties(relationship_filter)}

		if (neighbor_filter != None):
			neighbor_filter = parse_properties(neighbor_filter)
			for key in neighbor_filter:
				query[key] = neighbor_filter[key]

		return backend.find(neighbor_collection, query, count = count)

	def _out_vertices (self, neighbor_collection, neighbor_filter = None, relationship_filter = None, count = False):
		""" List (or count) all outgoing relationships between this object and others.
		
		.. note::
			- This method should not be called directly.
			- If relationship_filter is not None, a query is performed in the
			  database; hence, the source object must be committed. If not a
			  :class:`~errors.UncommittedObjectError` exception is thrown.
		"""
		targets = self._properties["_relationship_with"]

		if (len(targets) == 0):
			if (count):
				return 0
			else:
				return []

		# consider neighbors regardless of their relationship
		if (relationship_filter == None):
			candidates = targets

		# consider neighbors matching relationship_filter
		else:
			if (not self._committed):
				raise errors.UncommittedObjectError("Cannot list relationships from %s to other objects: the source is not committed." % self)

			candidates = []
			for target_id in targets:
				query = tree.traverse(
					parse_properties(relationship_filter),
					selector = lambda x: not x.startswith('$'),
					key_modifier = lambda x: "_relationships.%s.%s" % (target_id, x)
				)

				query["_id"] = self._properties["_id"]

				if (backend.find(self.__class__.__name__, query, count = True) == 0):
					continue

				candidates.append(target_id)

		if (len(candidates) == 0):
			if (count):
				return 0
			else:
				return []

		# select candidates matching neighbor_filter
		query = {"_id": {"$in": [bson.objectid.ObjectId(id) for id in candidates]}}

		if (neighbor_filter != None):
			neighbor_filter = parse_properties(neighbor_filter)
			for key in neighbor_filter:
				query[key] = neighbor_filter[key]

		return backend.find(neighbor_collection, query, count = count)

	def has_relationships_with (self, target):
		""" Test if this object has relationship(s) with another object.
		
		Parameters:
			- **target**: object to test for the existence of relationships with.

		.. seealso::
			:meth:`~objects.CommittableObject.list_relationships_with`
		"""
		if (not "_id" in target._properties):
			logger.debug("Attempt to test a relationship between %s and %s while the later has never been committed." % (self, target))
			return False

		return (str(target._properties["_id"]) in self._properties["_relationships"])

	def list_relationships_with (self, target):
		""" List relationship(s), if any, from this object to others.

		Parameters:
			- **target**: object to list relationships with.

		Return:
			A list.

		.. seealso::
			:meth:`~objects.CommittableObject.has_relationships_with`
		"""
		if (not "_id" in target._properties):
			logger.debug("Attempt to list relationships between %s and %s while the later has never been committed." % (self, target))
			return []

		target_id = str(target._properties["_id"])

		if (target_id in self._properties["_relationships"]):
			return copy.deepcopy(self._properties["_relationships"][target_id])
		else:
			return []

	def remove (self):
		""" Remove this object from the database.

		.. note::
			- Relationships from and to this object are removed as well.
			- The object remains in memory, flagged as uncommitted.

		.. seealso::
			:meth:`~objects.CommittableObject.remove_all`
		"""
		# remove all relationships with other objects
		for collection_name in backend.list_collections():
			if ("_id" in self._properties):
				for object in self._in_vertices(collection_name):
					object._disconnect_from(self, None)

			for object in self._out_vertices(collection_name):
				self._disconnect_from(object, None)

		# if the object has been committed at least once,
		if ("_id" in self._properties):
			# remove the object from the database
			backend.remove_object(self)

			# and declare it has never having been committed
			del self._properties["_id"]

		self._committed = False

	@classmethod
	def remove_all (cls):
		""" Remove all objects of this type from the database.

		.. note::
			- Relationships from and to these objects are removed as well.
			- Instanciated objects remain in memory, flagged as uncommitted.

		.. seealso::
			:meth:`~objects.CommittableObject.remove`
		"""
		collection_name = cls.__name__

		n_objects = backend.find(collection_name, None, count = True)
		objects = backend.find(collection_name, None)

		n = 0
		for object in objects:
			try:
				object.remove()
				n += 1
			except:
				continue

		if (n < n_objects):
			logger.warning("%s out of %s objects in collection '%s' were not removed." % (n_objects - n, n_objects, collection_name))
			return

		backend.drop_collection(cls.__name__)

	def __del__ (self):
		if (hasattr(self, "_committed") and (not self._committed)):
			logger.warning("Object %s has been destroyed without having been committed." % self)

	def __repr__ (self):
		return self.__str__()

class Direction:
	INGOING, SUB = 1, 1
	OUTGOING, SUPER = 2, 2
	BOTH = 0

	@classmethod
	def _validate (cls, value):
		value_t = type(value)

		if (value_t == int):
			if (value < 0) or (value > 2):
				raise errors.MetagenomeDBError("Invalid direction parameter '%s'" % value)
			return value

		if (value_t == str):
			try:
				return {
					"ingoing": 1,
					"outgoing": 2,
					"both": 0
				}[value.lower().strip()]
			except:
				raise errors.MetagenomeDBError("Invalid direction parameter '%s'" % value)

		raise errors.MetagenomeDBError("Invalid direction parameter '%s'" % value)

	@classmethod
	def _has_ingoing (cls, value):
		value = Direction._validate(value)
		return (value == Direction.INGOING) or (value == Direction.BOTH)

	@classmethod
	def _has_outgoing (cls, value):
		value = Direction._validate(value)
		return (value == Direction.OUTGOING) or (value == Direction.BOTH)

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Sequence object.
class Sequence (CommittableObject):

	def __init__ (self, properties):
		""" Create a new Sequence object.
		
		Parameters:
			- **properties**: properties of this sequence, as a dictionary.
			  Must contain at least a 'name' and 'sequence' property, or a
			  :class:`~errors.InvalidObjectError` exception is thrown. A
			  'length' property is automatically calculated and would overwrite
			  any such property if provided.

		.. note::
			The 'name' property is unique within a collection, but not across
			the whole database. It means that two sequences with the same name
			can coexist in the database as long as they belong to two different
			collections (or if they are not related to any collection).
		"""
		if (not "name" in properties):
			raise errors.InvalidObjectError("Property 'name' is missing")

		if (not "sequence" in properties):
			raise errors.InvalidObjectError("Property 'sequence' is missing")
	
		# TODO: Check the sequence
		# TODO: Check the sequence length; if too big (what is the limit?)
		#       we should store it using gridfs

		properties["length"] = len(properties["sequence"])

		indices = {
			"name": False,
			"length": False,
			"class": False,
		}

		CommittableObject.__init__(self, indices, properties)

	def add_to_collection (self, collection, relationship = None):
		""" Add this sequence to a collection.

		Parameters:
			- **collection**: collection to add this sequence to.
			- **relationship**: properties of the relationship linking this
			  sequence to **collection**, as a dictionary (optional). See
			  :doc:`annotations`.

		.. note::
			- If the collection already contains a sequence with the same name
			  a :class:`~errors.DuplicateObjectError` exception is thrown.
			- If the collection has never been committed to the database a
			  :class:`~errors.UncommittedObjectError` is thrown.
			- This sequence will need to be committed to the database for the
			  information about its relationship to **collection** to be stored
			  and queried. See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Sequence.remove_from_collection`
		"""
		if (not isinstance(collection, Collection)):
			raise errors.MetagenomeDBError("The 'collection' parameter must be a Collection object.")

		if (collection.count_sequences({"name": self["name"]}) > 0):
			raise errors.DuplicateObjectError(
				self.__class__.__name__,
				(("name", self["name"]),),
				"A sequence with name '%s' already exists in collection '%s'." % (self["name"], collection["name"])
			)

		self._connect_to(collection, relationship)

	def remove_from_collection (self, collection, relationship_filter = None):
		""" Remove this sequence from a collection.
		
		Parameters:
			- **collection**: collection to remove this collection from.
			- **relationship_filter**: relationships to remove (optional).
			  If none provided, all relationships linking this sequence to
			  **collection** are removed. See :doc:`queries`.

		.. note::
			- If this sequence and **collection** have no relationship, a
			  :class:`~errors.MetagenomeDBError` exception is thrown. 
			- If this sequence is not committed and **relationship_filter** is
			  set a :class:`~errors.UncommittedObjectError` exception is thrown.
			  See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Sequence.add_to_collection`
		"""
		if (not isinstance(collection, Collection)):
			raise errors.MetagenomeDBError("The 'collection' parameter must be a Collection object.")

		self._disconnect_from(collection, relationship_filter)

	def list_collections (self, collection_filter = None, relationship_filter = None):
		""" List collections this sequence is linked to.
		
		Parameters:
			- **collection_filter**: filter for the collections (optional). See
			  :doc:`queries`.
			- **relationship_filter**: filter for the relationship linking this
			  sequence to collections (optional). See :doc:`queries`.
		
		.. note::
			- If this sequence is not committed and **relationship_filter** is
			  set a :class:`~errors.UncommittedObjectError` exception is thrown.
			  See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Sequence.count_collections`
		"""
		return self._out_vertices("Collection", collection_filter, relationship_filter)

	def count_collections (self, collection_filter = None, relationship_filter = None):
		""" Count collections this sequence is linked to.
		
		Parameters:
			- **collection_filter**: filter for the collections (optional). See :doc:`queries`.
			- **relationship_filter**: filter for the relationship linking this
			  sequence to collections (optional). See :doc:`queries`.
		
		.. note::
			- If this sequence is not committed and **relationship_filter** is
			  set a :class:`~errors.UncommittedObjectError` exception is thrown.
			  See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Sequence.list_collections`
		"""
		return self._out_vertices("Collection", collection_filter, relationship_filter, True)

	def relate_to_sequence (self, sequence, relationship = None):
		""" Link this sequence to another sequence.
		
		Parameters:
			- **sequence**: sequence to link this sequence to.
			- **relationship**: description of the relationship linking this
			  sequence to **sequence**, as a dictionary (optional).
		
		.. note::
			- If **sequence** has never been committed to the database a
			  :class:`~errors.UncommittedObjectError` is thrown.
			- This sequence will need to be committed to the database for the
			  information about its relationship to **sequence** to be stored
			  and queried. See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Sequence.dissociate_from_sequence`
		"""
		if (not isinstance(sequence, Sequence)):
			raise errors.MetagenomeDBError("The 'sequence' parameter must be a Sequence object.")

		self._connect_to(sequence, relationship)

	def dissociate_from_sequence (self, sequence, relationship_filter = None):
		""" Remove links between this sequence and another sequence.

		Parameters:
			- **sequence**: sequence to unlink this sequence from.
			- **relationship_filter**: relationships to remove (optional).
			  If none provided, all relationships from this sequence
			  to **sequence** are removed. See :doc:`queries`.

		.. note::
			- If this sequence and **sequence** have no relationship, a
			  :class:`~errors.MetagenomeDBError` exception is thrown. 
			- If this sequence is not committed and **relationship_filter** is
			  set a :class:`~errors.UncommittedObjectError` exception is thrown.
			  See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Sequence.relate_to_sequence`
		"""
		if (not isinstance(sequence, Sequence)):
			raise errors.MetagenomeDBError("The 'sequence' parameter must be a Sequence object.")

		self._disconnect_from(sequence, relationship_filter)

	def list_related_sequences (self, direction = Direction.BOTH, sequence_filter = None, relationship_filter = None):
		""" List sequences this sequence is related to.
		
		Parameters:
			- **direction**: direction of the relationship (optional). If set to
			  ``Direction.INGOING``, will list sequences that are linked to the
			  present sequence. If set to ``Direction.OUTGOING``, will list
			  sequences this sequence is linked to. If set to ``Direction.BOTH``
			  (default), both neighboring sequences are listed. See
			  :doc:`relationships`.
			- **sequence_filter**: filter for the sequences to list (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationship between this
			  sequence and neighboring sequences (optional). See :doc:`queries`.

		.. note::
			- If **direction** is set to ``Direction.BOTH`` or ``Direction.OUTGOING``,
			  **relationship_filter** is set and this sequence is not committed,
			  a :class:`~errors.UncommittedObjectError` exception is thrown.

		.. seealso::
			:meth:`~objects.Sequence.count_related_sequences`
		"""
		related_sequences = []

		if Direction._has_ingoing(direction):
			related_sequences.append(self._in_vertices("Sequence", sequence_filter, relationship_filter))

		if Direction._has_outgoing(direction):
			related_sequences.append(self._out_vertices("Sequence", sequence_filter, relationship_filter))

		return itertools.chain(*related_sequences)

	def count_related_sequences (self, direction = Direction.BOTH, sequence_filter = None, relationship_filter = None):
		""" Count sequences this sequence is related to.
		
		Parameters:
			- **direction**: direction of the relationship (optional). If set to
			  ``Direction.INGOING``, will count sequences that are linked to 
			  this sequence. If set to ``Direction.OUTGOING``, will count
			  sequences this sequence is linked to. If set to ``Direction.BOTH``
			  (default), all neighboring sequences are counted. See
			  :doc:`relationships`
			- **sequence_filter**: filter for the sequences to count (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationship between this
			  sequence and neighboring sequences (optional). See :doc:`queries`.

		.. note::
			- If **direction** is set to ``Direction.BOTH`` or ``Direction.OUTGOING``,
			  **relationship_filter** is set and this sequence is not committed,
			  a :class:`~errors.UncommittedObjectError` exception is thrown.

		.. seealso::
			:meth:`~objects.Sequence.list_related_sequences`
		"""
		related_sequences_c = 0

		if Direction._has_ingoing(direction):
			related_sequences_c += self._in_vertices("Sequence", sequence_filter, relationship_filter, count = True)

		if Direction._has_outgoing(direction):
			related_sequences_c += self._out_vertices("Sequence", sequence_filter, relationship_filter, count = True)

		return related_sequences_c

	def __str__ (self):
		return "<Sequence id:%s name:'%s' length:%s state:'%s'>" % (
			self.get_property("_id", "none"),
			self["name"],
			self["length"],
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

# Collection of Sequence objects.
class Collection (CommittableObject):

	def __init__ (self, properties):
		""" Create a new Collection object.
		
		Parameters:
			- **properties**: properties of this sequence, as a dictionary.
			  Must contain at least a 'name' property, or a
			  :class:`~errors.InvalidObjectError` exception is thrown.

		.. note::
			  Collection names are unique in the database; if attempting to
			  commit a collection while another collection already exists with
			  the same name a :class:`~errors.DuplicateObjectError` exception
			  is thrown.
		"""
		if (not "name" in properties):
			raise errors.InvalidObjectError("Property 'name' is missing")

		indices = {
			"name": True,
			"class": False,
		}

		CommittableObject.__init__(self, indices, properties)

	def list_sequences (self, sequence_filter = None, relationship_filter = None):
		""" List sequences this collection contains.
		
		Parameters:
			- **sequence_filter**: filter for the sequences to list (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationship linking
			  sequences to this collection (optional). See :doc:`queries`.

		.. seealso::
			:meth:`~objects.Collection.count_sequences`
		"""
		return self._in_vertices("Sequence", sequence_filter, relationship_filter)

	def count_sequences (self, sequence_filter = None, relationship_filter = None):
		""" Count sequences this collection contains.
		
		Parameters:
			- **sequence_filter**: filter for the sequences to count (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationship linking
			  sequences to this collection (optional). See :doc:`queries`.

		.. seealso::
			:meth:`~objects.Collection.list_sequences`
		"""
		return self._in_vertices("Sequence", sequence_filter, relationship_filter, True)

	def add_to_collection (self, collection, relationship = None):
		""" Add this collection to a (super) collection.
		
		Parameters:
			- **collection**: collection to add this collection to.
			- **relationship**: properties of the relationship from this
			  collection to **collection**, as a dictionary (optional). See
			  :doc:`annotations`.

		.. note::
			- If **collection** has never been committed to the database a
			  :class:`~errors.UncommittedObjectError` is thrown.
			- This collection will need to be committed to the database for the
			  information about its relationship to **collection** to be stored
			  and queried. See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Collection.remove_from_collection`
		"""
		if (not isinstance(collection, Collection)):
			raise errors.MetagenomeDBError("The 'collection' parameter must be a Collection object.")

		self._connect_to(collection, relationship)

	def remove_from_collection (self, collection, relationship_filter = None):
		""" Remove this collection from another (super) collection.
		
		Parameters:
			- **collection**: collection to remove this collection from.
			- **relationship_filter**: relationships to remove (optional).
			  If none provided, all relationships linking this collection
			  to **collection** are removed. See :doc:`queries`.

		.. note::
			- If this collection and **collection** have no relationship, a
			  :class:`~errors.MetagenomeDBError` exception is thrown. 
			- If this collection is not committed and **relationship_filter** is
			  set a :class:`~errors.UncommittedObjectError` exception is thrown.
			  See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Collection.add_to_collection`
		"""
		if (not isinstance(collection, Collection)):
			raise errors.MetagenomeDBError("The 'collection' parameter must be a Collection object.")

		self._disconnect_from(collection, relationship_filter)

	def list_super_collections (self, collection_filter = None, relationship_filter = None):
		""" List all collections this collection is linked to.

		Parameters:
			- **collection_filter**: filter for the super-collections (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationships linking this
			  collection to super-collections (optional). See :doc:`queries`.

		.. note::
			- If this collection is not committed and **relationship_filter** is
			  set a :class:`~errors.UncommittedObjectError` exception is thrown.
			  See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Collection.count_super_collections`,
			:meth:`~objects.Collection.list_sub_collections`,
			:meth:`~objects.Collection.count_sub_collections`
		"""
		return self.list_related_collections(Direction.OUTGOING, collection_filter, relationship_filter)

	def count_super_collections (self, collection_filter = None, relationship_filter = None):
		""" Count all collections this collection is linked to.

		Parameters:
			- **collection_filter**: filter for the super-collections (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationships linking this
			  collection to super-collections (optional). See :doc:`queries`.

		.. note::
			- If this collection is not committed and **relationship_filter** is
			  set a :class:`~errors.UncommittedObjectError` exception is thrown.
			  See :doc:`relationships`.

		.. seealso::
			:meth:`~objects.Collection.list_super_collections`,
			:meth:`~objects.Collection.list_sub_collections`,
			:meth:`~objects.Collection.count_sub_collections`
		"""
		return self.count_related_collections(Direction.OUTGOING, collection_filter, relationship_filter)

	def list_sub_collections (self, collection_filter = None, relationship_filter = None):
		""" List all collections that are linked to this collection.

		Parameters:
			- **collection_filter**: filter for the sub-collections (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationships linking
			  sub-collections to this collection (optional). See :doc:`queries`.

		.. seealso::
			:meth:`~objects.Collection.count_sub_collections`,
			:meth:`~objects.Collection.list_super_collections`,
			:meth:`~objects.Collection.count_super_collections`
		"""
		return self.list_related_collections(Direction.INGOING, collection_filter, relationship_filter)

	def count_sub_collections (self, collection_filter = None, relationship_filter = None):
		""" Count all collections that are linked to this collection.

		Parameters:
			- **collection_filter**: filter for the sub-collections (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationships linking
			  sub-collections to this collection (optional). See :doc:`queries`.

		.. seealso::
			:meth:`~objects.Collection.list_sub_collections`,
			:meth:`~objects.Collection.list_super_collections`,
			:meth:`~objects.Collection.count_super_collections`
		"""
		return self.count_related_collections(Direction.INGOING, collection_filter, relationship_filter)

	def list_related_collections (self, direction = Direction.BOTH, collection_filter = None, relationship_filter = None):
		""" List all collections this collection is linked to, or have links to it.

		Parameters:
			- `direction`: direction of the relationship (optional). If set to
			  ``Direction.INGOING``, will list collections that are linked to
			  this collection (i.e., sub-collections). If set to
			  ``Direction.OUTGOING``, will list collections this collection is
			  linked to (i.e., super-collections). If set to ``Direction.BOTH``
			  (default), all neighboring collections are listed. See
			  :doc:`relationships`.
			- `collection_filter`: filter for the collections to list (optional).
			  See :doc:`queries`.
			- `relationship_filter`: filter for the relationships between this
			  collection and neighbor collections (optional). See :doc:`queries`.

		.. note::
			- If **direction** is set to ``Direction.BOTH`` or ``Direction.OUTGOING``,
			  **relationship_filter** is set and this collection is not committed,
			  a :class:`~errors.UncommittedObjectError` exception is thrown.

		.. seealso::
			:meth:`~objects.Collection.count_related_collections`
		"""
		collections = []

		if Direction._has_ingoing(direction):
			collections.append(self._in_vertices("Collection", collection_filter, relationship_filter))

		if Direction._has_outgoing(direction):
			collections.append(self._out_vertices("Collection", collection_filter, relationship_filter))

		return itertools.chain(*collections)

	def count_related_collections (self, direction = Direction.BOTH, collection_filter = None, relationship_filter = None):
		""" Count all collections this collection is linked to, or have links to it.

		Parameters:
			- `direction`: direction of the relationship (optional). If set to
			  ``Direction.INGOING``, will count collections that are linked to
			  this collection (i.e., sub-collections). If set to
			  ``Direction.OUTGOING``, will count collections this collection is
			  linked to (i.e., super-collections). If set to ``Direction.BOTH``
			  (default), all neighboring collections are counted. See
			  :doc:`relationships`.
			- `collection_filter`: filter for the collections to count (optional).
			  See :doc:`queries`.
			- `relationship_filter`: filter for the relationships between this
			  collection and neighbor collections (optional). See :doc:`queries`.

		.. note::
			- If **direction** is set to ``Direction.BOTH`` or ``Direction.OUTGOING``,
			  **relationship_filter** is set and this collection is not committed,
			  a :class:`~errors.UncommittedObjectError` exception is thrown.

		.. seealso::
			:meth:`~objects.Collection.list_related_collections`
		"""
		collections_c = 0

		if Direction._has_ingoing(direction):
			collections_c += self._in_vertices("Collection", collection_filter, relationship_filter, count = True)

		if Direction._has_outgoing(direction):
			collections_c += self._out_vertices("Collection", collection_filter, relationship_filter, count = True)

		return collections_c

	def __str__ (self):
		return "<Collection id:%s name:'%s' state:'%s'>" % (
			self.get_property("_id", "none"),
			self["name"],
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

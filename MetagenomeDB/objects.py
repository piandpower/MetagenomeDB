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

		:Parameters:
		  - `properties` (optional): object annotations, as a dictionary. Nested
			properties can be expressed using dot notation or by nested dictionaries.
		"""
		self._properties = parse_properties(properties)
		self._modified = False

	def get_properties (self):
		""" Return a copy of all of this object's properties, as a dictionary.
		"""
		return self._properties.copy()

	def get_property (self, key, default = None):
		""" Return the value for a given property.

		:Parameters:
		  - `key`: property to retrieve. Nested properties can be queried using
			a dot notation.

			Examples:
				object.get_property("a") -- will retrieve value for property 'a'
				object.get_property("a.b") -- will retrieve value for sub-property 'b' of property 'a' of the object

		  - `default` (optional): default value to return if the property is
			not set.

		:Note:
			Traditional dictionary-like notation can be used to retrieve
			a property. E.g., print object["property"]. The difference with
			get_property() is that the later allows for the case the property
			has not been set, while the former will throw an exception.

			Examples:
				object["a.b"] -- similar to get_property("a.b"), but requires property 'a.b' to exists
				object["a"]["b"] -- alternative syntax
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

		:Parameters:
		  - `properties` (optional): object annotations, as a dictionary. Nested
			properties can be expressed using dot notation or by nested dictionaries.
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
				raise ValueError("Unknown identifier '%s'" % id)

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
			raise ValueError("Property '%s' is reserved and cannot be modified." % key)

		MutableObject.__setitem__(self, key, value)
		self._committed = not self._modified

	def __delitem__ (self, key, value):
		key_ = tree.validate_key(key)

		if (key_[0].startswith('_')):
			raise ValueError("Property '%s' is reserved and cannot be modified." % key)

		MutableObject.__delitem__(self, key, value)
		self._committed = False

	def commit (self):
		""" Commit this object to the database.

		:Note:
			The commit will not be performed if the object has already been
			committed once and no modification (property manipulation) has
			been performed since then.
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
		"""
		return self._committed

	@classmethod
	def count (cls, filter):
		""" Count the number of objects of this type in the database.
		
		:Parameters:
		  - `filter` (optional): filter objects based on a dictionary.
		"""
		return backend.count(cls.__name__, query = filter)

	@classmethod
	def distinct (cls, property):
		""" Count the number of objects for each value of the given property.

		:Properties:
		  - `property`: property to count objects for.

		:Return:
			A dictionary with all values found for this property as keys, and
			number of objects having this value as values.
		"""
		return backend.distinct(cls.__name__, property)

	@classmethod
	def find (cls, filter):
		""" Find all objects of this type that match a query.
		
		:Properties:
		  - `filter`: set of properties and values objects of this type must
			possess to be selected, as a dictionary. Nested properties can be
			expressed using dot notation or by nested dictionaries.
			
			Examples:
				find({"name": "foo"}) -- will select all objects with value 'foo' for property 'name'
				find({"a": 1, "b": 2}) -- will select all objects with value 1 for property 'a' and value 2 for property 'b'
				find({"a.b": 3}) -- will select all objects with value 3 for sub-property 'b' of property a
				find({"a": {"b": 3}}) -- alternative syntax for the prior example
				find({}) -- select all objects of this type

		:Note:
			The `filter` property can incorporate operators and modifiers from
			MongoDB (see `MongoDB documentation
			<http://www.mongodb.org/display/DOCS/Advanced+Queries>`_); e.g.,
			
				find({"a": {"$gte": 3}}) -- will select all objects with value 3 or greater for property 'a'
				find({"a": {"$exists": True}}) -- will select all objects with property 'a'

		:Return:
			A generator.
		"""
		return backend.find(cls.__name__, query = filter)

	@classmethod
	def find_one (cls, filter):
		""" Find the first (or only) object of this type that match a query.

		:Properties:
		  - `filter`: see find()

		:Return:
			An object, or None if no object found.
		"""
		return backend.find(cls.__name__, query = filter, find_one = True)

	def _connect_to (self, target, relationship):
		""" Connect this object to another through a directed,
			annotated relationship (from this object to the target).

		:Note:
			This method should not be called directly.
		"""
		if (not "_id" in target._properties):
			raise Exception("Unable to connect %s to %s: the target has never been committed." % (self, target))

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

		# case where this object has a connection with the target
		else:
			assert (target_id in self._properties["_relationship_with"]) ###

			if (relationship in self._properties["_relationships"][target_id]):
				logger.warning("A relationship %s already exists between objects %s and %s, and has been ignored." % (relationship, self, target))
				return

			self._properties["_relationships"][target_id].append(relationship)
			self._committed = False

			logger.debug("Added relationship %s between %s and %s." % (relationship, self, target))

	def _disconnect_from (self, target, relationship_filter):
		""" Disconnect this object from another.

		:Note:
			This method should not be called directly.
		"""
		if (not "_id" in target._properties):
			raise Exception("Object %s is not connected to %s, as the later never has been committed." % (self, target))
			return

		target_id = str(target._properties["_id"])

		if (not target_id in self._properties["_relationships"]):
			raise Exception("Object %s is not connected to %s." % (self, target))

		# case 1: we remove all relationships between the object and target
		if (relationship_filter == None):
			del self._properties["_relationships"][target_id]
			self._properties["_relationship_with"].remove(target_id)
			self._committed = False

			logger.debug("Removed all relationships between %s and %s." % (self, target))

		# case 2: we remove all relationships matching a criteria
		else:
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
				raise Exception("Relationship %s not found between %s and %s." % (relationship_filter, self, target))

			for n in sorted(to_remove, reverse = True):
				logger.debug("Removed relationship %s between %s and %s." % (self._properties["_relationships"][target_id][n], self, target))

				del self._properties["_relationships"][target_id][n]

			if (len(to_remove) == n_relationships):
				del self._properties["_relationships"][target_id]
				self._properties["_relationship_with"].remove(target_id)

			self._committed = False

	def _in_vertices (self, neighbor_collection, neighbor_filter = None, relationship_filter = None, count = False):
		""" List (or count) all incoming relationships between objects and this object.
		
		:Note:
			This method should not be called directly.
		"""
		if (not "_id" in self._properties):
			logger.warning("Attempt to list neighbors of %s while this object has never been committed." % self)
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
		
		:Note:
			This method should not be called directly.
		"""
		if (not "_id" in self._properties):
			logger.warning("Attempt to list neighbors of %s while this object has never been committed." % self)
			if (count):
				return 0
			else:
				return []

		object_id = str(self._properties["_id"])
		clazz = self.__class__.__name__
		targets = self._properties["_relationship_with"]

		if (len(targets) == 0):
			if (count):
				return 0
			else:
				return []

		# select candidate neighbors using relationship_filter
		if (relationship_filter != None):
			candidates = []
			for target_id in targets:
				query = tree.traverse(
					parse_properties(relationship_filter),
					selector = lambda x: not x.startswith('$'),
					key_modifier = lambda x: "_relationships.%s.%s" % (target_id, x)
				)

				query["_id"] = self._properties["_id"]

				if (backend.find(clazz, query, count = True) == 0):
					continue

				candidates.append(target_id)
		else:
			candidates = targets

		if (len(candidates) == 0):
			if (count):
				return 0
			else:
				return []

		# then select among candidates using neighbor_filter
		query = {"_id": {"$in": [bson.objectid.ObjectId(id) for id in candidates]}}

		if (neighbor_filter != None):
			neighbor_filter = parse_properties(neighbor_filter)
			for key in neighbor_filter:
				query[key] = neighbor_filter[key]

		return backend.find(neighbor_collection, query, count = count)

	def has_relationships_with (self, target):
		""" Test if this object has a relationship with another object.
		
		:Parameters:
		  - `target`: object to test for the existence of relationships with.
		"""
		if (not "_id" in target._properties):
			logger.debug("Attempt to test a relationship between %s and %s while the later has never been committed." % (self, target))
			return False

		return (str(target._properties["_id"]) in self._properties["_relationships"])

	def list_relationships_with (self, target):
		""" List relationships (if any) between this object and others.

		:Parameters:
		  - `target`: object to list relationships with.

		:Return:
			A list.
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

		:Note:
			Relationships between this object and others are removed as well.

			The object remains in memory, flagged as uncommitted.

			Will throw an exception if called while the object has never been
			committed.
		"""

		if (not self._committed):
			raise errors.UncommittedObject(self)

		# Remove all relationships with other objects
		for collection_name in backend.list_collections():
			for object in self._in_vertices(collection_name):
				object._disconnect_from(self, None)

			for object in self._out_vertices(collection_name):
				self._disconnect_from(object, None)

		backend.remove_object(self)

		del self._properties["_id"]
		self._committed = False

	@classmethod
	def remove_all (cls):
		""" Remove all objects of this type from the database.

		:Note:
			Relationships between these objects and others are removed as well.

			Instanciated objects remain in memory, flagged as uncommitted.
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
		""" Clean-up code when the object is garbage collected.
		"""
		# if the object is destroyed due to an exception thrown during
		# its instantiation, self._committed will not exists.
		if (not hasattr(self, "_committed")):
			return

		if (not self._committed):
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
				raise ValueError("Invalid direction '%s'" % value)
			return value

		if (value_t == str):
			try:
				return {
					"ingoing": 1,
					"outgoing": 2,
					"both": 0
				}[value.lower().strip()]
			except:
				raise ValueError("Invalid direction '%s'" % value)

		raise ValueError("Invalid direction '%s'" % value)

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
		if (not "name" in properties):
			raise errors.MalformedObject("Property 'name' is missing")

		if (not "sequence" in properties):
			raise errors.MalformedObject("Property 'sequence' is missing")
	
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

	# Add this sequence to an existing collection
	#	collection -- Collection to add this sequence to
	#	relationship -- Properties of the relationship between
	#		this sequence and the collection
	def add_to_collection (self, collection, relationship = None):
		if (not isinstance(collection, Collection)):
			raise ValueError("The 'collection' parameter must be a Collection object.")

		self._connect_to(collection, relationship)

	# Remove this sequence from an existing collection
	#	collection -- Collection to remove this sequence from
	#	relationship_filter -- If set, remove only those relationships that
	#		 match the filter. If not set, all relationships will be removed
	def remove_from_collection (self, collection, relationship_filter = None):
		if (not isinstance(collection, Collection)):
			raise ValueError("The 'collection' parameter must be a Collection object.")

		self._disconnect_from(collection, relationship_filter)

	# List all collections this sequence is part of
	#	collection_filter -- Filter for the collection (optional)
	#	relationship_filter -- Filter for the relationship between this
	#		sequence and any collection (optional)
	def list_collections (self, collection_filter = None, relationship_filter = None):
		return self._out_vertices("Collection", collection_filter, relationship_filter)

	# Count all collections this sequence is part of
	#	collection_filter -- Filter for the collection (optional)
	#	relationship_filter -- Filter for the relationship between this
	#		sequence and any collection (optional)
	def count_collections (self, collection_filter = None, relationship_filter = None):
		return self._out_vertices("Collection", collection_filter, relationship_filter, True)

	def relate_to_sequence (self, sequence, relationship = None):
		if (not isinstance(sequence, Sequence)):
			raise ValueError("The 'sequence' parameter must be a Sequence object.")

		self._connect_to(sequence, relationship)

	def dissociate_from_sequence (self, sequence, relationship_filter = None):
		if (not isinstance(sequence, Sequence)):
			raise ValueError("The 'sequence' parameter must be a Sequence object.")

		self._disconnect_from(sequence, relationship_filter)

	def list_related_sequences (self, direction = Direction.BOTH, sequence_filter = None, relationship_filter = None):
		related_sequences = []

		if Direction._has_ingoing(direction):
			related_sequences.append(self._in_vertices("Sequence", sequence_filter, relationship_filter))

		if Direction._has_outgoing(direction):
			related_sequences.append(self._out_vertices("Sequence", sequence_filter, relationship_filter))

		return itertools.chain(*related_sequences)

	def count_related_sequences (self, direction = Direction.BOTH, sequence_filter = None, relationship_filter = None):
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
		if (not "name" in properties):
			raise errors.MalformedObject("Property 'name' is missing")

		indices = {
			"name": True,
			"class": False,
		}

		CommittableObject.__init__(self, indices, properties)

	def list_sequences (self, sequence_filter = None, relationship_filter = None):
		return self._in_vertices("Sequence", sequence_filter, relationship_filter)

	def count_sequences (self, sequence_filter = None, relationship_filter = None):
		return self._in_vertices("Sequence", sequence_filter, relationship_filter, True)

	def add_to_collection (self, collection, relationship = None):
		if (not isinstance(collection, Collection)):
			raise ValueError("The 'collection' parameter must be a Collection object.")

		self._connect_to(collection, relationship)

	def remove_from_collection (self, collection, relationship_filter = None):
		if (not isinstance(collection, Collection)):
			raise ValueError("The 'collection' parameter must be a Collection object.")

		self._disconnect_from(collection, relationship_filter)

	def list_sub_collections (self, collection_filter = None, relationship_filter = None):
		return self.list_related_collections(Direction.INGOING, collection_filter, relationship_filter)

	def list_super_collections (self, collection_filter = None, relationship_filter = None):
		return self.list_related_collections(Direction.OUTGOING, collection_filter, relationship_filter)

	def list_related_collections (self, direction = Direction.BOTH, collection_filter = None, relationship_filter = None):
		collections = []

		if Direction._has_ingoing(direction):
			collections.append(self._in_vertices("Collection", collection_filter, relationship_filter))

		if Direction._has_outgoing(direction):
			collections.append(self._out_vertices("Collection", collection_filter, relationship_filter))

		return itertools.chain(*collections)

	def count_sub_collections (self, collection_filter = None, relationship_filter = None):
		return self.count_related_collections(Direction.INGOING, collection_filter, relationship_filter)

	def count_super_collections (self, collection_filter = None, relationship_filter = None):
		return self.count_related_collections(Direction.OUTGOING, collection_filter, relationship_filter)

	def count_related_collections (self, direction = Direction.BOTH, collection_filter = None, relationship_filter = None):
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

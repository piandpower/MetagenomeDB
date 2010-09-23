# objects.py: object representation of the MongoDB content

import sys, datetime, itertools, copy, logging
import pymongo

import backend, errors
from utils import tree

logger = logging.getLogger("MetagenomeDB.objects")

# MutableObject: Base object that can receive arbitrary properties.
class MutableObject (object):

	# Create a new object.
	#	properties -- (dictionary) object annotations. Nested properties can
	#		be expressed using dot notation.
	def __init__ (self, **properties):
		self._properties = {}

		for key, value in properties.iteritems():
			key = tree.validate_key(key)
			tree.set(self._properties, key, value)

		self._modified = False

	# Return a copy of all of this object's properties, as a dictionary.
	def get_properties (self):
		return self._properties.copy()

	# Return the value for a given property.
	#	property -- property to retrieve. Nested properties can be queried
	#		using a dot notation.
	#	default -- default value to return if the property is not set.
	def get_property (self, key, default = None):
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

# CommittableObject: Object that can be committed to the backend database.
class CommittableObject (MutableObject):

	# Create a new object.
	#	properties -- (dictionary) object annotations. Nested properties can
	#		be expressed using dot notation.
	def __init__ (self, indices, **properties):
		MutableObject.__init__(self, **properties)

		# if the object is provided with an identifier,
		# we check if this identifier is present in the
		# object cache to know if it was committed.
		if ("_id" in self._properties):
			id = self._properties["_id"]

			if (type(id) == str):
				id = pymongo.objectid.ObjectId(id)
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

	# Commit this object to the database.
	#	patch -- (dictionary) transient properties patch; set of properties
	#		that will be added to the object prior commit. Those properties
	#		are removed (or restored, if overwritten) after commit.
	def commit (self, **patch):
		if (self._committed):
			return

		# If some patch needs to be applied on the object's
		# properties, we temporary store the old values
		tmp = {}
		for (key, value) in patch.iteritems():
			assert (key != "_id") ###
			tmp[key] = self._properties[key]
			self._properties[key] = value

		id = backend.commit(self)

		# We restore the object's properties, if needed
		for (key, value) in tmp.iteritems():
			self._properties[key] = value

		self._committed = True

	# Test if this object has been committed to the database.
	# Return a boolean.
	def is_committed (self):
		return self._committed

	# Count the number of object of this type in the database.
	#	filter -- (dictionary) optional filter.
	@classmethod
	def count (cls, **filter):
		return backend.count(cls.__name__, query = filter)

	# Count instances of this object having distinct values for a given property.
	#	property -- property to count objects for.
	# Return a dictionary with distinct values for this property as keys, and
	# number of objects having this value as value.
	@classmethod
	def distinct (cls, property):
		return backend.distinct(cls.__name__, property)

	# Find all instances of this object that match a query.
	#	filter -- (dictionary) query, or None if all objects are to be returned.
	# Return the objects selected, as a generator.
	@classmethod
	def find (cls, **filter):
		return backend.find(cls.__name__, query = filter)

	# Find the first (or only) instance of this object that match a query.
	#	filter -- (dictionary) query, or None if all objects are to be returned.
	@classmethod
	def find_one (cls, **filter):
		return backend.find(cls.__name__, query = filter, find_one = True)

	# Connect this object to another through a directed,
	# annotated relationship (from this object to the target)
	def _connect_to (self, target, relationship):
		if (not target._committed):
			raise Exception("Unable to connect %s to %s: the target is not committed" % (self, target))

		target_id = str(target._properties["_id"])

		# case where this object has no connection yet
		if (not target_id in self._properties["_relationships"]):
			assert (not target_id in self._properties["_relationship_with"]) ###
			self._properties["_relationship_with"].append(target_id)

		# case where this object has a connection with the target
		else:
			assert (target_id in self._properties["_relationship_with"]) ###
			if (self._properties["_relationships"][target_id] == relationship):
				return

		self._properties["_relationships"][target_id] = relationship
		self._committed = False

	# Disconnect this object from another
	def _disconnect_from (self, target):
		if (not target._committed):
			raise Exception("Object %s is not connected to %s" % (self, target))

		target_id = str(target._properties["_id"])

		if (not target_id in self._properties["_relationships"]):
			raise Exception("Object %s is not connected to %s" % (self, target))

		del self._properties["_relationships"][target_id]
		self._properties["_relationship_with"].remove(target_id)
		self._committed = False

	# Return a description of the relationship between this object and another
	# object, if any.
	#	target -- Object with which this object has a relationship
	def relationship_with (self, target):
		if (not target._committed):
			return None

		target_id = str(target._properties["_id"])

		if (target_id in self._properties["_relationships"]):
			return copy.deepcopy(self._properties["_relationships"][target_id])
		else:
			return None

	# Remove this object from the database. Also remove all relationships
	# between other objects and this object.
	# Note: The object remains in memory, flagged as uncommitted.
	def remove (self):
		if (not self._committed):
			raise errors.UncommittedObject()

		for neighbor in backend.neighbors(self):
			neighbor._disconnect_from(self)

		backend.remove(self)
		del self._properties["_id"]
		self._committed = False

	# Remove all objects of this type in the database.
	# Note: any existing instance of this object remains in memory, flagged as uncommitted.
	@classmethod
	def remove_all (cls):
		backend.remove_all(cls.__name__)

	def __del__ (self):
		# if the object is destroyed due to an exception thrown during
		# its instantiation, self._committed will not exists.
		if (not hasattr(self, "_committed")):
			return

		if (not self._committed):
			logger.warning("Object %s has been destroyed without having been committed" % self)

	def __repr__ (self):
		return self.__str__()

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Sequence object.
class Sequence (CommittableObject):

	def __init__ (self, **properties):
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

#		super(Sequence, self).__init__(indices, **properties)
		CommittableObject.__init__(self, indices, **properties)

	def add_to_collection (self, collection, relationship):
		self._connect_to(collection, relationship)

	def remove_from_collection (self, collection):
		self._disconnect_from(collection)

	def list_collections (self, collection_filter = None, relationship_filter = None):
		return backend.outgoing_neighbors(self, "Collection", collection_filter, relationship_filter)

	def count_collections (self, collection_filter = None, relationship_filter = None):
		return backend.outgoing_neighbors(self, "Collection", collection_filter, relationship_filter, True)

	def part_of_sequence (self, sequence, relationship):
		pass

	def similar_to (self, sequence, relationship):
		pass

	def disconnect_from_sequence (self, sequence):
		pass

	def __str__ (self):
		return "<Sequence id:%s name:'%s' length:%s state:'%s'>" % (
			self.get_property("_id", "none"),
			self["name"],
			self["length"],
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

# Collection of Sequence objects.
class Collection (CommittableObject):

	def __init__ (self, **properties):
		if (not "name" in properties):
			raise errors.MalformedObject("Property 'name' is missing")

		indices = {
			"name": True,
			"class": False,
		}

#		super(Collection, self).__init__(indices, **properties)
		CommittableObject.__init__(self, indices, **properties)

	def add_sequence (self, sequence, **relationship):
		sequence._connect_to(self, relationship)

	def remove_sequence (self, sequence):
		sequence._disconnect_from(self)

	def list_sequences (self, sequence_filter = None, relationship_filter = None):
		return backend.ingoing_neighbors(self, "Sequence", sequence_filter, relationship_filter)

	def count_sequences (self, sequence_filter = None, relationship_filter = None):
		return backend.ingoing_neighbors(self, "Sequence", sequence_filter, relationship_filter, True)

	def add_to_collection (self, collection, relationship):
		self._connect_to(collection, relationship)

	def remove_from_collection (self, collection):
		self._disconnect_from(collection)

	def remove_collection (self, collection):
		collection._disconnect_from(self)

	def list_super_collections (self, collection_filter = None, relationship_filter = None):
		return backend.outgoing_neighbors(self, "Collection", collection_filter, relationship_filter)

	def count_super_collections (self, collection_filter = None, relationship_filter = None):
		return backend.outgoing_neighbors(self, "Collection", collection_filter, relationship_filter, True)

	def list_sub_collections (self, collection_filter = None, relationship_filter = None):
		return backend.ingoing_neighbors(self, "Collection", collection_filter, relationship_filter)

	def count_sub_collections (self, collection_filter = None, relationship_filter = None):
		return backend.ingoing_neighbors(self, "Collection", collection_filter, relationship_filter, True)

	def __str__ (self):
		return "<Collection id:%s name:'%s' state:'%s'>" % (
			self.get_property("_id", "none"),
			self["name"],
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

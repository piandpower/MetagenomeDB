# base.py: root class abstracting the MongoDB content

import forge, tree, errors, commons
import pymongo
import sys, datetime, itertools, copy

# Base object.
class Object (object):

	# Create a new base object.
	#	properties -- (dictionary) object annotations. Nested properties can
	#		be expressed using dot notation.
	def __init__ (self, **properties):
		self.__properties = {}

		for key, value in properties.iteritems():
			key = tree.validate_key(key)
			tree.set(self.__properties, key, value)

		if ("_indices" in self.__properties):
			self.__indices = self.__properties["_indices"]
			del self.__properties["_indices"]
		else:
			self.__indices = {}

		# if the object is provided with an identifier,
		# we check if this identifier is present in the
		# object cache to know if it was committed.
		if ("_id" in self.__properties):
			id = self.__properties["_id"]

			if (type(id) == str):
				id = pymongo.objectid.ObjectId(id)
				self.__properties["_id"] = id

			if (not forge.exists(id)):
				raise ValueError("Unknown identifier '%s'" % id)

			self.__committed = True
		else:
			self.__committed = False

		# TODO: prevent the user to inject 'internal' keys; e.g., _creation_time

	# Commit this object to the database.
	#	patch -- (dictionary) transient properties patch; set of properties
	#		that will be added to the object prior commit. Those properties
	#		are removed (or restored, if overwritten) after commit.
	def commit (self, **patch):
		if (self.__committed):
			return

		# If some patch needs to be applied on the object's
		# properties, we temporary store the old values
		tmp = {}
		for (key, value) in patch.iteritems():
			assert (key != "_id") ###
			tmp[key] = self.__properties[key]
			self.__properties[key] = value

		id = forge.commit(self, self.__indices)
		self.__committed = True
		self.__properties["_id"] = id

		# We restore the object's properties, if needed
		for (key, value) in tmp.iteritems():
			self.__properties[key] = value

	# Count the number of object of this type in the database.
	#	filter -- (dictionary) optional filter.
	@classmethod
	def count (cls, **filter):
		return forge.count(cls.__name__, query = filter)

	# Count instances of this object having distinct values for a given property.
	#	property -- property to count objects for.
	# Return a dictionary with distinct values for this property as keys, and
	# number of objects having this value as value.
	@classmethod
	def distinct (cls, property):
		return forge.distinct(cls.__name__, property)

	# Find all instances of this object that match a query.
	#	filter -- (dictionary) query, or None if all objects are to be returned.
	# Return the objects selected, as a generator.
	@classmethod
	def find (cls, **filter):
		return forge.find(cls.__name__, query = filter)

	# Find the first (or only) instance of this object that match a query.
	#	filter -- (dictionary) query, or None if all objects are to be returned.
	@classmethod
	def find_one (cls, **filter):
		return forge.find(cls.__name__, query = filter, find_one = True)

	# Return a copy of all of this object's properties.
	# Return a dictionary.
	def get_properties (self):
		return self.__properties.copy()

	# Return the value for a given property.
	#	property -- property to retrieve. Nested properties can be requested
	#		using a dot notation.
	#	default -- default value to return if the property is not set.
	def get_property (self, key, default = None):
		try:
			return copy.deepcopy(self.__getitem__(key))

		except KeyError:
			return default

	INGOING, REFERRING = 1, 1
	OUTGOING, REFERRED = 2, 2
	BOTH = 3

	# Return anonymous objects this object is related to.
	#	direction -- either Object.INGOING (or Object.REFERRING; anonymous
	#		objects referring to this object) or Object.OUTGOING (or
	#		Object.REFERRED; anonymous objects refered to be this object).
	#	object_filter -- filter to apply on the related anoynmous objects.
	#	relationship_filter -- filter to apply on the relationship between this
	#		object and the related anonymous objects.
	# Return the related anonymous objects as a generator.
	def get_related_objects (self, direction, object_filter = None, relationship_filter = None):
		ingoing, outgoing = [], []

		if (direction & self.INGOING != 0):
			ingoing = forge.find_neighbors(self, forge.INGOING, "Object", object_filter, relationship_filter)

		if (direction & self.OUTGOING != 0):
			outgoing = forge.find_neighbors(self, forge.OUTGOING, "Object", object_filter, relationship_filter)

		return itertools.chain(ingoing, outgoing)

	# Test if this object has been committed to the database.
	# Return a boolean.
	def is_committed (self):
		return self.__committed

	# Remove this object from the database.
	# Note: The object remains in memory, flagged as uncommitted.
	def remove (self):
		if (not self.__committed):
			raise errors.UncommittedObject()

		forge.remove(self)
		del self.__properties["_id"]
		self.__committed = False

	# Remove all objects of this type in the database.
	# Note: any existing instance of this object remains in memory, flagged as uncommitted.
	@classmethod
	def remove_all (cls):
		forge.remove_all(cls.__name__)

	def __del__ (self):
		# if the object is destroyed due to an exception thrown during
		# its instantiation, self.__committed will not exists.
		if (not hasattr(self, "__committed")):
			return

		if ((not self.__committed) and commons.display_warnings):
			print >>sys.stderr, "WARNING: Object %s has been destroyed without having been committed" % self

	def __setitem__ (self, key, value):
		keys = tree.validate_key(key)
		if (keys[0] == "_id"):
			raise ValueError("The property '_id' cannot be modified")

		# discard 'phantom' modifications
		if tree.contains(self.__properties, keys) and \
		   (value == tree.get(self.__properties, keys)):
			return

		tree.set(self.__properties, keys, value)
		self.__committed = False

	def __getitem__ (self, key):
		keys = tree.validate_key(key)
		return copy.deepcopy(tree.get(self.__properties, keys))

	def __delitem__ (self, key):
		keys = tree.validate_key(key)
		if (keys[0] == "_id"):
			raise ValueError("The property '_id' cannot be modified")

		tree.delete(self.__properties, keys)
		self.__committed = False

	def __contains__ (self, key):
		keys = tree.validate_key(key)
		return tree.contains(self.__properties, keys)

	def __str__ (self):
		return "<Object id:%s state:'%s'>" % (
			self.get_property("_id", "none"),
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

	def __repr__ (self):
		return self.__str__()

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Sequence object.
class Sequence (Object):

	def __init__ (self, **properties):
		if (not "name" in properties):
			raise errors.MalformedObject("Property 'name' is missing")

		if (not "sequence" in properties):
			raise errors.MalformedObject("Property 'sequence' is missing")
	
		# TODO: Check the sequence
		# TODO: Check the sequence length; if too big (what is the limit?)
		#       we should store it using gridfs

		properties["length"] = len(properties["sequence"])

		properties["_indices.name"] = False
		properties["_indices.length"] = False
		properties["_indices.class"] = False

		super(Sequence, self).__init__(**properties)

	# Return collections this sequence is part of.
	# - collection_filter: collection filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_collections (self, collection_filter = None, relationship_filter = None):
		return forge.find_neighbors(self, forge.OUTGOING, "Collection", collection_filter, relationship_filter)

	# Return sequences this sequence is related to.
	#	direction -- either Sequence.INGOING (sequences referring to this sequence;
	#		Sequence.REFERRING can also be used) or Sequence.OUTGOING (sequences
	#		refered to be this sequence; Sequence.REFEREED can also be used).
	#	sequence_filter -- filter to apply on the related sequences.
	#	relationship_filter -- filter to apply on the relationship between this
	#		sequence and the related sequences.
	# Return the related sequences as a generator.
	def get_related_sequences (self, direction, sequence_filter = None, relationship_filter = None):
		ingoing, outgoing = [], []

		if (direction & self.INGOING != 0):
			ingoing = forge.find_neighbors(self, forge.INGOING, "Sequence", sequence_filter, relationship_filter)

		if (direction & self.OUTGOING != 0):
			outgoing = forge.find_neighbors(self, forge.OUTGOING, "Sequence", sequence_filter, relationship_filter)

		return itertools.chain(ingoing, outgoing)

	def __str__ (self):
		return "<Sequence id:%s name:'%s' length:%s state:'%s'>" % (
			self.get_property("_id", "none"),
			self["name"],
			self["length"],
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

# Collection of Sequence objects.
class Collection (Object):

	def __init__ (self, **properties):
		if (not "name" in properties):
			raise errors.MalformedObject("Property 'name' is missing")

		properties["_indices.name"] = True
		properties["_indices.class"] = False

		super(Collection, self).__init__(**properties)

	# Add a sequence object to this collection.
	def add_sequence (self, sequence, relationship = None):
		# TO DO
		raise NotImplementedError

	# Remove a sequence object from this collection.
	# Note: Raise a ObjectNotFound error if the sequence is not part of this collection.
	def remove_sequence (self, sequence, relationship = None):
		# TO DO
		raise NotImplementedError

	def has_sequence (self, sequence):
		if (type(sequence) == Sequence):
			sequence = sequence["name"]

		return forge.has_neighbor(self, forge.INGOING, "Sequence", {"name": sequence})

	# Return collections this collection is part of.
	#	collection_filter -- filter to apply on the super-collections
	#	relationship_filter -- filter to apply on the relationship between this
	#		collection and the related super-collections 
	# Return the related collections as a generator.
	def get_supercollections (self, collection_filter = None, relationship_filter = None):
		return forge.find_neighbors(self, forge.OUTGOING, "Collection", collection_filter, relationship_filter)

	# Return collections that are part of this collection.
	#	collection_filter -- filter to apply on the sub-collections
	#	relationship_filter -- filter to apply on the relationship between this
	#		collection and the related sub-collections 
	# Return the related collections as a generator.
	def get_subcollections (self, collection_filter = None, relationship_filter = None):
		return forge.find_neighbors(self, forge.INGOING, "Collection", collection_filter, relationship_filter)

	# Return sequences that are part of this collection.
	# - sequence_filter: sequence filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	#	sequence_filter -- filter to apply on the related sequences.
	#	relationship_filter -- filter to apply on the relationship between this
	#		sequence and the related sequences.
	# Return the related sequences as a generator.
	def get_sequences (self, sequence_filter = None, relationship_filter = None):
		return forge.find_neighbors(self, forge.INGOING, "Sequence", sequence_filter, relationship_filter)

	def count_sequences (self, sequence_filter = None, relationship_filter = None):
		return forge.find_neighbors(self, forge.INGOING, "Sequence", sequence_filter, relationship_filter, count = True)

	# Remove this collection from the database.
	#	remove_sequences -- (boolean) if True, remove also the sequences that
	#		belong to this collection
	# TODO: allow the removal of super- and sub-collections
	def remove (self, remove_sequences = False):
		if (remove_sequences):
			for sequence, relationship in self.get_sequences():
				relationship.remove(remove_source = True)

		super(Collection, self).remove()

	def __str__ (self):
		return "<Collection id:%s name:'%s' state:'%s'>" % (
			self.get_property("_id", "none"),
			self["name"],
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

# Relationship between Collection and/or Sequence objects.
class Relationship (Object):

	def __init__ (self, **properties):
		for key in ("source", "target"):
			if (key in properties):
				properties[key] = Relationship.__validate(properties[key], key)
			else:
				raise errors.MalformedObject("Property '%s' is missing" % key)

		if (not "type" in properties):
			raise errors.MalformedObject("Property 'type' is missing")

		properties["_indices.source"] = False
		properties["_indices.target"] = False
		properties["_indices.type"] = False

		super(Relationship, self).__init__(**properties)

	def __setitem__ (self, key, value):
		if (key in ("source", "target")):
			value = Relationship.__validate(value, key)

		super(Relationship, self).__setitem__(key, value)

	@classmethod
	def __validate (cls, object, side):
		if (isinstance(object, pymongo.dbref.DBRef)) and (object.collection in ("Collection", "Sequence", "Object")):
			return forge.find(object.collection, object.id, True)

		elif (object.__class__.__name__ in ("Collection", "Sequence", "Object")):
			return object

		else:
			raise errors.MalformedObject("Invalid value for '%s': must be an Object, Collection or Sequence object" % side)

	# Return the object declared as the source of this relationship.
	def get_source (self):
		return self["source"]

	# Return the object declared as the target of this relationship.
	def get_target (self):
		return self["target"]

	def commit (self):
		patch = {}

		source = self["source"]
		source.commit()
		patch["source"] = pymongo.dbref.DBRef(source.__class__.__name__, source["_id"])

		target = self["target"]
		target.commit()
		patch["target"] = pymongo.dbref.DBRef(target.__class__.__name__, target["_id"])

		super(Relationship, self).commit(**patch)

	# Remove this relationship from the database.
	#	remove_source -- if True, remove also the source object
	#	remove_target -- if True, remove also the target object
	def remove (self, remove_source = False, remove_target = False):
		if (remove_source):
			self["source"].remove()

		if (remove_target):
			self["target"].remove()

		super(Relationship, self).remove()

	def __str__ (self):
		return "<Relationship id:%s source:%s %s target:%s state:'%s'>" % (
			self.get_property("_id", "none"),
			self["source"],
			self["type"],
			self["target"],
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

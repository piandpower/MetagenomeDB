# base.py: root class abstracting the MongoDB content

import connection, forge, tree, errors, commons
import pymongo
import sys, datetime

class Object (object):

	# Create a new object wrapping a MongoDB collection.
	# - properties: dictionary of key/values for this object
	# - indices: dictionary of which keys will be set as indexes for the
	#   MongoDB collection. Values are booleans that indicate if this index
	#   must contains unique values.
	def __init__ (self, properties, indices):
		self.__properties = {}
		self.__indices = indices

		for key, value in properties.iteritems():
			key = tree.validate_key(key)
			tree.set(self.__properties, key, value)

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

	#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: Class methods

	# Count the number of instances of this object in the database
	@classmethod
	def count (cls, **filter):
		return forge.count(cls.__name__, query = filter)

	# Retrieve distinct values (and number of objects having this value) for
	# a given property
	@classmethod
	def distinct (cls, property):
		return forge.distinct(cls.__name__, property)

	# Select instances of this object that pass a filter,
	# expressed as a set of (possibly) nested key/values.
	# If no filter is provided, all instances are returned.
	@classmethod
	def find (cls, **filter):
		return forge.find(cls.__name__, query = filter)

	# Same as find(), but return only the first instance.
	@classmethod
	def find_one (cls, **filter):
		return forge.find(cls.__name__, query = filter, find_one = True)

	# Remove all objects of this type in the database. Note that
	# any existing instance of this object remains in memory, albeit
	# flagged as uncommitted.
	@classmethod
	def remove_all (cls):
		forge.remove_all(cls.__name__)

	#:::::::::::::::::::::::::::::::::::::::::::::::::::::::: Instances methods

	# Test if this object has been committed to the database.
	def is_committed (self):
		return self.__committed

	# Commit this instance of this object to the database.
	# The new identifier of this object is returned.
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

		return id

	# Remove this object from the database. The object
	# remains in memory, albeit flagged as uncommitted.
	def remove (self):
		if (not self.__committed):
			raise errors.UncommittedObject()

		forge.remove(self)
		del self.__properties["_id"]
		self.__committed = False

	def __del__ (self):
		# if the object is destroyed due to an exception thrown during
		# its instantiation, self.__committed will not exists.
		if (not hasattr(self, "__committed")):
			return

		if ((not self.__committed) and commons.display_warnings):
			print >>sys.stderr, "WARNING: Object %s has been destroyed without having been committed" % self

	# Find neighbors of this object in the database, as declared through
	# 'Relationship' objects.
	# - direction: either INGOING (objects pointing to this object) or
	#   OUTGOING (objects pointed by this object)
	# - neighbor_class: class of the neighbors to look for
	# - neighbor_filter: neighbor filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary
	# Note: This method shouldn't be called directly by the user.
	def get_neighbors (self, direction, neighbor_class, neighbor_filter, relationship_filter):
		if (not self.__committed):
			raise errors.UncommittedObject()

		return forge.neighbors(
			self,
			direction,
			neighbor_class,
			neighbor_filter,
			relationship_filter
		)

	#:::::::::::::::::::::::::::::::::::::::::::::::::: Properties manipulation

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
		return tree.get(self.__properties, keys)

	def __delitem__ (self, key):
		keys = tree.validate_key(key)
		if (keys[0] == "_id"):
			raise ValueError("The property '_id' cannot be modified")

		tree.delete(self.__properties, keys)
		self.__committed = False

	def __contains__ (self, key):
		keys = tree.validate_key(key)
		return tree.contains(self.__properties, keys)

	# Returns a copy of this object's properties, as a nested dictionary.
	def get_properties (self):
		return self.__properties.copy()

	# Return the value of a given property, or a default one if this
	# property doesn't exist.
	def get_property (self, key, default = None):
		try:
			return self.__getitem__(key)

		except KeyError:
			return default

	#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: Misc. methods

	def __str__ (self):
		if (hasattr(self, "__committed") and self.__committed):
			return "<Object %s>" % id
		else:
			return "<Object (uncommitted)>"

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

		if (not "length" in properties):
			properties["length"] = len(properties["sequence"])

		super(Sequence, self).__init__(properties, {
			"name": False,
			"length": False,
			"class": False,
		})

	# Return collections this sequence is part of.
	# - collection_filter: collection filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_collections (self, collection_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.OUTGOING, "Collection", collection_filter, relationship_filter)

	# Return sequences this sequence refers to.
	# - sequence_filter: sequence filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_refereed_sequences (self, sequence_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.OUTGOING, "Sequence", sequence_filter, relationship_filter)

	# Return sequences referring this sequence.
	# - sequence_filter: sequence filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_referring_sequences (self, sequence_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.INGOING, "Sequence", sequence_filter, relationship_filter)

	def __str__ (self):
		return "<Sequence id:%s name:'%s' len:%s>" % (
			self.get_property("_id", "(uncommitted)"),
			self["name"],
			self["length"]
		)

# Collection of Sequence objects.
class Collection (Object):

	def __init__ (self, **properties):
		if (not "name" in properties):
			raise errors.MalformedObject("Property 'name' is missing")

		super(Collection, self).__init__(properties, {
			"name": True,
			"class": False,
		})

	# Return collections this collection is part of.
	# - collection_filter: collection filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_supercollections (self, collection_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.OUTGOING, "Collection", collection_filter, relationship_filter)

	# Return collections that are part of this collection.
	# - collection_filter: collection filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_subcollections (self, collection_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.INGOING, "Collection", collection_filter, relationship_filter)

	# Return sequences that are part of this collection.
	# - sequence_filter: sequence filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_sequences (self, sequence_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.INGOING, "Sequence", sequence_filter, relationship_filter)

	# Remove this collection from the database.
	# - remove_sequences: if True, remove also the sequences that belong to this collection
	# TODO: allow the removal of super- and sub-collections
	def remove (self, remove_sequences = False):
		if (remove_sequences):
			for sequence, relationship in self.get_sequences():
				relationship.remove(remove_source = True)

		super(Collection, self).remove()

	def __str__ (self):
		return "<Collection id:%s name:'%s'>" % (
			self.get_property("_id", "(uncommitted)"),
			self["name"]
		)

# Relationship between Collection and/or Sequence objects.
class Relationship (Object):

	def __init__ (self, **properties):
		self.__is_custom = {}

		for load in ("source", "target"):
			custom_load = "custom_" + load

			if (load in properties):
				if (custom_load in properties):
					raise errors.MalformedObject("Properties '%s' and '%s' can not coexist" % (load, custom_load))

				properties[load] = Relationship.__validate_target_or_source(properties[load], load)
				self.__is_custom[load] = False

			elif (custom_load in properties):
				self.__is_custom[load] = True

			else:
				raise errors.MalformedObject("Property '%s' is missing" % key)

		if (not "type" in properties):
			raise errors.MalformedObject("Property 'type' is missing")

		super(Relationship, self).__init__(properties, {
			"source": False,
			"target": False,
			"custom_source": False,
			"custom_target": False,
			"type": False,
		})

	# Hook to validate sources and targets on-the-fly
	def __setitem__ (self, key, value):
		if (key in ("source", "target")):
			Relationship.__validate_target_or_source(value, key)
			if (self.__is_custom[key]):
				del self["custom_%s" % key]

			self.__is_custom[key] = False

		elif (key in ("custom_source", "custom_target")):
			key_ = key[7:]
			if (not self.__is_custom[key_]):
				del self[key_]

			self.__is_custom[key_] = True

		super(Relationship, self).__setitem__(key, value)

	# Validate objects provided as either source or target
	@classmethod
	def __validate_target_or_source (cls, object, side):
		if (isinstance(object, pymongo.dbref.DBRef)) and (object.collection in ("Collection", "Sequence")):
			return forge.find(object.collection, object.id, True)

		elif (isinstance(object, Collection) or isinstance(object, Sequence)):
			return object

		else:
			raise errors.MalformedObject("Invalid value for '%s': must be a Collection or Sequence object" % side)

	# Return the collection or sequence declared as the source of this relationship.
	def get_source (self):
		if self.is_source_custom():
			return self["custom_source"]
		else:
			return self["source"]

	def is_source_custom (self):
		return self.__is_custom["source"]

	# Return the collection or sequence declared as the target of this relationship.
	def get_target (self):
		if self.is_target_custom():
			return self["custom_target"]
		else:
			return self["target"]

	def is_target_custom (self):
		return self.__is_custom["target"]

	def commit (self):
		patch = {}

		if (not self.is_source_custom()):
			source = self["source"]
			source.commit()
			patch["source"] = pymongo.dbref.DBRef(source.__class__.__name__, source["_id"])

		if (not self.is_target_custom()):
			target = self["target"]
			target.commit()
			patch["target"] = pymongo.dbref.DBRef(target.__class__.__name__, target["_id"])

		super(Relationship, self).commit(**patch)

	# Remove this relationship from the database.
	# - remove_source: if True, remove also the source object
	# - remove_target: if True, remove also the target object
	def remove (self, remove_source = False, remove_target = False):
		if (remove_source and not self.is_source_custom()):
			self["source"].remove()

		if (remove_target and not self.is_target_custom()):
			self["target"].remove()

		super(Relationship, self).remove()

	def __str__ (self):
		return "<Relationship id:%s source:%s %s target:%s>" % (
			self.get_property("_id", "(uncommitted)"),
			self.get_property("source", "(custom)"),
			self["type"],
			self.get_property("target", "(custom)")
		)

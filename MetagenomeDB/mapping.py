# mapping.py: root class abstracting the MongoDB content

# TODO:
# - assert no user-provided field can start with a '_'

import connection, forge, tree
import pymongo
import sys, json

class UncommittedObject (Exception):
	def __init__ (self, msg = None):
		self.msg = msg

	def __str__ (self):
		return self.msg

class Object (object):
	def __init__ (self, properties, indexes):
		self.__properties = properties
		self.__indexes = indexes

		if ("_id" in self.__properties):
			id = self.__properties["_id"]

			if (type(id) == str):
				id = pymongo.objectid.ObjectId(id)
				self.__properties["_id"] = id

			if (not forge.exists(id)):
				raise ValueError("Unknown identifier '%s'" % id)

			# unless the object is provided an _id, it
			# is considered not stored in the database.
			self.__committed = True

	#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: Class methods

	# Create a new object from a JSON-formatted file.
	@classmethod
	def from_json (cls, fn):
		data = json.load(open(fn, 'r'))

		kw = {}
		for (key, value) in iterate(data):
			kw['_'.join(key)] = value

		return cls(**kw)

	# Count the number of instances of this object in the database
	@classmethod
	def count (cls):
		return forge.count(cls.__name__)

	# Select instances of this object that pass a filter,
	# expressed as a set of (possibly) nested key/values.
	# If no filter is provided, all instances are returned.
	@classmethod
	def select (cls, **filter):
		return forge.find(cls.__name__, query = filter)

	# Same as select(), but return only the first instance.
	@classmethod
	def select_one (cls, **filter):
		return forge.find(cls.__name__, query = filter, find_one = True)

	# Remove all objects of this type in the database. Note that
	# any existing instance of this object remains in memory, albeit
	# flagged as uncommitted.
	@classmethod
	def remove_all (cls):
		forge.drop(cls.__name__)

	#:::::::::::::::::::::::::::::::::::::::::::::::::::::::: Instances methods

	# Test if this object has been committed to the database.
	def is_committed (self):
		return self.__committed

	# Commit this instance of this object to the database.
	# The new identifier of this object is returned.
	def commit (self, **patch):
		# If some patch needs to be applied on the object's
		# properties, we temporary store the old values
		tmp = {}
		for (key, value) in patch.iteritems():
			assert (key != "_id") ###
			tmp[key] = self.__properties[key]
			self.__properties[key] = value

		id = forge.commit(self, self.__indexes)
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
			raise UncommittedObject()

		forge.remove(self)
		tree.delete(self.__properties, "_id")
		self.__committed = False

	def __del__ (self):
		if (not self.__committed):
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
			raise UncommittedObject()

		return forge.neighbors(
			self,
			direction,
			neighbor_class,
			neighbor_filter,
			relationship_filter
		)

	#:::::::::::::::::::::::::::::::::::::::::::::::::: Properties manipulation

	def __setitem__ (self, key, value):
		if (type(key) == str):
			key = key.split('.')

		if (key[0] == "_id"):
			raise ValueError("The property '_id' is read-only")

		# discard 'phantom' modifications
		if tree.contains(self.__properties, key) and (value == tree.get(self.__properties, key)):
			return

		tree.set(self.__properties, key, value)
		self.__committed = False

	def __getitem__ (self, key):
		if (type(key) == str):
			key = key.split('.')

		return tree.get(self.__properties, key)

	def __delitem__ (self, key):
		if (type(key) == str):
			key = key.split('.')

		if (key[0] == "_id"):
			raise ValueError("The property '_id' is read-only")

		tree.delete(self.__properties, key)
		self.__committed = False

	def __contains__ (self, key):
		if (type(key) == str):
			key = key.split('.')

		return tree.contains(self.__properties, key)

	# Returns a copy of this object's properties, as a nested dictionary.
	def get_properties (self):
		return self.__properties.copy()

	# Return the value of a given property, or a default one if this
	# property doesn't exist.
	def get_property (self, key, default):
		try:
			return tree.get(self.__properties, key)
		except:
			return default

	#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: Misc. methods

	def __str__ (self):
		if (self.__committed):
			return "<Object %s>" % id
		else:
			return "<Object (uncommitted)>"

	def __repr__ (self):
		return self.__str__()


# TODO:
# - assert no user-provided field can start with a '_'

import commons, connection, forge, tree
import pymongo
from encodings import hex_codec
import sys, json, datetime

class UncommittedObject (Exception):
	def __init__ (self, msg):
		self.msg = msg

	def __str__ (self):
		return self.msg

class DuplicateObject (Exception):
	pass

NOT_STORED = 1
STORED = 2
REMOVED = 3

class Object (object):

	_indexes = {}

	def __init__ (self, **kw):
		self.__properties = {}

		for key, value in kw.iteritems():
			if (key == "_id"):
				self.__properties[key] = value
			else:
				tree.set(self.__properties, key.split('_'), value)

		if ("_id" in self.__properties):
			self.__state = STORED
		else:
			self.__state = NOT_STORED

		self.__modified = False

	# Create a new object from a JSON-formated file.
	@classmethod
	def from_json (cls, fn):
		data = json.load(open(fn, 'r'))

		kw = {}
		for (key, value) in iterate(data):
			kw['_'.join(key)] = value

		return cls.from_dict(kw)

	# Returns a copy of the internal JSON-like description of this object.
	def as_dict (self):
		return self.__properties.copy()

	def __del__ (self):
		if (self.__state == NOT_STORED):
			print >>sys.stderr, "WARNING: Object %s has been destroyed without having been committed" % self

	# Returns the identifier this object have in the database. If this object
	# has never been committed, a UncommittedObject exception is thrown.
	def id (self):
		if (self.__state != STORED):
			raise UncommittedObject("This object is not referenced in the database")

		return self.__properties["_id"]

	# Returns a flag telling if this object has been modified
	# since it has been created or committed to the database.
	def is_modified (self):
		return self.__modified

	# Returns a flag telling if this object has already been
	# committed to the database. Note: a committed object could
	# have been modified since its last commit, and could not
	# reflects the information stored in the database.
	def is_committed (self):
		return (self.__state == STORED)

	def __setitem__ (self, key, value):
		if (type(key) == str):
			key = key.split('.')

		# discard 'phantom' modifications
		if tree.contains(self.__properties, key) and (value == tree.get(self.__properties, key)):
			return

		tree.set(self.__properties, key, value)
		self.__modified = True

	def __getitem__ (self, key):
		if (type(key) == str):
			key = key.split('.')

		return tree.get(self.__properties, key)

	def get (self, key, default):
		try:
			return tree.get(self.__properties, key)
		except:
			return default

	def __delitem__ (self, key):
		if (key == "_id"):
			raise ValueError("The field '_id' cannot be deleted")

		if (type(key) == str):
			key = key.split('.')

		tree.delete(self.__properties, key)

	def __contains__ (self, key):
		if (type(key) == str):
			key = key.split('.')

		return tree.contains(self.__properties, key)

	def validate (self, schema):
		### TO DO
		raise NotImplementedError

	def _neighbors (self, this_end, collection, query = None, where = None):
		if (self.__state != STORED):
			raise UncommittedObject("Unable to retrieve neighbors of %s until it is committed" % self)

		relationships = connection.connection()["Relationship"]

		if (query == None):
			query = {}

		if (this_end == "source"):
			other_end = "target"
		else:
			other_end = "source"

		query[this_end] = pymongo.dbref.DBRef(self.__class__.__name__, self.id())

		if (where == None):
			getter = relationships.find(query)
		else:
			getter = relationships.find(query).where(where)

		def results():
			for relationship in getter:
				xref = relationship[other_end]

				if (xref.collection == collection):
					neighbor = forge.create_from_query(xref.collection, xref.id)
					relationship = forge.create_from_json("Relationship", relationship)

					yield neighbor, relationship

		return results()

	# Commit this object to the database. The
	# new identifier of this object is returned.
	def commit (self, **kw):
		collection = self.__class__.__name__

		db = connection.connection()

		if (not collection in db.collection_names()):
			if (commons.debug_level > 0):
				if (len(self._indexes) > 0):
					commons.log("commit", "'%s' collection created with indexes %s" % (collection, ', '.join(["'%s'" % key for key in sorted(self._indexes.keys())])))
				else:
					commons.log("commit", "'%s' collection created" % collection)

			for (index, is_unique) in self._indexes.iteritems():
				db[collection].create_index(index, unique = is_unique)

		# If some patch needs to be applied on the object's
		# properties, we temporary store the old values
		tmp = {}
		for (key, value) in kw.iteritems():
			tmp[key] = self.__properties[key]
			self.__properties[key] = value

		# Insertion
		if (self.__state != STORED):
			self.__properties["created-on"] = datetime.datetime.now()

			try:
				id = db[collection].insert(self.__properties, safe = True, check_keys = True)

			except pymongo.errors.OperationFailure, e:
				if ("E11000" in str(e)):
					raise DuplicateObject()
				else:
					raise Exception("Unable to commit: %s" % e)

			self.__properties["_id"] = id
			self.__state = STORED
			self.__modified = False

			verb = "created"

		# Update
		elif (self.__modified):
			self.__properties["last-modified-on"] = datetime.datetime.now()

			self.__modified = False

			### TO DO
			raise NotImplementedError

			verb = "updated"

		else:
			verb = "unchanged"

		# We restore the object's properties, if needed
		for (key, value) in tmp.iteritems():
			self.__properties[key] = value

		if (commons.debug_level > 1):
			commons.log("commit", "%s %s in collection '%s'" % (self, verb, collection))

		return self["_id"]

	# Count the number of instances of this object in the database
	@classmethod
	def count (cls):
		return forge.count(cls.__name__)

	# Select instances of this object that statisfy a criterion,
	# expressed as a nested tree.
	# If no criteria is provided, all instances are returned.
	@classmethod
	def select (cls, **kwargs):
		return forge.find(cls.__name__, query = kwargs)

	# Select the first (or the only) instance of this object that satisfy
	# a criterion, expressed as a nested tree.
	@classmethod
	def select_one (cls, **kwargs):
		return forge.find(cls.__name__, query = kwargs, find_one = True)

	# Delete this object from the database. The object does remain
	# in memory, albeit its status is set to uncommitted.
	def delete (self):
		collection = self.__class__.__name__

		connection.connection()[collection].remove({ "_id": self.id() })

		tree.delete(self.__properties, "_id")
		self.__state = REMOVED

		if (commons.debug_level > 1):
			commons.log("remove", "%s removed from '%s'" % (self, collection))

	# Drop all objects of this type in the database.
	@classmethod
	def drop (cls):
		connection.connection().drop_collection(cls.__name__)

		if (commons.debug_level > 0):
			commons.log("drop", "'%s' collection dropped" % cls.__name__)

	def __str__ (self):
		if (self.__stored):
			return "<Object %s>" % id
		else:
			return "<Object (uncommitted)>"

	def __repr__ (self):
		return self.__str__()

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

def _ (map, key):
	value = map[key]
	del map[key]
	return value

class Collection (Object):

	_indexes = {
		"name": True,
		"class": False,
	}

	def __init__ (self, name, clazz, **kw):
		kw["name"] = name
		kw["class"] = clazz

		super(Collection, self).__init__(**kw)

	# Create a new Collection object from a tree.
	@classmethod
	def from_dict (cls, data):
		if (not "name" in data):
			raise ValueError("A 'name' property must be provided")

		if (not "class" in data):
			raise ValueError("A 'class' property must be provided")

		return cls(_(data, "name"), _(data, "class"), **data)

	# List collections this Collection is part of. A filter (expressed as a
	# MongoDB query) can be applied on the Relationship objects linking the
	# supercollections to this Collection.
	def get_supercollections (self, query = None, where = None):
		return self._neighbors("source", "Collection", query, where)

	# List sub-collections that are linked to this Collection. A filter
	# (expressed as a MongoDB query) can be applied on the Relationship objects
	# linking the subcollections to this Collection.
	def get_subcollections (self, query = None, where = None):
		return self._neighbors("target", "Collection", query, where)

	# List sequences that are part of this collection. A filter (expressed as a
	# MongoDB query) can be applied on the Relationship objects linking the
	# Sequence objects to this Collection.
	def get_sequences (self, query = None, where = None):
		return self._neighbors("target", "Sequence", query, where)

	# Remove this Collection from the database.
	def remove (self, remove_sequences = False):
		if (remove_sequences):
			for sequence, relationship in self.get_sequences():
				relationship.remove(remove_source = True)

		super(Collection, self).remove()

	def __str__ (self):
		return "<Collection id:%s name:'%s' class:'%s'>" % (self.get("_id", "(uncommitted)"), self["name"], self["class"])

class Sequence (Object):

	_indexes = {
		"name": False,
		"length": False,
	}

	def __init__ (self, name, sequence, **kw):
		# TODO: Check the sequence

		if (not "length" in kw):
			kw["length"] = len(sequence)

		kw["name"] = name
		kw["sequence"] = sequence

		super(Sequence, self).__init__(**kw)

	# Create a new Sequence object from a tree.
	@classmethod
	def from_dict (cls, data):
		if (not "name" in data):
			raise ValueError("A 'name' property must be provided")

		if (not "sequence" in data):
			raise ValueError("A 'sequence' property must be provided")

		return cls(_(data, "name"), _(data, "sequence"), **data)

	# List collections this Sequence is part of. A filter (expressed as a
	# MongoDB query) can be applied on the Relationship objects that link
	# this Sequence to a Collection.
	def get_collections (self, query = None, where = None):
		return self._neighbors("source", "Collection", query, where)

	# List sequences this Sequence is related to. A filter (expressed as a
	# MongoDB query) can be applied on the Relationship objects that link this
	# Sequence to other sequences.
	def get_refereed_sequences (self, query = None, where = None):
		return self._neighbors("source", "Sequence", query, where)

	# List sequences that relate to this Sequence. A filter (expressed as a
	# MongoDB query) can be applied on the Relationship objects that link
	# other sequences to this Sequence.
	def get_referring_sequences (self, query = None, where = None):
		return self._neighbors("target", "Sequence", query, where)

	def __str__ (self):
		return "<Sequence id:%s name:'%s' len:%s>" % (self.get("_id", "(uncommitted)"), self["name"], self["length"])

class Relationship (Object):

	_indexes = {
		"source": False,
		"target": False,
		"type": False,
	}

	def __init__ (self, source, target, type, **kw):
		kw["source"] = Relationship.__validate_source(source)
		kw["target"] = Relationship.__validate_target(target)
		kw["type"] = type

		super(Relationship, self).__init__(**kw)

	# Create a Relationship object from a tree.
	@classmethod
	def from_dict (cls, data):
		if (not "source" in data) or (not isinstance(data["source"], pymongo.dbref.DBRef)):
			raise ValueError("A 'source' property must be provided")

		if (not "target" in data) or (not isinstance(data["target"], pymongo.dbref.DBRef)):
			raise ValueError("A 'target' property must be provided")

		source_xref = _(data, "source")
		target_xref = _(data, "target")

		return cls(
			forge.create_from_query(source_xref.collection, source_xref.id),
			forge.create_from_query(target_xref.collection, target_xref.id),
			_(data, "type"),
			**data
		)

	# Get the object (Collection or Sequence) at the source of this relationship.
	def get_source (self):
		return self["source"]

	# Get the object (Collection or Sequence) that is the target of this relationship.
	def get_target (self):
		return self["target"]

	def commit (self):
		source, target = self["source"], self["target"]

		source.commit()
		target.commit()

		super(Relationship, self).commit(
			source = pymongo.dbref.DBRef(source.__class__.__name__, source.id()),
			target = pymongo.dbref.DBRef(target.__class__.__name__, target.id())
		)

	@classmethod
	def __validate_source (cls, source):
		if not (isinstance(source, Collection) or isinstance(source, Sequence)):
			raise ValueError("The source object must be of type Collection or Sequence")

		return source

	@classmethod
	def __validate_target (cls, target):
		if not (isinstance(target, Collection) or isinstance(target, Sequence)):
			raise ValueError("The target object must be of type Collection or Sequence")

		return target

	def __setitem__ (self, key, value):
		if (key == "source"):
			Relationship.__validate_source(value)

		elif (key == "target"):
			Relationship.__validate_target(value)

		super(Relationship, self).__setitem__(key, value)

	def remove (self, remove_source = False, remove_target = False):
		if (remove_source):
			self["source"].remove()

		if (remove_target):
			self["target"].remove()

		super(Relationship, self).remove()

	def __str__ (self):
		return "<Relationship id:%s source:%s %s target:%s>" % (self.get("_id", "(uncommitted)"), self["source"], self["type"], self["target"])

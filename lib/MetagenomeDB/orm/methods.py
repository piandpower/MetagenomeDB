# low-level interface with the MongoDB server

# Note: The term 'collection', when used in this file, refers to a MongoDB
# collection and NOT to the Collection class in objects.py

from .. import errors
import connection
import classes
from .. import utils

import pymongo, bson

import weakref
import datetime
import re
import logging
import inspect

logger = logging.getLogger("MetagenomeDB.ORM.methods")

# Object cache, as a map with weak values
_cache = weakref.WeakValueDictionary()

# List of classes the foundry should instanciate from MongoDB documents, based on the name of the collection this document comes from
_classes = {}

def declare_class (cls):
	_classes[cls.__name__] = cls

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Commit a PersistentObject to the database. IMPORTANT NOTE: this does not
# support concurrent modifications. I.e., if another client modifies the
# backend database after an object has been instanciated, a commit() will
# overwrite those modifications.
def _commit (object):
	db = connection.connection()

	collection_name = object.__class__.__name__
	collection = db[collection_name]

	# if the collection this object belongs to doesn't exist in
	# the database, we create it with its indices (if any)
	if (not collection_name in db.collection_names()):
		msg = "Collection '%s' created" % collection_name
		if (len(object._indices) > 0):
			msg += " with indices %s" % ', '.join(["'%s'" % key for key in sorted(object._indices.keys())])

			for (index, is_unique) in object._indices.iteritems():
				collection.create_index(index, unique = is_unique)

		logger.debug(msg + '.')

	# second case: the object is not committed, and is not in the database
	if (not "_id" in object):
		object._properties["_creation_time"] = datetime.datetime.utcnow()
		verb = "created"

	# third case: the object is not committed, but a former version exists in the database
	else:
		object._properties["_modification_time"] = datetime.datetime.utcnow()
		verb = "updated"

	try:
		object_id = collection.save(
			object.get_properties(),
			safe = True
		)

		object._properties["_id"] = object_id
		_cache[object_id] = object

	except pymongo.errors.OperationFailure as e:
		# we process index-related errors independently
		if ("E11000" in str(e)):
			properties = [(key, object[key]) for key in filter(lambda x: "$%s_" % x in str(e), object._indices)]
			raise errors.DuplicateObjectError(collection_name, properties)

		raise e

	except bson.errors.InvalidDocument as e:
		if ("too large" in str(e)):
			raise errors.DBOperationError("Object is too large to be committed")

		raise e

	logger.debug("Object %s %s in collection '%s'." % (object, verb, collection_name))

def exists (id):
	return (id in _cache)

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

def count (collection, query):
	""" Return the number of objects matching a given query in a given collection
	"""
	if (query == {}):
		cursor = connection.connection()[collection]
		return cursor.count()
	else:
		return find(collection, query, count = True)

def distinct (collection, field):
	""" Return unique values for a given field in a given collection, plus the number of objects having this value
	"""
	cursor = connection.connection()[collection]

	result = cursor.group(
		key = {field: 1},
		condition = {},
		initial = {"count": 0},
		reduce = "function (o, p) { p.count++; }"
	)

	result_ = {}
	for r in result:
		result_[r[field]] = int(r["count"])

	return result_

def list_collections (with_classes = False):
	""" Return a list of all existing collections in the database that can be
		mapped to an instance of a PersistentObject class or subclass.
	"""
	# list all collections in the database
	with connection.protect():
		collection_names = connection.connection().collection_names()

	# return collections represented by PersistentObject subclasses
	collections = []
	for collection_name in collection_names:
		if (collection_name in _classes):
			if (with_classes):
				collections.append((collection_name, _classes[collection_name]))
			else:
				collections.append(collection_name)

	return collections

def find (collection, query, find_one = False, count = False):
	""" Return objects matching a given query (expressed as a JSON object, see http://www.mongodb.org/display/DOCS/Querying), as PersistentObject instances
	"""
	cursor = connection.connection()[collection]
	query_t = type(query)

	if (query_t == str):
		try:
			query = {"_id": bson.objectid.ObjectId(query)}

		except bson.errors.InvalidId:
			raise errors.InvalidObjectOperationError("Invalid identifier: %s" % query)

	if (query_t == bson.objectid.ObjectId):
		query = {"_id": query}

	elif (query_t == dict):
		# no query argument: returns all objects in this collection
		if (query == {}):
			query = None

	elif (query != None):
		raise errors.InvalidObjectOperationError("Invalid query: %s" % query)

	logger.debug("Querying %s in collection '%s'." % (query, collection))

	if (count):
		return cursor.find(query, timeout = False).count()

	if (find_one):
		return _forge_from_entry(collection, cursor.find_one(query))
	else:
		return _forge_from_entries(collection, cursor.find(query, timeout = False))

# Forge an object from a unique entry
def _forge_from_entry (collection, entry):
	if (entry == None):
		return None

	id = entry["_id"]
	if (id in _cache):
		return _cache[id]

	# select the class for this object
	clazz = _classes[collection]

	# trick: we store a non-volatile object in the _cache dictionary so
	# that during the instanciation the identifier is present in the cache
	_cache[id] = clazz

	# instanciate this class
	instance = clazz(utils.tree.traverse(entry, lambda x: True, lambda x: str(x)))

	_cache[id] = instance
	return instance

# Forge an iterator from multiple entries
def _forge_from_entries (collection, resultset):
	if (resultset == None):
		return []
	else:
		def __generator():
			for object in resultset:
				yield _forge_from_entry(collection, object)

		return __generator()

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

def remove_object (object):
	""" Remove an object from a collection
	"""
	collection_name = object.__class__.__name__

	with connection.protect():
		connection.connection()[collection_name].remove({"_id": object["_id"]})

	del _cache[object["_id"]]

	logger.debug("Object %s was removed from collection '%s'." % (object, collection_name))

def drop_collection (collection):
	""" Drop a collection
	"""
	with connection.protect():
		connection.connection().drop_collection(collection)

	logger.debug("Collection '%s' was dropped." % collection)

def copy_database (target_db, admin_user = None, admin_password = None, force = False):
	""" Copy the current database to a new database name (see http://www.mongodb.org/display/DOCS/Clone+Database)
	"""
	with connection.protect():
		# save the current connection
		db_connection = connection.connection()
		db_connection_ = connection.connection_information()

		source_db = db_connection_["db"]
		if (source_db == target_db):
			logger.debug("Ignored request to copy '%s' into itself." % target_db)
			return

		# open a connection to the admin collection
		admin_connection = connection.connect(db = "admin", user = admin_user, password = admin_password)

		if (target_db in admin_connection.connection.database_names()):
			if (force):
				logger.debug("'%s' already exists and will be merged with content of '%s'." % (source_db, target_db))
			else:
				raise errors.DBOperationError("Unable to copy database '%s' to '%s': target already exists." % (source_db, target_db))

		# copy the database
		try:
			admin_connection.connection.copy_database(source_db, target_db)

		# restore the current connection
		finally:
			connection._connection = db_connection
			connection._connection_information = db_connection_

	logger.debug("Copy of '%s' into '%s' successful." % (source_db, target_db))

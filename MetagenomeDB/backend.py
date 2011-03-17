# backend.py: low-level interface with the MongoDB database, with on-the-fly
# instanciation of objects (with caching) from MongoDB result sets.

# Note: The term 'collection', when used in this file, refers to a MongoDB
# collection and NOT to the Collection object in objects.py

import weakref, datetime, re, logging, inspect
import pymongo, bson

import connection, errors
from sequence import Sequence
from collection import Collection
from utils import tree

__CLASSES = {
	"Sequence": Sequence,
	"Collection": Collection
}

logger = logging.getLogger("MetagenomeDB.backend")

# Object cache, as a map with weak values
__objects = weakref.WeakValueDictionary()

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Commit a CommittableObject to the database. IMPORTANT NOTE: this does not
# support concurrent modifications. I.e., if another client modifies the
# backend database after an object has been instanciated, a commit() will
# overwrite those modifications.
def commit (object):
	db = connection.connection()

	collection_name = object.__class__.__name__
	collection = db[collection_name]

	# if the collection this object belongs to doesn't exist in
	# the database, we create it with its indices (if any)
	if (not collection_name in db.collection_names()):
		msg = "Collection '%s' created" % collection_name
		if (len(object._indices) > 0):
			msg += " with indices %s" % ', '.join(["'%s'" % key for key in sorted(object._indices.keys())])

		logger.debug(msg + '.')

		for (index, is_unique) in object._indices.iteritems():
			collection.create_index(index, unique = is_unique)

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
		__objects[object_id] = object

	except pymongo.errors.OperationFailure as msg:
		if ("E11000" in str(msg)):
			properties = [(key, object[key]) for key in filter(lambda x: "$%s_" % x in str(msg), object._indices)]
			raise errors.DuplicateObjectError(collection_name, properties)
		else:
			raise errors.MetagenomeDBError("Unable to commit. Reason: %s" % msg)

	logger.debug("Object %s %s in collection '%s'." % (object, verb, collection_name))

def exists (id):
	return (id in __objects)

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Count entries in a given collection
def count (collection, query):
	if (query == {}):
		cursor = connection.connection()[collection]
		return cursor.count()
	else:
		return find(collection, query, count = True)

# Retrieve distinct values (and number of objects
# with this value) for a give field
def distinct (collection, field):
	cursor = connection.connection()[collection]

	result = cursor.group(
		key = { field: 1 },
		condition = {},
		initial = {"count": 0},
		reduce = "function (o, p) { p.count++; }"
	)

	result_ = {}
	for r in result:
		result_[r[field]] = int(r["count"])

	return result_

# Create objects from entries matching a given query, expressed as
# a JSON tree; see http://www.mongodb.org/display/DOCS/Querying
# Special keys:
#   - any '_xxx' key will be changed to '$xxx' (e.g., $where), except '_id'
#   - value for '_id' will be cast into a bson.objectid.ObjectId
def find (collection, query, find_one = False, count = False):
	cursor = connection.connection()[collection]
	query_t = type(query)

	if (query_t == str):
		try:
			query = {"_id": bson.objectid.ObjectId(query)}

		except bson.errors.InvalidId:
			raise errors.MetagenomeDBError("Invalid identifier: %s" % query)

	if (query_t == bson.objectid.ObjectId):
		query = {"_id": query}

	elif (query_t == dict):
		# no query argument: returns all objects in this collection
		if (query == {}):
			query = None

	elif (query != None):
		raise errors.MetagenomeDBError("Invalid query: %s" % query)

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
	if (id in __objects):
		return __objects[id]

	# select the class for this object
	clazz = __CLASSES[collection]

	# trick: we store a non-volatile object in the __objects dictionary so
	# that during the instanciation the identifier is present in the cache
	__objects[id] = clazz

	# instanciate this class
	instance = clazz(tree.traverse(entry, lambda x: True, lambda x: str(x)))

	__objects[id] = instance
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
	""" Remove an object from a collection.
	"""
	collection_name = object.__class__.__name__
	connection.connection()[collection_name].remove({"_id": object["_id"]})
	del __objects[object["_id"]]

	logger.debug("Object %s was removed from collection '%s'." % (object, collection_name))

def drop_collection (collection):
	""" Drop a collection.
	"""
	connection.connection().drop_collection(collection)

	logger.debug("Collection '%s' was dropped." % collection)

def list_collections (with_classes = False):
	""" Return a list of all existing collections that are
		represented by a CommittableObject subclass.
	"""
	# list all collections in the database
	collections = []
	for collection_name in connection.connection().collection_names():
		if (collection_name in __CLASSES):
			if (with_classes):
				collections.append((collection_name, __CLASSES[collection_name]))
			else:
				collections.append(collection_name)

	return collections

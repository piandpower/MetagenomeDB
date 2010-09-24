# backend.py: low-level interface with the MongoDB database, with on-the-fly
# instanciation of objects (with caching) from MongoDB result sets.

# Note: The term 'collection', when used in this file, refers to a MongoDB
# collection and NOT to the Collection object in objects.py

import weakref, datetime, re, logging
import pymongo

import connection, objects, errors
from utils import tree

logger = logging.getLogger("MetagenomeDB.backend")

# Object cache, as a map with weak values
__objects = weakref.WeakValueDictionary()

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Commit a CommittableObject to the database. IMPORTANT NOTE: this does not
# support concurrent modifications. I.e., if another client modifies the
# backend database after an object has been instanciated, a commit() will
# overwrite those modifications.
def commit (object):
	# first case: the object is already committed; we do nothing and return its identifier
	if (object._committed):
		return object["_id"]

	db = connection.connection()

	collection_name = object.__class__.__name__
	collection = db[collection_name]

	# if the collection this object belongs to doesn't exist in
	# the database, we create it with its indices (if any)
	if (not collection_name in db.collection_names()):
		msg = "Collection '%s' created" % collection_name
		if (len(object._indices) > 0):
			msg += " with indices %s." % ', '.join(["'%s'" % key for key in sorted(object._indices.keys())])

		logger.info(msg)

		for (index, is_unique) in object._indices.iteritems():
			collection.create_index(index, unique = is_unique)

	# second case: the object is not committed, and is not in the database
	if (not "_id" in object):
		object._properties["_creation_time"] = datetime.datetime.now()
		verb = "created"

	# third case: the object is not committed, but a former version exists in the database
	else:
		object._properties["_modification_time"] = datetime.datetime.now()
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
			raise errors.DuplicateObject(collection_name, properties)
		else:
			raise Exception("Unable to commit. Reason: %s" % msg)

	logger.info("Object %s %s in collection '%s'." % (object, verb, collection_name))

	return object_id

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
		initial = { "count": 0 },
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
#   - value for '_id' will be cast into a pymongo.objectid.ObjectId
def find (collection, query, find_one = False, count = False):
	cursor = connection.connection()[collection]
	query_t = type(query)

	if (query_t == str):
		try:
			query = { "_id": pymongo.objectid.ObjectId(query) }

		except pymongo.errors.InvalidId:
			raise ValueError("Invalid identifier: %s" % query)

	if (query_t == pymongo.objectid.ObjectId):
		query = { "_id": query }

	elif (query_t == dict):
		# no query argument: returns all objects in this collection
		if (query == {}):
			query = None
		else:
			query = __clean_query(query)

	elif (query != None):
		raise ValueError("Invalid query: %s" % query)

	logger.debug("Querying %s in collection '%s'." % (query, collection))

	if (count):
		return cursor.find(query).count()

	if (find_one):
		return __forge_from_entry(collection, cursor.find_one(query))
	else:
		return __forge_from_entries(collection, cursor.find(query))

# Forge an object from a unique entry
def __forge_from_entry (collection, entry):
	if (entry == None):
		return None

	id = entry["_id"]
	if (id in __objects):
		return __objects[id]

	# select the class for this object
	object = getattr(objects, collection)

	# trick: we store a non-volatile object in the __objects dictionary so
	# that during the instanciation the identifier is present in the cache
	__objects[id] = object

	# instanciate this class
	instance = object(**tree.traverse(entry, lambda x: True, lambda x: str(x)))

	__objects[id] = instance
	return instance

# Forge an iterator from multiple entries
def __forge_from_entries (collection, resultset):
	if (resultset == None):
		return []
	else:
		def __generator():
			for object in resultset:
				yield __forge_from_entry(collection, object)

		return __generator()

def __clean_query (query):
	"""
	query = tree.traverse(
		query,
		selector = lambda x: x.startswith('_'),
		key_modifier = lambda x: '$' + x[1:]
	)

	query = tree.traverse(
		query,
		selector = lambda x: (x == "$id"),
		key_modifier = lambda x: "_id",
		value_modifier = lambda x: pymongo.objectid.ObjectId(x),
	)
	"""

	query = tree.traverse(
		query,
		selector = lambda x: (x == "clazz"),
		key_modifier = lambda x: "class",
	)

	return query

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

def exists (id):
	return (id in __objects)

# Drop a whole collection, and remove any corresponding instanciated object.
def remove_all (collection):
	objects = find(collection, None)
	n_objects = find(collection, None, count = True)

	n = 0
	for object in objects:
		try:
			object.remove()
			n += 1
		except:
			continue

	if (n < n_objects):
		logger.warning("%s out of %s objects in collection '%s' were not removed." % (n_objects - n, n_objects, collection))
		return

	connection.connection().drop_collection(collection)
	logger.info("Collection '%s' dropped." % collection)

# Remove an object from the database.
def remove (object):
	if (not object.is_committed()):
		raise errors.UncommittedObject(object)

	if (has_ingoing_neighbors(object)):
		raise errors.LinkedObject(object)

	collection = object.__class__.__name__
	connection.connection()[collection].remove({ "_id": object["_id"] })

	logger.info("Object %s removed from collection '%s'." % (object, collection))

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

def has_ingoing_neighbors (object):
	if (not object.is_committed()):
		raise errors.UncommittedObject(object)

	object_id = str(object._properties["_id"])

	query = { "_relationship_with": object_id }

	for collection in connection.connection().collection_names():
		if (collection == "system.indexes"):
			continue

		if (find(collection, query, count = count) > 0):
			return True

	return False

def ingoing_neighbors (object, neighbor_collection, neighbor_filter = None, relationship_filter = None, count = False):
	if (not object.is_committed()):
		raise errors.UncommittedObject(object)

	object_id = str(object._properties["_id"])

	query = { "_relationship_with": object_id }

	if (neighbor_filter != None):
		for key in neighbor_filter:
			query[key] = neighbor_filter[key]

	if (relationship_filter != None):
		query["_relationships"] = { object_id: __clean_query(relationship_filter) }

	return find(neighbor_collection, query, count = count)

def outgoing_neighbors (object, neighbor_collection, neighbor_filter = None, relationship_filter = None, count = False):
	query = { "_id": { "$in": [pymongo.objectid.ObjectId(id) for id in object._properties["_relationship_with"]] }}

	if (neighbor_filter != None):
		for key in neighbor_filter:
			query[key] = neighbor_filter[key]

	if (relationship_filter != None):
		query["_relationships"] = { object_id: __clean_query(relationship_filter) }

	return find(neighbor_collection, query, count = count)

# forge.py: low-level interface with the MongoDB database, with on-the-fly
# instanciation of objects (with cache) from MongoDB result sets.

# Note: The term 'collection', when used in this file, refers to a MongoDB
# collection and NOT to the Collection object in objects.py

import commons, connection, objects, tree, errors
import pymongo
import weakref, datetime, re

__objects = weakref.WeakValueDictionary()

def exists (id):
	return (id in __objects)

# Drop a whole collection, and remove any corresponding instanciated object
def remove_all (collection):
	connection.connection().drop_collection(collection)

	for object in filter(lambda x: x.__class__.__name__ == collection, __objects.values()):
		object.remove()

	if (commons.debug_level > 0):
		commons.log("remove_all", "'%s' collection dropped" % collection)

# Remove an object from the database
def remove (object):
	collection = object.__class__.__name__
	connection.connection()[collection].remove({ "_id": object["_id"] })

	if (commons.debug_level > 1):
		commons.log("remove", "%s removed from '%s'" % (object, collection))

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

	else:
		raise ValueError("Invalid query: %s" % query)

	if (count):
		return cursor.find(query).count()

	if (find_one):
		return __forge_from_entry(collection, cursor.find_one(query))
	else:
		return __forge_from_entries(collection, cursor.find(query))

OUTGOING = 1
INGOING = 2

# Find neighbors of a given object
def find_neighbors (object, direction, neighbor_collection, neighbor_filter = None, relationship_filter = None, count = False):
	if (direction == OUTGOING):
		here, there = "source", "target"
	elif (direction == INGOING):
		here, there = "target", "source"
	else:
		raise ValueError("Invalid direction '%s'" % direction)

	if (not object.is_committed()):
		raise errors.UncommittedObject()

	# (1) list all candidate neighbors, based on the relationship filter only
	if (relationship_filter == None):
		relationship_filter = {}
	else:
		relationship_filter = __clean_query(relationship_filter)

	relationship_filter[here] = pymongo.dbref.DBRef(object.__class__.__name__, object["_id"])
	r = connection.connection()["Relationship"]

	candidate_neighbors = {}

	for relationship in r.find(relationship_filter):
		dbref = relationship[there]
		if (dbref.collection != neighbor_collection):
			continue

		if (dbref.id not in candidate_neighbors):
			candidate_neighbors[dbref.id] = []

		candidate_neighbors[dbref.id].append(relationship)

	# (2) filter down those eligible neighbors using the neighbor filter
	if (neighbor_filter == None):
		neighbor_filter = {}
	else:
		neighbor_filter = __clean_query(neighbor_filter)

	neighbor_filter["_id"] = { "$in": candidate_neighbors.keys() }
	n = connection.connection()[neighbor_collection]

	if (count):
		return n.find(neighbor_filter).count()

	def iterator():
		for neighbor in n.find(neighbor_filter):
			for relationship in candidate_neighbors[neighbor["_id"]]:
				yield __forge_from_entry(neighbor_collection, neighbor), __forge_from_entry("Relationship", relationship)

	return iterator()

def __clean_query (query):
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

	return query

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

def commit (object, indices):
	# first case: the object is already committed; we do nothing and return its identifier
	if (object.is_committed()):
		return object["_id"]

	db = connection.connection()

	collection_name = object.__class__.__name__
	collection = db[collection_name]

	# if the collection this object belongs to doesn't exist in
	# the database, we create it with its indices (if any)
	if (not collection_name in db.collection_names()):
		if (commons.debug_level > 0):
			msg = "'%s' collection created" % collection_name
			if (len(indexes) > 0):
				msg += " with indices %s" % ', '.join(["'%s'" % key for key in sorted(indices.keys())])

			commons.log("commit", msg)

		for (index, is_unique) in indices.iteritems():
			collection.create_index(index, unique = is_unique)

	# second case: the object is not committed, and is not in the database
	if (not "_id" in object):
		object["_creation_time"] = datetime.datetime.now()
		verb = "created"

	# third case: the object is not committed, but a former version exists in the database
	else:
		object["_modification_time"] = datetime.datetime.now()
		verb = "updated"

	try:
		object_id = collection.save(
			object.get_properties(),
			safe = True,
		)

		__objects[object_id] = object

	except pymongo.errors.OperationFailure as msg:
		if ("E11000" in str(msg)):
			keys = ','.join([object[key] for key in filter(lambda x: indices[x], indices)])

			raise errors.DuplicateObject(collection_name, keys)
		else:
			raise Exception("Unable to commit: %s" % msg)

	if (commons.debug_level > 1):
		commons.log("commit", "%s %s in collection '%s'" % (object, verb, collection_name))

	return object_id

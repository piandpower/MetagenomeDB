# forge.py: low-level interface with the MongoDB database, with on-the-fly
# instanciation of objects (with cache) from MongoDB result sets.

# Note: The term 'collection', when used in this file, refers to a MongoDB
# collection and NOT to the Collection object in objects.py

import commons, connection, objects, tree
import pymongo
import weakref, datetime

class DuplicateObject (Exception):
	pass

__objects = weakref.WeakValueDictionary()

# Drop a whole collection, and remove any corresponding instanciated object
def drop (collection):
	connection.connection().drop_collection(collection)

	for object in filter(lambda x: x.__class__.__name__ == collection, __objects.values()):
		object.remove()

	if (commons.debug_level > 0):
		commons.log("drop", "'%s' collection dropped" % collection)

# Remove an object from the database
def remove (object):
	collection = object.__class__.__name__
	connection.connection()[collection].remove({ "_id": object["_id"] })

	if (commons.debug_level > 1):
		commons.log("remove", "%s removed from '%s'" % (object, collection))

# Count entries in a given collection
def count (collection):
	cursor = connection.connection()[collection]
	return cursor.count()

# Create objects from entries matching a given query, expressed as a JSON tree
# (see http://www.mongodb.org/display/DOCS/Querying)
# Special keys:
#   - any '_xxx' key will be changed to '$xxx' (e.g., $where), except '_id'
#   - value for '_id' will be cast into a pymongo.objectid.ObjectId
def find (collection, query, find_one = False):
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
			return __forge_from_entries(collection, cursor.find())

		query = __clean_query(query)

	else:
		raise ValueError("Invalid query: %s" % query)

	if (find_one):
		return __forge_from_entry(collection, cursor.find_one(query))
	else:
		return __forge_from_entries(collection, cursor.find(query))

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

OUTGOING = 1
INGOING = 2

# Find neighbors of a given object
def neighbors (object, direction, neighbor_collection, neighbor_filter = None, relationship_filter = None):
	if (direction == OUTGOING):
		local_side, distant_side = "source", "target"

	elif (direction == INGOING):
		local_side, distant_side = "target", "source"

	else:
		raise ValueError("Invalid end '%s'" % direction)

	# list all eligible neighbors, based on the relationship filter only
	if (relationship_filter == None):
		relationship_filter = {}
	else:
		relationship_filter = __clean_query(relationship_filter)

	relationship_filter[local_side] = pymongo.dbref.DBRef(object.__class__.__name__, object["_id"])
	relationships = connection.connection()["Relationship"]

	eligible_neighbors = {}

	for relationship in relationships.find(relationship_filter):
		dbref = relationship[distant_side]
		if (dbref.collection != neighbor_collection):
			continue

		eligible_neighbors[dbref.id] = relationship

	# filter down those eligible neighbors using the neighbor filter
	if (neighbor_filter == None):
		neighbor_filter = {}
	else:
		neighbor_filter = __clean_query(neighbor_filter)

	neighbor_filter["_id"] = { "$in": eligible_neighbors.keys() }
	neighbors = connection.connection()[neighbor_collection]

	def __results():
		for neighbor in neighbors.find(neighbor_filter):
			relationship = eligible_neighbors[neighbor["_id"]]

			yield \
				__forge_from_entry(neighbor_collection, neighbor), \
				__forge_from_entry("Relationship", relationship)

	return __results()

def commit (object, indexes):
	collection = object.__class__.__name__
	db = connection.connection()

	if (not collection in db.collection_names()):
		if (commons.debug_level > 0):
			if (len(indexes) > 0):
				commons.log("commit", "'%s' collection created with indexes %s" % (collection, ', '.join(["'%s'" % key for key in sorted(indexes.keys())])))
			else:
				commons.log("commit", "'%s' collection created" % collection)

		for (index, is_unique) in indexes.iteritems():
			db[collection].create_index(index, unique = is_unique)

	# Upsert
	if (not object.is_committed()):
		assert (not "_id" in object) ###

		object["created-on"] = datetime.datetime.now()

		try:
			id = db[collection].insert(object.get_properties(), safe = True, check_keys = True)

		except pymongo.errors.OperationFailure as msg:
			if ("E11000" in str(msg)):
				raise DuplicateObject()
			else:
				raise Exception("Unable to commit: %s" % msg)

		verb = "created"

		"""
	# Update
	elif (self.__modified):
		self.__properties["last-modified-on"] = datetime.datetime.now()

		self.__modified = False

		### TO DO
		raise NotImplementedError

		verb = "updated"
		"""

	else:
		id = object["_id"]
		verb = "unchanged"

	if (commons.debug_level > 1):
		commons.log("commit", "%s %s in collection '%s'" % (object, verb, collection))

	return id

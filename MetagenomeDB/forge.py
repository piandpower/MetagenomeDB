
import connection, objects, tree
import pymongo
import weakref

__objects = weakref.WeakValueDictionary()

# Count entries in a given collection
def count (collection):
	cursor = connection.connection()[collection]
	return cursor.count()

# Create objects from entries matching a given query, expressed as a JSON tree
# (see http://www.mongodb.org/display/DOCS/Querying)
# Special keys:
#   - any '_xxx' key will be changed to '$xxx' (e.g., $where)
#   - 'id' will be changed to '_id'
def find (collection, query, find_one = False):
	cursor = connection.connection()[collection]

	# no query argument: returns all objects in this collection
	if (query == {}):
		return __forge_from_entries(collection, cursor.find())

	# change any '_xxx' field into '$xxx'
	query = tree.traverse(
		query,
		selector = lambda x: x.startswith('_'),
		key_modifier = lambda x: '$' + x[1:]
	)

	# change any 'id' into '_id'
	query = tree.traverse(
		query,
		selector = lambda x: (x == "id"),
		key_modifier = lambda x: "_id",
		value_modifier = lambda x: pymongo.objectid.ObjectId(x),
	)

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

	clazz = getattr(objects, collection)
	instance = clazz.from_dict(tree.traverse(entry, lambda x: True, lambda x: str(x)))

	__objects[id] = instance
	return instance

# Forge an iterator from multiple entries
def __forge_from_entries (collection, resultset):
	if (resultset == None):
		return []
	else:
		def generator():
			for object in resultset:
				yield __forge_from_entry(collection, object)

		return generator()

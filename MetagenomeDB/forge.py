
import connection, objects
import pymongo
import weakref

__objects = weakref.WeakValueDictionary()

def create_from_query (classname, query = None, where = None, find_one = False):
	db = connection.connection()[classname]

	if (query != None) and (type(query) == pymongo.objectid.ObjectId):
		if (query in __objects):
			return __objects[query]
		else:
			return create_from_json(classname, db.find_one({ "_id": query }))

	if (find_one):
		if (where == None):
			return create_from_json(classname, db.find_one(query))
		else:
			return create_from_json(classname, db.find_one(query).where(where))

	else:
		if (where == None):
			return create_from_resultset(classname, db.find(query))
		else:
			return create_from_resultset(classname, db.find(query).where(where))

def create_from_resultset (classname, resultset):
	if (resultset == None):
		return []
	else:
		def generator():
			for object in resultset:
				yield create_from_json(classname, object)

		return generator()

def __unicode_to_string (map):
	map_ = {}

	for key in map:
		value = map[key]
		if (type(value) == dict):
			map_[str(key)] = __unicode_to_string(value)
		else:
			map_[str(key)] = value

	return map_

def create_from_json (classname, entry):
	if (entry == None):
		return None

	id = entry["_id"]
	if (id in __objects):
		return __objects[id]

	clazz = getattr(objects, classname)
	instance = clazz.from_dict(__unicode_to_string(entry))

	__objects[id] = instance
	return instance

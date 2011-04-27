# objects.py: object representation of the MongoDB content

import backend, errors
from utils import tree
import bson
import sys, copy, logging

logger = logging.getLogger("MetagenomeDB.classes")

class MutableObject (object):
	""" MutableObject: Base object that can receive arbitrary properties.
	"""

	def __init__ (self, properties):
		""" Create a new object.

		Parameters:
			- **properties** (optional): object annotations, as a dictionary.
			  Nested properties can be expressed using dot notation or by nested
			  dictionaries.
		"""
		self._properties = tree.expand(properties)
		self._modified = False

	def get_properties (self):
		""" Return a copy of all of this object's properties, as a dictionary.

		.. seealso::
			:meth:`~MutableObject.get_property`
		"""
		return self._properties.copy()

	def get_property (self, key, default = None):
		""" Return the value for a given property.

		Parameters:
			- **key**: property to retrieve; see :doc:`annotations`.

		.. seealso::
			:meth:`~MutableObject.get_properties`
		"""
		try:
			return copy.deepcopy(self.__getitem__(key))

		except KeyError:
			return default

	def _setitem_precallback (self, key, value):
		""" Setter callback, called before the property is set or updated.

		Parameters:
			- **key**: property to set or update
			- **value**: value to be set for this property

		Return:
			- value: the value to set
		"""
		return value

	def _setitem_postcallback (self):
		""" Setter callback, called after the property has been set or updated.
		
		.. note::
			The property may not have been changed if its former value was the
			same as the new one; in this case self._modified will be set to False
		"""
		pass

	def __setitem__ (self, key, value):
		key = tree.expand_key(key)
		value = self._setitem_precallback(key, value)

		# only modify the property if the value is different from its previous one (if any)
		if (not tree.contains(self._properties, key)) or (value != tree.get(self._properties, key)):
			tree.set(self._properties, key, value)
			self._modified = True
		else:
			self._modified = False

		self._setitem_postcallback()

	def _getitem_precallback (self, key, value):
		""" Getter callback, called before the property has been returned.

		Parameters:
			- **key**: the property that has been requested
			- **value**: the value that is going to be returned

		Return:
			- value: if different from None, will be returned instead of **value**
		"""
		return None

	def __getitem__ (self, key):
		key = tree.expand_key(key)
		value = copy.deepcopy(tree.get(self._properties, key))

		value_ = self._getitem_precallback(key, value)
		return value if (value_ == None) else value_

	def _delitem_precallback (self, key):
		""" Deletion callback, called before the property is deleted.

		Parameters:
			- **key**: property to delete
		"""
		pass

	def _delitem_postcallback (self):
		""" Deletion callback, called after the property has been deleted.
		"""
		pass

	def __delitem__ (self, key):
		key = tree.expand_key(key)
		self._delitem_precallback(key)

		tree.delete(self._properties, key)
		self._modified = True

		self._delitem_postcallback()

	def __contains__ (self, key):
		key_ = tree.expand_key(key)
		return tree.contains(self._properties, key_)

class CommittableObject (MutableObject):
	""" CommittableObject: Object that can be committed to the backend database.
	"""

	def __init__ (self, indices, properties):
		""" Create a new object.

		Parameters:
			- **properties** (optional): object annotations, as a dictionary.
			  Nested properties can be expressed using dot notation or by nested
			  dictionaries.
		"""
		MutableObject.__init__(self, properties)

		# if the object is provided with an identifier,
		# we check if this identifier is present in the
		# object cache to know if it was committed.
		if ("_id" in self._properties):
			id = self._properties["_id"]

			if (type(id) == str):
				id = bson.objectid.ObjectId(id)
				self._properties["_id"] = id

			if (not backend.exists(id)):
				raise errors.InvalidObjectError("Unknown object identifier '%s'." % id)

			self._committed = True
		else:
			self._committed = False

		if (not "_relationships" in self._properties):
			self._properties["_relationship_with"] = []
			self._properties["_relationships"] = {}

		self._indices = indices
		self._indices["_relationship_with"] = False

	def _setitem_precallback (self, key, value):
		if (key[0].startswith('_')):
			raise errors.InvalidObjectOperationError("Property '%s' is reserved and cannot be modified." % '.'.join(key))

		return value

	def _setitem_postcallback (self):
		self._committed = not self._modified

	def _delitem_precallback (self, key):
		if (key[0].startswith('_')):
			raise errors.InvalidObjectOperationError("Property '%s' is reserved and cannot be modified." % '.'.join(key))

	def _delitem_postcallback (self):
		self._committed = False

	def commit (self):
		""" Commit this object to the database.

		.. note::
			- The commit will not be performed if the object has already been
			  committed once and no modification (property manipulation) has
			  been performed since then.
			- If an object already exists in the database with the same values
			  for properties flagged as unique a :class:`MetagenomeDB.errors.DuplicateObjectError`
			  exception is thrown.

		.. seealso::
			:meth:`~CommittableObject.is_committed`
		"""
		if (self._committed):
			return

		"""
		# pre-flight: if some patch needs to be applied on the object's
		# properties, we temporary store the old values
		tmp = {}
		for (key, value) in patch.iteritems():
			assert (key != "_id") ###
			tmp[key] = self._properties[key]
			self._properties[key] = value
		"""

		with errors._protect():
			backend._commit(self)

		"""
		# post-flight: we restore the object's properties, if needed
		for (key, value) in tmp.iteritems():
			self._properties[key] = value
		"""

		self._committed = True

	def is_committed (self):
		""" Test if this object has been committed to the database since
			its latest modification.

		.. seealso::
			:meth:`~CommittableObject.commit`
		"""
		return self._committed

	@classmethod
	def count (cls, filter = None):
		""" Count the number of objects of this type in the database.
		
		Parameters:
			- **filter**: filter for the objects to count (optional); see
			  :doc:`queries`.

		.. seealso::
			:meth:`~CommittableObject.find`
		"""
		return backend.count(cls.__name__, query = filter)

	@classmethod
	def distinct (cls, property):
		""" For each value found in the database for a given property, return
		the number of objects that have this value.

		Parameters:
			- **property**: property to count objects for.

		Return:
			A dictionary with all values found for this property as keys, and
			number of objects having this value as values.
		"""
		return backend.distinct(cls.__name__, property)

	@classmethod
	def find (cls, filter = None):
		""" Find all objects of this type that match a query.
		
		Parameters:
			- **filter**: filter for the objects to select (optional); see
			  :doc:`queries`.

		Return:
			A generator.

		.. seealso::
			:meth:`~CommittableObject.count`, :meth:`~CommittableObject.find_one`
		"""
		return backend.find(cls.__name__, query = filter)

	@classmethod
	def find_one (cls, filter):
		""" Find the first (or only) object of this type that match a query.

		Parameters:
			- **filter**: filter for the object to select; see :doc:`queries`.

		Return:
			An object, or None if no object found.

		.. seealso::
			:meth:`~CommittableObject.find`
		"""
		return backend.find(cls.__name__, query = filter, find_one = True)

	def _connect_to (self, target, relationship):
		""" Connect this object to another through a directed,
			annotated relationship (from this object to the target).

		.. note::
			- This method should not be called directly.
			- The target MUST have been committed at least once. However, the
			  source (i.e., the present object) can exist in memory only.
			- Throw a :class:`MetagenomeDB.errors.UncommittedObjectError` exception if the
			  target has never been committed.
		"""
		if (not "_id" in target._properties):
			raise errors.UncommittedObjectError("Cannot connect %s to %s: target has never been committed." % target)

		if (self == target):
			raise errors.InvalidObjectOperationError("Cannot connect %s to itself" % self)

		target_id = str(target._properties["_id"])

		if (relationship == None):
			relationship = {}
		else:
			relationship = tree.expand(relationship)

		# case where this object has no connection with the target yet
		if (not target_id in self._properties["_relationships"]):
			assert (not target_id in self._properties["_relationship_with"]) ###

			self._properties["_relationship_with"].append(target_id)
			self._properties["_relationships"][target_id] = [relationship]
			self._committed = False

			logger.debug("Initial relationship %s created between %s and %s." % (relationship, self, target))

		# case where this object has a connection with the target
		else:
			if (relationship in self._properties["_relationships"][target_id]):
				raise errors.DuplicateObjectError("A relationship %s already exists between objects %s and %s." % (relationship, self, target))

			self._properties["_relationships"][target_id].append(relationship)
			self._committed = False

			logger.debug("Relationship %s created between %s and %s." % (relationship, self, target))

	def _disconnect_from (self, target, relationship_filter):
		""" Disconnect this object from another.

		.. note::
			- This method should not be called directly.
			- The target MUST have been committed at least once. However, the
			  source (i.e., the present object) can exist in memory only.
			- Throw a :class:`MetagenomeDB.errors.UncommittedObjectError` exception if the
			  target has never been committed, or if attempting to use
			  **relationship_filter** while the source is not committed.
			- Throw a :class:`MetagenomeDB.errors.InvalidObjectOperationError` if the
			  source is not connected to the target.
		"""
		if (not "_id" in target._properties):
			raise errors.UncommittedObjectError("Cannot disconnect %s from %s: target has never been committed." % target)

		target_id = str(target._properties["_id"])

		if (not target_id in self._properties["_relationships"]):
			raise errors.InvalidObjectOperationError("%s is not connected to %s." % (self, target))

		# case 1: we remove all relationships between the object and target
		if (relationship_filter == None):
			del self._properties["_relationships"][target_id]
			self._properties["_relationship_with"].remove(target_id)
			self._committed = False

			logger.debug("Removed all relationships between %s and %s." % (self, target))

		# case 2: we remove all relationships matching a criteria
		else:
			if (not self._committed):
				raise errors.UncommittedObjectError("Cannot disconnect %s from %s: the source is not committed." % (self, target))

			n_relationships = len(self._properties["_relationships"][target_id])
			clazz = self.__class__.__name__
			to_remove = []

			for n in range(n_relationships):
				query = {"_id": self._properties["_id"]}

				for key, value in tree.flatten(relationship_filter).iteritems():
					query["_relationships.%s.%s.%s" % (target_id, n, key)] = value

				if (backend.find(clazz, query, count = True) == 0):
					continue

				to_remove.append(n)

			if (len(to_remove) == 0):
				raise errors.InvalidObjectOperationError("%s is not connected to %s by any relationship matching %s." % (self, target, tree.flatten(relationship_filter)))

			for n in sorted(to_remove, reverse = True):
				logger.debug("Removed relationship %s between %s and %s." % (self._properties["_relationships"][target_id][n], self, target))

				del self._properties["_relationships"][target_id][n]

			if (len(to_remove) == n_relationships):
				del self._properties["_relationships"][target_id]
				self._properties["_relationship_with"].remove(target_id)

			self._committed = False

	def _in_vertices (self, neighbor_collection, neighbor_filter = None, relationship_filter = None, count = False):
		""" List (or count) all incoming relationships between objects and this object.
		
		.. note::
			This method should not be called directly.
		"""
		# if the present object has never been committed,
		# no object can possibly be linked to it.
		if (not "_id" in self._properties):
			logger.debug("Attempt to list in-neighbors of %s while this object has never been committed." % self)
			if (count):
				return 0
			else:
				return []

		object_id = str(self._properties["_id"])

		query = {"_relationship_with": object_id}

		if (relationship_filter != None):
			query["_relationships.%s" % object_id] = {"$elemMatch": tree.flatten(relationship_filter)}

		if (neighbor_filter != None):
			neighbor_filter = tree.expand(neighbor_filter)
			for key in neighbor_filter:
				query[key] = neighbor_filter[key]

		return backend.find(neighbor_collection, query, count = count)

	def _out_vertices (self, neighbor_collection, neighbor_filter = None, relationship_filter = None, count = False):
		""" List (or count) all outgoing relationships between this object and others.
		
		.. note::
			- This method should not be called directly.
			- If relationship_filter is not None, a query is performed in the
			  database; hence, the source object must be committed. If not a
			  :class:`MetagenomeDB.errors.UncommittedObjectError` exception is thrown.
		"""
		targets = self._properties["_relationship_with"]

		if (len(targets) == 0):
			if (count):
				return 0
			else:
				return []

		# consider neighbors regardless of their relationship
		if (relationship_filter == None):
			candidates = targets

		# consider neighbors matching relationship_filter
		else:
			if (not self._committed):
				raise errors.UncommittedObjectError("Cannot list relationships from %s to other objects: the source is not committed." % self)

			candidates = []
			for target_id in targets:
				query = {
					"_id": self._properties["_id"],
					"_relationships.%s" % target_id: {"$elemMatch": tree.flatten(relationship_filter)}
				}

				if (backend.find(self.__class__.__name__, query, count = True) == 0):
					continue

				candidates.append(target_id)

		if (len(candidates) == 0):
			if (count):
				return 0
			else:
				return []

		# select candidates matching neighbor_filter
		query = {"_id": {"$in": [bson.objectid.ObjectId(id) for id in candidates]}}

		if (neighbor_filter != None):
			neighbor_filter = tree.expand(neighbor_filter)
			for key in neighbor_filter:
				query[key] = neighbor_filter[key]

		return backend.find(neighbor_collection, query, count = count)

	def has_relationships_with (self, target):
		""" Test if this object has relationship(s) with another object.
		
		Parameters:
			- **target**: object to test for the existence of relationships with.

		.. seealso::
			:meth:`~CommittableObject.list_relationships_with`
		"""
		if (not "_id" in target._properties):
			logger.debug("Attempt to test a relationship between %s and %s while the later has never been committed." % (self, target))
			return False

		return (str(target._properties["_id"]) in self._properties["_relationships"])

	def list_relationships_with (self, target):
		""" List relationship(s), if any, from this object to others.

		Parameters:
			- **target**: object to list relationships with.

		Return:
			A list.

		.. seealso::
			:meth:`~CommittableObject.has_relationships_with`
		"""
		if (not "_id" in target._properties):
			logger.debug("Attempt to list relationships between %s and %s while the later has never been committed." % (self, target))
			return []

		target_id = str(target._properties["_id"])

		if (target_id in self._properties["_relationships"]):
			return copy.deepcopy(self._properties["_relationships"][target_id])
		else:
			return []

	def remove (self):
		""" Remove this object from the database.

		.. note::
			- Relationships from and to this object are removed as well.
			- The object remains in memory, flagged as uncommitted.

		.. seealso::
			:meth:`~CommittableObject.remove_all`
		"""
		# remove all relationships with other objects
		for collection_name in backend.list_collections():
			if ("_id" in self._properties):
				for object in self._in_vertices(collection_name):
					object._disconnect_from(self, None)

			for object in self._out_vertices(collection_name):
				self._disconnect_from(object, None)

		# if the object has been committed at least once,
		if ("_id" in self._properties):
			# remove the object from the database
			with errors._protect():
				backend.remove_object(self)

			# and declare it has never having been committed
			del self._properties["_id"]

		self._committed = False

	@classmethod
	def remove_all (cls):
		""" Remove all objects of this type from the database.

		.. note::
			- Relationships from and to these objects are removed as well.
			- Instanciated objects remain in memory, flagged as uncommitted.

		.. seealso::
			:meth:`~CommittableObject.remove`
		"""
		collection_name = cls.__name__

		n_objects = backend.find(collection_name, None, count = True)
		objects = backend.find(collection_name, None)

		n = 0
		for object in objects:
			try:
				object.remove()
				n += 1
			except:
				continue

		if (n < n_objects):
			logger.warning("%s out of %s objects in collection '%s' were not removed." % (n_objects - n, n_objects, collection_name))
			return

		backend.drop_collection(cls.__name__)

	def __del__ (self):
		if (hasattr(self, "_committed") and (not self._committed)):
			logger.debug("Object %s has been destroyed without having been committed." % self)

	def __repr__ (self):
		return self.__str__()


from objects import CommittableObject, Direction
import errors
import itertools

# Collection of Sequence objects.
class Collection (CommittableObject):

	def __init__ (self, properties):
		""" Create a new Collection object.
		
		Parameters:
			- **properties**: properties of this sequence, as a dictionary.
			  Must contain at least a 'name' property, or a
			  :class:`MetagenomeDB.errors.InvalidObjectError` exception is thrown.

		.. note::
			  Collection names are unique in the database; if attempting to
			  commit a collection while another collection already exists with
			  the same name a :class:`MetagenomeDB.errors.DuplicateObjectError`
			  exception is thrown.
		"""
		if (not "name" in properties):
			raise errors.InvalidObjectError("Property 'name' is missing")

		indices = {
			"name": True,
			"class": False,
		}

		CommittableObject.__init__(self, indices, properties)

	def _delitem_precallback (self, key):
		CommittableObject._delitem_precallback(self, key)

		if (key == ("name",)):
			raise errors.InvalidObjectOperationError("Property 'name' cannot be deleted.")

	def list_sequences (self, sequence_filter = None, relationship_filter = None):
		""" List sequences this collection contains.
		
		Parameters:
			- **sequence_filter**: filter for the sequences to list (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationship linking
			  sequences to this collection (optional). See :doc:`queries`.

		.. seealso::
			:meth:`Collection.count_sequences() <MetagenomeDB.Collection.count_sequences>`
		"""
		return self._in_vertices("Sequence", sequence_filter, relationship_filter)

	def count_sequences (self, sequence_filter = None, relationship_filter = None):
		""" Count sequences this collection contains.
		
		Parameters:
			- **sequence_filter**: filter for the sequences to count (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationship linking
			  sequences to this collection (optional). See :doc:`queries`.

		.. seealso::
			:meth:`Collection.list_sequences() <MetagenomeDB.Collection.list_sequences>`
		"""
		return self._in_vertices("Sequence", sequence_filter, relationship_filter, True)

	def add_to_collection (self, collection, relationship = None):
		""" Add this collection to a (super) collection.
		
		Parameters:
			- **collection**: collection to add this collection to.
			- **relationship**: properties of the relationship from this
			  collection to **collection**, as a dictionary (optional). See
			  :doc:`annotations`.

		.. note::
			- If **collection** has never been committed to the database a
			  :class:`MetagenomeDB.errors.UncommittedObjectError` is thrown.
			- This collection will need to be committed to the database for the
			  information about its relationship to **collection** to be stored
			  and queried. See :doc:`relationships`.

		.. seealso::
			:meth:`Collection.remove_from_collection() <MetagenomeDB.Collection.remove_from_collection>`
		"""
		if (not isinstance(collection, Collection)):
			raise ValueError("The 'collection' parameter must be a Collection object.")

		self._connect_to(collection, relationship)

	def remove_from_collection (self, collection, relationship_filter = None):
		""" Remove this collection from another (super) collection.
		
		Parameters:
			- **collection**: collection to remove this collection from.
			- **relationship_filter**: relationships to remove (optional).
			  If none provided, all relationships linking this collection
			  to **collection** are removed. See :doc:`queries`.

		.. note::
			- If this collection and **collection** have no relationship, a
			  :class:`MetagenomeDB.errors.InvalidObjectOperationError` exception is thrown. 
			- If this collection is not committed and **relationship_filter** is
			  set a :class:`MetagenomeDB.errors.UncommittedObjectError` exception
			  is thrown. See :doc:`relationships`.

		.. seealso::
			:meth:`Collection.add_to_collection() <MetagenomeDB.Collection.add_to_collection>`
		"""
		if (not isinstance(collection, Collection)):
			raise ValueError("The 'collection' parameter must be a Collection object.")

		self._disconnect_from(collection, relationship_filter)

	def list_super_collections (self, collection_filter = None, relationship_filter = None):
		""" List all collections this collection is linked to.

		Parameters:
			- **collection_filter**: filter for the super-collections (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationships linking this
			  collection to super-collections (optional). See :doc:`queries`.

		.. note::
			- If this collection is not committed and **relationship_filter** is
			  set a :class:`MetagenomeDB.errors.UncommittedObjectError` exception
			  is thrown. See :doc:`relationships`.

		.. seealso::
			:meth:`Collection.count_super_collections() <MetagenomeDB.Collection.count_super_collections>`,
			:meth:`Collection.list_sub_collections() <MetagenomeDB.Collection.list_sub_collections>`,
			:meth:`Collection.count_sub_collections() <MetagenomeDB.Collection.count_sub_collections>`
		"""
		return self.list_related_collections(Direction.OUTGOING, collection_filter, relationship_filter)

	def count_super_collections (self, collection_filter = None, relationship_filter = None):
		""" Count all collections this collection is linked to.

		Parameters:
			- **collection_filter**: filter for the super-collections (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationships linking this
			  collection to super-collections (optional). See :doc:`queries`.

		.. note::
			- If this collection is not committed and **relationship_filter** is
			  set a :class:`MetagenomeDB.errors.UncommittedObjectError` exception
			  is thrown. See :doc:`relationships`.

		.. seealso::
			:meth:`Collection.list_super_collections() <MetagenomeDB.Collection.list_super_collections>`,
			:meth:`Collection.list_sub_collections() <MetagenomeDB.Collection.list_sub_collections>`,
			:meth:`Collection.count_sub_collections() <MetagenomeDB.Collection.count_sub_collections>`
		"""
		return self.count_related_collections(Direction.OUTGOING, collection_filter, relationship_filter)

	def list_sub_collections (self, collection_filter = None, relationship_filter = None):
		""" List all collections that are linked to this collection.

		Parameters:
			- **collection_filter**: filter for the sub-collections (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationships linking
			  sub-collections to this collection (optional). See :doc:`queries`.

		.. seealso::
			:meth:`Collection.count_sub_collections() <MetagenomeDB.Collection.count_sub_collections>`,
			:meth:`Collection.list_super_collections() <MetagenomeDB.Collection.list_super_collections>`,
			:meth:`Collection.count_super_collections() <MetagenomeDB.Collection.count_super_collections>`
		"""
		return self.list_related_collections(Direction.INGOING, collection_filter, relationship_filter)

	def count_sub_collections (self, collection_filter = None, relationship_filter = None):
		""" Count all collections that are linked to this collection.

		Parameters:
			- **collection_filter**: filter for the sub-collections (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationships linking
			  sub-collections to this collection (optional). See :doc:`queries`.

		.. seealso::
			:meth:`Collection.list_sub_collections() <MetagenomeDB.Collection.list_sub_collections>`,
			:meth:`Collection.list_super_collections() <MetagenomeDB.Collection.list_super_collections>`,
			:meth:`Collection.count_super_collections() <MetagenomeDB.Collection.count_super_collections>`
		"""
		return self.count_related_collections(Direction.INGOING, collection_filter, relationship_filter)

	def list_related_collections (self, direction = Direction.BOTH, collection_filter = None, relationship_filter = None):
		""" List all collections this collection is linked to, or have links to it.

		Parameters:
			- `direction`: direction of the relationship (optional). If set to
			  ``Direction.INGOING``, will list collections that are linked to
			  this collection (i.e., sub-collections). If set to
			  ``Direction.OUTGOING``, will list collections this collection is
			  linked to (i.e., super-collections). If set to ``Direction.BOTH``
			  (default), all neighboring collections are listed. See
			  :doc:`relationships`.
			- `collection_filter`: filter for the collections to list (optional).
			  See :doc:`queries`.
			- `relationship_filter`: filter for the relationships between this
			  collection and neighbor collections (optional). See :doc:`queries`.

		.. note::
			- If **direction** is set to ``Direction.BOTH`` or ``Direction.OUTGOING``,
			  **relationship_filter** is set and this collection is not committed,
			  a :class:`MetagenomeDB.errors.UncommittedObjectError` exception is thrown.

		.. seealso::
			:meth:`Collection.count_related_collections() <MetagenomeDB.Collection.count_related_collections>`
		"""
		collections = []

		if Direction._has_ingoing(direction):
			collections.append(self._in_vertices("Collection", collection_filter, relationship_filter))

		if Direction._has_outgoing(direction):
			collections.append(self._out_vertices("Collection", collection_filter, relationship_filter))

		return itertools.chain(*collections)

	def count_related_collections (self, direction = Direction.BOTH, collection_filter = None, relationship_filter = None):
		""" Count all collections this collection is linked to, or have links to it.

		Parameters:
			- `direction`: direction of the relationship (optional). If set to
			  ``Direction.INGOING``, will count collections that are linked to
			  this collection (i.e., sub-collections). If set to
			  ``Direction.OUTGOING``, will count collections this collection is
			  linked to (i.e., super-collections). If set to ``Direction.BOTH``
			  (default), all neighboring collections are counted. See
			  :doc:`relationships`.
			- `collection_filter`: filter for the collections to count (optional).
			  See :doc:`queries`.
			- `relationship_filter`: filter for the relationships between this
			  collection and neighbor collections (optional). See :doc:`queries`.

		.. note::
			- If **direction** is set to ``Direction.BOTH`` or ``Direction.OUTGOING``,
			  **relationship_filter** is set and this collection is not committed,
			  a :class:`MetagenomeDB.errors.UncommittedObjectError` exception is thrown.

		.. seealso::
			:meth:`Collection.list_related_collections() <MetagenomeDB.Collection.list_related_collections>`
		"""
		collections_c = 0

		if Direction._has_ingoing(direction):
			collections_c += self._in_vertices("Collection", collection_filter, relationship_filter, count = True)

		if Direction._has_outgoing(direction):
			collections_c += self._out_vertices("Collection", collection_filter, relationship_filter, count = True)

		return collections_c

	def __str__ (self):
		return "<Collection id:%s name:'%s' state:'%s'>" % (
			self.get_property("_id", "none"),
			self["name"],
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

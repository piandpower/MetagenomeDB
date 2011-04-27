
from classes import CommittableObject
import errors
import zlib, itertools

### needed for list_top_collections(); should probably be not here
from utils import tree
import backend
###

class Direction:
	INGOING, SUB = 1, 1
	OUTGOING, SUPER = 2, 2
	BOTH = 0

	@classmethod
	def _validate (cls, value):
		value_t = type(value)

		if (value_t == int):
			if (value < 0) or (value > 2):
				raise ValueError("Invalid direction parameter '%s'" % value)
			return value

		if (value_t == str):
			try:
				return {
					"ingoing": 1,
					"outgoing": 2,
					"both": 0
				}[value.lower().strip()]
			except:
				raise ValueError("Invalid direction parameter '%s'" % value)

		raise ValueError("Invalid direction parameter '%s'" % value)

	@classmethod
	def _has_ingoing (cls, value):
		value = Direction._validate(value)
		return (value == Direction.INGOING) or (value == Direction.BOTH)

	@classmethod
	def _has_outgoing (cls, value):
		value = Direction._validate(value)
		return (value == Direction.OUTGOING) or (value == Direction.BOTH)

# Sequence object.
class Sequence (CommittableObject):

	__MAX_UNCOMPRESSED_SEQUENCE_SIZE = 1000000
	__MAX_COMPRESSED_SEQUENCE_SIZE = 1000000

	def __init__ (self, properties):
		""" Create a new Sequence object.
		
		Parameters:
			- **properties**: properties of this sequence, as a dictionary.
			  Must contain at least a 'name' and 'sequence' property, or a
			  :class:`MetagenomeDB.errors.InvalidObjectError` exception is thrown.
			  A 'length' property is automatically calculated and would overwrite
			  any such property if provided.

		.. note::
			The 'name' property is unique within a collection, but not across
			the whole database. It means that two sequences with the same name
			can coexist in the database as long as they belong to two different
			collections (or if they are not related to any collection).
		"""
		if (not "name" in properties):
			raise errors.InvalidObjectError("Property 'name' is missing")

		if (not "sequence" in properties):
			raise errors.InvalidObjectError("Property 'sequence' is missing")

		sequence, length = Sequence._process_sequence(properties["sequence"])

		properties["sequence"] = sequence
		properties["length"] = length

		indices = {
			"name": False,
			"length": False,
			"class": False,
		}

		CommittableObject.__init__(self, indices, properties)

	@classmethod
	def _process_sequence (self, value):
		# storing the sequence as an uncompressed string
		if (len(value) <= Sequence.__MAX_UNCOMPRESSED_SEQUENCE_SIZE):
			return value, len(value)
	
		sequence, crc = zlib.compress(value, 9), zlib.crc32(value)

		# storing the sequence as a compressed string
		if (len(sequence) <= Sequence.__MAX_COMPRESSED_SEQUENCE_SIZE):
			return {"data": sequence, "crc": crc}, len(value)

		# storing the sequence as a blob
		handle = None

		raise NotImplementedError() ####

		return {"handle": handle, "crc": crc}, len(value)

	def _setitem_precallback (self, key, value):
		CommittableObject._setitem_precallback(self, key, value)

		if (key == ("sequence",)):
			sequence, length = Sequence._process_sequence(value)
			self._properties["length"] = length
			return sequence

		if (key == ("length",)):
			raise errors.InvalidObjectOperationError("Property 'length' is tied to 'sequence' and cannot be changed directly.")

		return value

	def _getitem_precallback (self, key, value):
		if (key == ("sequence",)):
			if (type(value) in (str, unicode)):
				return value

			if ("data" in value):
				sequence = zlib.decompress(value["data"])
				if (zlib.crc32(sequence) != value["crc"]):
					raise errors.InvalidObjectError("Sequence information has been corrupted.")

				return sequence

			if ("handle" in value):
				pass

			raise errors.InvalidObjectError("Invalid value for 'sequence' property.")

	def _delitem_precallback (self, key):
		CommittableObject._delitem_precallback(self, key)

		if (key == ("name",)):
			raise errors.InvalidObjectOperationError("Property 'name' cannot be deleted.")

		if (key == ("sequence",)):
			raise errors.InvalidObjectOperationError("Property 'sequence' cannot be deleted.")

		if (key == ("length",)):
			raise errors.InvalidObjectOperationError("Property 'length' cannot be deleted.")

	def add_to_collection (self, collection, relationship = None):
		""" Add this sequence to a collection.

		Parameters:
			- **collection**: collection to add this sequence to.
			- **relationship**: properties of the relationship linking this
			  sequence to **collection**, as a dictionary (optional). See
			  :doc:`annotations`.

		.. note::
			- If the collection already contains a sequence with the same name
			  a :class:`MetagenomeDB.errors.DuplicateObjectError` exception is thrown.
			- If the collection has never been committed to the database a
			  :class:`MetagenomeDB.errors.UncommittedObjectError` is thrown.
			- This sequence will need to be committed to the database for the
			  information about its relationship to **collection** to be stored
			  and queried. See :doc:`relationships`.

		.. seealso::
			:meth:`Sequence.remove_from_collection() <MetagenomeDB.Sequence.remove_from_collection>`
		"""
		if (not isinstance(collection, Collection)):
			raise ValueError("The 'collection' parameter must be a Collection object.")

		if (collection.count_sequences({"name": self["name"]}) > 0):
			raise errors.DuplicateObjectError(
				self.__class__.__name__,
				(("name", self["name"]),),
				"A sequence with name '%s' already exists in collection '%s'." % (self["name"], collection["name"])
			)

		self._connect_to(collection, relationship)

	def remove_from_collection (self, collection, relationship_filter = None):
		""" Remove this sequence from a collection.
		
		Parameters:
			- **collection**: collection to remove this collection from.
			- **relationship_filter**: relationships to remove (optional).
			  If none provided, all relationships linking this sequence to
			  **collection** are removed. See :doc:`queries`.

		.. note::
			- If this sequence and **collection** have no relationship, a
			  :class:`MetagenomeDB.errors.InvalidObjectOperationError` exception is thrown. 
			- If this sequence is not committed and **relationship_filter** is
			  set a :class:`MetagenomeDB.errors.UncommittedObjectError` exception
			  is thrown. See :doc:`relationships`.

		.. seealso::
			:meth:`Sequence.add_to_collection() <MetagenomeDB.Sequence.add_to_collection>`
		"""
		if (not isinstance(collection, Collection)):
			raise ValueError("The 'collection' parameter must be a Collection object.")

		self._disconnect_from(collection, relationship_filter)

	def list_collections (self, collection_filter = None, relationship_filter = None):
		""" List collections this sequence is linked to.
		
		Parameters:
			- **collection_filter**: filter for the collections (optional). See
			  :doc:`queries`.
			- **relationship_filter**: filter for the relationship linking this
			  sequence to collections (optional). See :doc:`queries`.
		
		.. note::
			- If this sequence is not committed and **relationship_filter** is
			  set a :class:`MetagenomeDB.errors.UncommittedObjectError` exception
			  is thrown. See :doc:`relationships`.

		.. seealso::
			:meth:`Sequence.count_collections() <MetagenomeDB.Sequence.count_collections>`
		"""
		return self._out_vertices("Collection", collection_filter, relationship_filter)

	def count_collections (self, collection_filter = None, relationship_filter = None):
		""" Count collections this sequence is linked to.
		
		Parameters:
			- **collection_filter**: filter for the collections (optional). See :doc:`queries`.
			- **relationship_filter**: filter for the relationship linking this
			  sequence to collections (optional). See :doc:`queries`.
		
		.. note::
			- If this sequence is not committed and **relationship_filter** is
			  set a :class:`MetagenomeDB.errors.UncommittedObjectError` exception
			  is thrown. See :doc:`relationships`.

		.. seealso::
			:meth:`Sequence.list_collections() <MetagenomeDB.Sequence.list_collections>`
		"""
		return self._out_vertices("Collection", collection_filter, relationship_filter, True)

	def list_top_collections (self, collection_filter = None):
		""" List top collections this sequence is linked to.
		
		Explore all collections this sequence belong to, and the collection these
		collections belong to (if any) until reaching the 'top' collections which
		belong to no other collection.

		Parameters:
			- **collection_filter**: filter for the top collections (optional). See :doc:`queries`.
		"""
		# we list all top collections
		top, visited = {}, {}
		def crawl (collection):
			if (collection.count_super_collections() == 0):
				top[collection] = True
			else:
				for super_collection in collection.list_super_collections():
					if (super_collection in visited):
						continue

					crawl(super_collection)
					visited[super_collection] = True

		for collection in self.list_collections():
			crawl(collection)

		# we then filter these collections, if needed
		if (collection_filter == None):
			return sorted(top.keys())

		else:
			query = {"_id": {"$in": [collection["_id"] for collection in top]}}

			collection_filter = tree.expand(collection_filter)
			for key in collection_filter:
				query[key] = collection_filter[key]

			return backend.find("Collection", query)

	def relate_to_sequence (self, sequence, relationship = None):
		""" Link this sequence to another sequence.
		
		Parameters:
			- **sequence**: sequence to link this sequence to.
			- **relationship**: description of the relationship linking this
			  sequence to **sequence**, as a dictionary (optional).
		
		.. note::
			- If **sequence** has never been committed to the database a
			  :class:`MetagenomeDB.errors.UncommittedObjectError` is thrown.
			- This sequence will need to be committed to the database for the
			  information about its relationship to **sequence** to be stored
			  and queried. See :doc:`relationships`.

		.. seealso::
			:meth:`Sequence.dissociate_from_sequence() <MetagenomeDB.Sequence.dissociate_from_sequence>`
		"""
		if (not isinstance(sequence, Sequence)):
			raise ValueError("The 'sequence' parameter must be a Sequence object.")

		self._connect_to(sequence, relationship)

	def dissociate_from_sequence (self, sequence, relationship_filter = None):
		""" Remove links between this sequence and another sequence.

		Parameters:
			- **sequence**: sequence to unlink this sequence from.
			- **relationship_filter**: relationships to remove (optional).
			  If none provided, all relationships from this sequence
			  to **sequence** are removed. See :doc:`queries`.

		.. note::
			- If this sequence and **sequence** have no relationship, a
			  :class:`MetagenomeDB.errors.InvalidObjectOperationError` exception is thrown. 
			- If this sequence is not committed and **relationship_filter** is
			  set a :class:`MetagenomeDB.errors.UncommittedObjectError` exception
			  is thrown. See :doc:`relationships`.

		.. seealso::
			:meth:`Sequence.relate_to_sequence() <MetagenomeDB.Sequence.relate_to_sequence>`
		"""
		if (not isinstance(sequence, Sequence)):
			raise ValueError("The 'sequence' parameter must be a Sequence object.")

		self._disconnect_from(sequence, relationship_filter)

	def list_related_sequences (self, direction = Direction.BOTH, sequence_filter = None, relationship_filter = None):
		""" List sequences this sequence is related to.
		
		Parameters:
			- **direction**: direction of the relationship (optional). If set to
			  ``Direction.INGOING``, will list sequences that are linked to the
			  present sequence. If set to ``Direction.OUTGOING``, will list
			  sequences this sequence is linked to. If set to ``Direction.BOTH``
			  (default), both neighboring sequences are listed. See
			  :doc:`relationships`.
			- **sequence_filter**: filter for the sequences to list (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationship between this
			  sequence and neighboring sequences (optional). See :doc:`queries`.

		.. note::
			- If **direction** is set to ``Direction.BOTH`` or ``Direction.OUTGOING``,
			  **relationship_filter** is set and this sequence is not committed,
			  a :class:`MetagenomeDB.errors.UncommittedObjectError` exception is thrown.

		.. seealso::
			:meth:`Sequence.count_related_sequences() <MetagenomeDB.Sequence.count_related_sequences>`
		"""
		related_sequences = []

		if Direction._has_ingoing(direction):
			related_sequences.append(self._in_vertices("Sequence", sequence_filter, relationship_filter))

		if Direction._has_outgoing(direction):
			related_sequences.append(self._out_vertices("Sequence", sequence_filter, relationship_filter))

		return itertools.chain(*related_sequences)

	def count_related_sequences (self, direction = Direction.BOTH, sequence_filter = None, relationship_filter = None):
		""" Count sequences this sequence is related to.
		
		Parameters:
			- **direction**: direction of the relationship (optional). If set to
			  ``Direction.INGOING``, will count sequences that are linked to 
			  this sequence. If set to ``Direction.OUTGOING``, will count
			  sequences this sequence is linked to. If set to ``Direction.BOTH``
			  (default), all neighboring sequences are counted. See
			  :doc:`relationships`
			- **sequence_filter**: filter for the sequences to count (optional).
			  See :doc:`queries`.
			- **relationship_filter**: filter for the relationship between this
			  sequence and neighboring sequences (optional). See :doc:`queries`.

		.. note::
			- If **direction** is set to ``Direction.BOTH`` or ``Direction.OUTGOING``,
			  **relationship_filter** is set and this sequence is not committed,
			  a :class:`MetagenomeDB.errors.UncommittedObjectError` exception is thrown.

		.. seealso::
			:meth:`Sequence.list_related_sequences() <MetagenomeDB.Sequence.list_related_sequences>`
		"""
		related_sequences_c = 0

		if Direction._has_ingoing(direction):
			related_sequences_c += self._in_vertices("Sequence", sequence_filter, relationship_filter, count = True)

		if Direction._has_outgoing(direction):
			related_sequences_c += self._out_vertices("Sequence", sequence_filter, relationship_filter, count = True)

		return related_sequences_c

	def __str__ (self):
		return "<Sequence id:%s name:'%s' length:%s state:'%s'>" % (
			self.get_property("_id", "none"),
			self["name"],
			self["length"],
			{True: "committed", False: "uncommitted"}[self.is_committed()],
		)

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

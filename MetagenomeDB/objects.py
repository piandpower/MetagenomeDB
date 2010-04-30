# objects.py: abstract representation of the MongoDB database content as
# Collection, Sequence and Relationship objects.

# TODO: think about the best strategy to remove objects that are linked

import commons, forge, base
import pymongo

class Collection (base.Object):
	def __init__ (self, **properties):
		if (not "name" in properties):
			raise ValueError("Mandatory property 'name' is missing")

		super(Collection, self).__init__(properties, {
			"name": True,
			"class": False,
		})

	# Return collections this collection is part of.
	# - collection_filter: collection filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_supercollections (self, collection_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.OUTGOING, "Collection", collection_filter, relationship_filter)

	# Return collections that are part of this collection.
	# - collection_filter: collection filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_subcollections (self, collection_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.INGOING, "Collection", collection_filter, relationship_filter)

	# Return sequences that are part of this collection.
	# - sequence_filter: sequence filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_sequences (self, sequence_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.INGOING, "Sequence", sequence_filter, relationship_filter)

	# Remove this collection from the database.
	# - remove_sequences: if True, remove also the sequences that belong to this collection
	# TODO: allow the removal of super- and sub-collections
	def remove (self, remove_sequences = False):
		if (remove_sequences):
			for sequence, relationship in self.get_sequences():
				relationship.remove(remove_source = True)

		super(Collection, self).remove()

	def __str__ (self):
		return "<Collection id:%s name:'%s'>" % (self.get_property("_id", "(uncommitted)"), self["name"])

class Sequence (base.Object):
	def __init__ (self, **properties):
		if (not "name" in properties):
			raise ValueError("Mandatory property 'name' is missing")

		if (not "sequence" in properties):
			raise ValueError("Mandatory property 'sequence' is missing")
	
		# TODO: Check the sequence

		if (not "length" in properties):
			properties["length"] = len(properties["sequence"])

		super(Sequence, self).__init__(properties, {
			"name": False,
			"length": False,
		})

	# Return collections this sequence is part of.
	# - collection_filter: collection filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_collections (self, collection_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.OUTGOING, "Collection", collection_filter, relationship_filter)

	# Return sequences this sequence refers to.
	# - sequence_filter: sequence filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_refereed_sequences (self, sequence_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.OUTGOING, "Sequence", sequence_filter, relationship_filter)

	# Return sequences referring this sequence.
	# - sequence_filter: sequence filter, expressed as a nested dictionary
	# - relationship_filter: relationship filter, expressed as a nested dictionary 
	def get_referring_sequences (self, sequence_filter = None, relationship_filter = None):
		return self.get_neighbors(forge.INGOING, "Sequence", sequence_filter, relationship_filter)

	def __str__ (self):
		return "<Sequence id:%s name:'%s' len:%s>" % (self.get_property("_id", "(uncommitted)"), self["name"], self["length"])

class Relationship (base.Object):
	def __init__ (self, **properties):
		if (not "source" in properties):
			raise ValueError("Mandatory property 'source' is missing")

		properties["source"] = Relationship.__validate(properties["source"], "source")

		if (not "target" in properties):
			raise ValueError("Mandatory property 'target' is missing")

		properties["target"] = Relationship.__validate(properties["target"], "target")

		if (not "type" in properties):
			raise ValueError("Mandatory property 'type' is missing")

		super(Relationship, self).__init__(properties, {
			"source": False,
			"target": False,
			"type": False,
		})

	# Validate objects provided as either source or target
	@classmethod
	def __validate (cls, object, side):
		if (isinstance(object, pymongo.dbref.DBRef)) and (object.collection in ("Collection", "Sequence")):
			return forge.find(object.collection, object.id, True)

		elif (isinstance(object, Collection) or isinstance(object, Sequence)):
			return object

		else:
			raise ValueError("Invalid value for '%s': must be a Collection or Sequence object" % side)

	def __setitem__ (self, key, value):
		if (key in ("source", "target")):
			Relationship.__validate(value, key)

		super(Relationship, self).__setitem__(key, value)

	# Return the collection or sequence declared as the source of this relationship.
	def get_source (self):
		return self["source"]

	# Return the collection or sequence declared as the target of this relationship.
	def get_target (self):
		return self["target"]

	def commit (self):
		source, target = self["source"], self["target"]

		source.commit()
		target.commit()

		super(Relationship, self).commit(
			source = pymongo.dbref.DBRef(source.__class__.__name__, source["_id"]),
			target = pymongo.dbref.DBRef(target.__class__.__name__, target["_id"])
		)

	# Remove this relationship from the database.
	# - remove_source: if True, remove also the source object
	# - remove_target: if True, remove also the target object
	def remove (self, remove_source = False, remove_target = False):
		if (remove_source):
			self["source"].remove()

		if (remove_target):
			self["target"].remove()

		super(Relationship, self).remove()

	def __str__ (self):
		return "<Relationship id:%s source:%s %s target:%s>" % (self.get_property("_id", "(uncommitted)"), self["source"], self["type"], self["target"])

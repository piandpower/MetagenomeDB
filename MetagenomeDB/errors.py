
# Base class for all MetagenomeDB exceptions.
class MetagenomeDBError (Exception):
	pass

class ConnectionError (MetagenomeDBError):
	def __init__ (self, database, host, port, message):
		self.database = database
		self.host = host
		self.port = port
		self.message = str(message)

	def __str__ (self):
		return "Unable to connect to database '%s' on %s:%s. Reason: %s" % (self.database, self.host, self.port, self.message)

class DuplicateObject (MetagenomeDBError):
	def __init__ (self, collection, properties):
		self.collection = collection
		self.properties = properties

	def __str__ (self):
		return "An object of type '%s' with propert%s %s already exists." % (
			self.collection,
			{ True: "ies", False: "y" }[len(self.properties) > 1],
			', '.join(["'%s' = '%s'" % property for property in self.properties])
		)

# Exception thrown when an object is removed from the database or its
# relationships are explored without this object having been committed.
class UncommittedObject (MetagenomeDBError):
	pass

# Exception thrown when an object is created with incorrect initial parameters.
class MalformedObject (MetagenomeDBError):
	pass

# Exception thrown when an object is removed while having other objects
# maintaining relationships to it.
class LinkedObject (MetagenomeDBError):
	pass

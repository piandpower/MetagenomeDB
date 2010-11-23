
class MetagenomeDBError (Exception):
	""" Base class for all MetagenomeDB exceptions.
	"""
	pass

class ConnectionError (MetagenomeDBError):
	""" Exception that is raised when failing to connect to a MongoDB server.
	"""
	def __init__ (self, database, host, port, message):
		self.database = database
		self.host = host
		self.port = port
		self.message = str(message)

	def __str__ (self):
		return "Unable to connect to database '%s' on %s:%s. Reason: %s" % (self.database, self.host, self.port, self.message)

class DuplicateObjectError (MetagenomeDBError):
	""" Exception that is raised when attempting to add an object in the
		database while a formerly imported object already exists with the
		same values for one or more unique properties.
	"""
	def __init__ (self, object_type, duplicate_properties, msg = None):
		self.object_type = object_type
		self.duplicate_properties = duplicate_properties

		if (msg == None):
			self.msg = "An object of type '%s' with propert%s %s already exists in the database." % (
				self.object_type,
				{True: "ies", False: "y"}[len(self.duplicate_properties) > 1],
				', '.join(["'%s' and value '%s'" % property for property in self.duplicate_properties])
			)
		else:
			self.msg = msg

	def __str__ (self):
		return self.msg

class UncommittedObjectError (MetagenomeDBError):
	""" Exception thrown when an operation is performed on an uncommitted object
		that requires this object to be committed.
	"""
	pass

class InvalidObjectError (MetagenomeDBError):
	""" Exception thrown when an object is created with incorrect initial parameters.
	"""
	pass

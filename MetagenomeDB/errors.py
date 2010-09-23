
class ConnectionError (Exception):
	def __init__ (self, database, host, port, message):
		self.database = database
		self.host = host
		self.port = port
		self.message = str(message)

	def __str__ (self):
		return "Unable to connect to database '%s' on %s:%s. Reason: %s" % (self.database, self.host, self.port, self.message)

class DuplicateObject (Exception):
	def __init__ (self, collection, properties):
		self.collection = collection
		self.properties = properties

	def __str__ (self):
		return "An object of type '%s' with propert%s %s already exists" % (
			self.collection,
			{ True: "ies", False: "y" }[len(self.properties) > 1],
			', '.join(["%s = '%s'" % property for property in self.properties])
		)

class UncommittedObject (Exception):
	def __init__ (self, name):
		self.name = name

	def __str__ (self):
		return self.name

class MalformedObject (Exception):
	def __init__ (self, msg):
		self.msg = msg

	def __str__ (self):
		return self.msg

class ConnectionError (Exception):
	def __init__ (self, database, host, port, message):
		self.database = database
		self.host = host
		self.port = port
		self.message = str(message)

	def __str__ (self):
		return "Unable to connect to database '%s' on %s:%s. Reason: %s" % (self.database, self.host, self.port, self.message)

class DuplicateObject (Exception):
	def __init__ (self, collection, key):
		self.collection = collection
		self.key = key

	def __str__ (self):
		return "An object of type '%s' with key '%s' already exists" % (self.collection, self.key)

class UncommittedObject (Exception):
	def __init__ (self, name):
		self.name = name

	def __str__ (self):
		return self.msg

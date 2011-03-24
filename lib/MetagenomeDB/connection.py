
import os, logging, ConfigParser, copy
import pymongo
import errors

logger = logging.getLogger("MetagenomeDB.connection")

__connection = None
__connection_info = {}

def connect (host = None, port = None, db = None, user = None, password = None):
	""" Open a connection to a MongoDB database.

	Parameters:
		- **host**: host of the MongoDB server (optional). Default: 'localhost'
		- **port**: port of the MongoDB server (optional). Default: 27017
		- **db**: database within the MongoDB server (optional). Default:
		  'MetagenomeDB'
		- **user**: user for a secured MongoDB connection (optional)
		- **password**: password for a secured MongoDB connection (optional)
	
	.. note::
		If a value is not provided for any of these parameters, an attempt will
		be made to read it from a ~/.MetagenomeDB file. If this attempt fail
		(because the file doesn't exists or it doesn't contain value for this
		parameter), then the default value is used.
	"""

	# test if a ~/.MetagenomeDB file is present
	config_parser = ConfigParser.RawConfigParser()
	config_fn = os.path.expanduser(os.path.join("~", ".MetagenomeDB"))
	has_config = (config_parser.read(config_fn) != [])

	def get (key, value, default):
		# case 1: the user provided a value
		if (value != None):
			return value

		# case 2: the user didn't provide a value, but one exists in ~/.MetagenomeDB
		if (has_config):
			try:
				value = config_parser.get("connection", key)
				logger.debug("Connection parameter '%s' read from %s (value: '%s')" % (key, config_fn, value))
				return value

			except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
				pass

		# case 3: no value can be found, and the default is used
		logger.debug("Connection parameter '%s' set to default value '%s'" % (key, default))
		return default

	host = get("host", host, "localhost")
	port = int(get("port", port, 27017))
	db = get("db", db, "MetagenomeDB")
	user = get("user", user, '')
	password = get("password", password, '')

	url = "%s:%s/%s" % (host, port, db)
	if (user != ''):
		url = "%s:%s@%s" % (user, password, url)

	logger.debug("Connection requested to %s" % url)

	try:
		connection = pymongo.connection.Connection(host, port)
		database = pymongo.database.Database(connection, db)

		# use credentials, if any
		if (user != ''):
			success = database.authenticate(user, password)
			if (not success):
				raise errors.ConnectionError(db, host, port, "Authentication failed (user: '%s', password: '%s')." % (user, password))

			logger.debug("Authenticated as '%s'." % user)

		database.collection_names()

	except pymongo.errors.ConnectionFailure as msg:
		# the mongodb server couldn't be located
		raise errors.ConnectionError(db, host, port, msg)

	except pymongo.errors.OperationFailure as msg:
		if ("database error: unauthorized" in str(msg)):
			msg = "Incorrect credentials or database doesn't exist."

		raise errors.ConnectionError(db, host, port, msg)

	logger.debug("Connected to %s" % url)

	global __connection
	__connection = database

	global __connection_info
	__connection_info = {
		"host": host,
		"port": port,
		"db": db,
		"user": user,
		"password": password
	}

	return __connection

def connection():
	""" Obtain a connection object to a MongoDB database. If no connection exists, connect() is called without argument.
	
	.. note::
		connection() is a singleton; i.e., any call to this function will
		return the same connection object.
	"""
	logger.debug("Connection requested by PID %s" % os.getpid())

	if (__connection == None):
		connect()

	return __connection

def connection_information():
	""" Obtain information about the connection to MongoDB, as a dictionary.
	"""
	if (__connection == None):
		connect()

	return copy.deepcopy(__connection_info)

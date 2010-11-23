
import os, sys, ConfigParser, logging
import pymongo

from utils import tree
import errors

logger = logging.getLogger("MetagenomeDB.connection")

__connection = None

def __connect (host, port, db, user, password):
	global __connection

	try:
		connection = pymongo.connection.Connection(host, port)
		if (not db in connection.database_names()):
			logger.warning("The database '%s' doesn't exist and has been created." % db)

		connection = connection[db]

	except pymongo.errors.ConnectionFailure as msg:
		raise errors.ConnectionError(db, host, port, msg)

	logger.debug("Connected to '%s' on %s:%s." % (db, host, port))

	# use credentials, if any
	if (user != ''):
		connection.authenticate(user, password)

		logger.debug("Authenticated as '%s'." % user)

	# test if the credentials are okay
	try:
		connection.collection_names()

	except pymongo.errors.OperationFailure as msg:
		raise errors.ConnectionError(db, host, port, "Incorrect credentials.")

	__connection = connection
	return __connection

def connect (host = "localhost", port = 27017, database = "MetagenomeDB", user = '', password = ''):
	""" Override MongoDB server connection information.
	
	Parameters:
		- **host**: host of the MongoDB server (optional). Default: 'localhost'
		- **port**: port of the MongoDB server (optional). Default: 27017
		- **database**: database within the MongoDB server (optional). Default:
		  'MetagenomeDB'
		- **user**: user for a secured MongoDB connection (optional)
		- **password**: password for a secured MongoDB connection (optional)
	
	.. note::
		If :func:`~connection.connect` is not called, the connection information
		are read in the '~/.MetagenomeDB' file.
	"""
	__connect(host, port, database, user, password)

# Return a connection to a MongoDB server. If no connection information has
# been provided by a previous call to connect(), those information are
# extracted from '~/.MetagenomeDB'. Act as a singleton; i.e., all subsequent
# calls to this function will return the existing connection.
def connection():
	if (__connection != None):
		return __connection

	cp = ConfigParser.RawConfigParser()
	fn = os.path.expanduser(os.path.join("~", ".MetagenomeDB"))

	if (cp.read(fn) == []):
		raise errors.MetagenomeDBError("Unable to find the configuration file '%s'." % fn)

	host = __property(cp, "connection", "host", "localhost")
	port = __property(cp, "connection", "port", 27017, "int")
	db = __property(cp, "connection", "database")

	user = __property(cp, "connection", "user", '')
	password = __property(cp, "connection", "password", '')

	return __connect(host, port, db, user, password)

def __property (cp, section, key, default = None, coerce = None):
	try:
		if (coerce == "int"):
			return cp.getint(section, key)

		if (coerce == "float"):
			return cp.getfloat(section, key)

		return cp.get(section, key)

	except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
		if (default != None):
			logger.debug("Default value '%s' used for key '%s' in section '%s'." % (default, key, section))
			return default
		else:
			raise errors.MetagenomeDBError("No value found for key '%s' in section '%s'." % (key, section))

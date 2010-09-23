
import os, sys, ConfigParser, logging
import pymongo

from utils import tree
import errors

logger = logging.getLogger("MetagenomeDB.connection")

# Retrieve a value from a .cfg file
def __property (cp, section, key, default = None, coerce = None):
	try:
		if (coerce == "int"):
			return cp.getint(section, key)

		if (coerce == "float"):
			return cp.getfloat(section, key)

		return cp.get(section, key)

	except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
		if (default != None):
			logger.debug("Default value '%s' used for key '%s' in section '%s'" % (default, key, section))
			return default
		else:
			raise Exception("No value found for key '%s' in section '%s'" % (key, section))

__connection = None

# Create a connection to a MongoDB server. Act as a singleton; i.e., if a
# connection has already been set up, return it rather than creating a new one.
def connection():
	global __connection

	if (__connection != None):
		return __connection

	cp = ConfigParser.RawConfigParser()

	if (cp.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "connection.cfg")) == []):
		raise Exception("Unable to locate 'connection.cfg'.")

	host = __property(cp, "connection", "host", "localhost")
	port = __property(cp, "connection", "port", 27017, "int")
	db = __property(cp, "connection", "database")

	try:
		connection = pymongo.connection.Connection(host, port)[db]

	except pymongo.errors.ConnectionFailure as msg:
		raise errors.ConnectionError(db, host, port, msg)

	logger.info("Connected to '%s' on %s:%s" % (db, host, port))

	# use credentials, if any
	user = __property(cp, "connection", "user", '')
	password = __property(cp, "connection", "password", '')

	if (user != ''):
		connection.authenticate(user, password)

		logger.info("Authenticated as '%s'" % user)

	# test if the credentials are okay
	try:
		connection.collection_names()

	except pymongo.errors.OperationFailure as msg:
		raise errors.ConnectionError(db, host, port, "Incorrect credentials.")

	__connection = connection
	return __connection

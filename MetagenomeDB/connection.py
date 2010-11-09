
import os, sys, ConfigParser, logging
import pymongo

from utils import tree
import errors

logger = logging.getLogger("MetagenomeDB.connection")

__connection = None

def __connect (host, port, db, user, password):
	global __connection

	try:
		connection = pymongo.connection.Connection(host, port)[db]

	except pymongo.errors.ConnectionFailure as msg:
		raise errors.ConnectionError(db, host, port, msg)

	logger.info("Connected to '%s' on %s:%s." % (db, host, port))

	# use credentials, if any
	if (user != ''):
		connection.authenticate(user, password)

		logger.info("Authenticated as '%s'." % user)

	# test if the credentials are okay
	try:
		connection.collection_names()

	except pymongo.errors.OperationFailure as msg:
		raise errors.ConnectionError(db, host, port, "Incorrect credentials.")

	__connection = connection
	return __connection

# Specify the access parameters to a MongoDB server. If not used, MetagenomeDB
# will read those parameters from the 'MetagenomeDB/connection.cfg' file.
def connect (host = "localhost", port = 27017, database = "MetagenomeDB", user = '', password = ''):
	__connect(host, port, database, user, password)

# Return a connection to a MongoDB server. If no connection information has
# been provided by a previous call to connect(), those information are
# extracted from 'MetagenomeDB/connection.cfg'. Act as a singleton; i.e., all
# subsequent calls to this function will return the existing connection.
def connection():
	if (__connection != None):
		return __connection

	cp = ConfigParser.RawConfigParser()

	if (cp.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "connection.cfg")) == []):
		raise Exception("Unable to locate 'connection.cfg'.")

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
			raise Exception("No value found for key '%s' in section '%s'." % (key, section))

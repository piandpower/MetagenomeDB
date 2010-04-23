
import os, sys, ConfigParser
import commons
import pymongo

def __property (cp, section, key, default = None, coerce = None):
	try:
		if (coerce == "int"):
			return cp.getint(section, key)

		if (coerce == "float"):
			return cp.getfloat(section, key)

		return cp.get(section, key)

	except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
		if (default):
			return default
		else:
			raise Exception("No value found for '%s' in section '%s'" % (key, section))

__connection = None

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
		raise Exception("Unable to connect to database '%s' on %s:%s. Message was: %s" % (db, host, port, msg))

	if (commons.debug_level > 0):
		commons.log("connection", "Connected to '%s' on %s:%s" % (db, host, port))

	# use credentials, if any
	user = __property(cp, "connection", "user", '')
	password = __property(cp, "connection", "password", '')

	if (user != ''):
		connection.authenticate(user, password)

		if (commons.debug_level):
			commons.log("connection", "Authenticated as '%s'" % user)

	# test if the credentials are okay
	try:
		connection.collection_names()

	except pymongo.errors.OperationFailure as msg:
		raise Exception("Unable to connect to database '%s' on %s:%s. Incorrect credentials." % (db, host, port))

	__connection = connection
	return __connection

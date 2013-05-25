
from .. import errors

import pymongo

import os
import ConfigParser
import contextlib
import copy
import logging

logger = logging.getLogger("MetagenomeDB.ORM.connection")

_connection = None # connection to a database (warning: instance of pymongo.database.Database, NOT pymongo.connection.Connection)
_connection_info = {} # information about the connection

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

	url = "mongodb://"
	if (user != ''):
		url += "%s@" % user
	url += "%s:%s/%s" % (host, port, db)

	logger.debug("Connection requested to %s" % url)

	try:
		connection = pymongo.connection.Connection(host, port)
		database = pymongo.database.Database(connection, db)

		# use credentials, if any
		if (user != ''):
			success = database.authenticate(user, password)
			if (not success):
				raise errors.DBConnectionError(db, host, port, "Authentication failed (user: '%s', password: '%s')." % (user, password))

			logger.debug("Authenticated as '%s'." % user)

		database.collection_names()

	except pymongo.errors.ConnectionFailure as msg:
		# the mongodb server couldn't be located
		raise errors.DBConnectionError(db, host, port, msg)

	except pymongo.errors.OperationFailure as msg:
		if ("database error: unauthorized" in str(msg)):
			msg = "Incorrect credentials or database doesn't exist."

		raise errors.DBConnectionError(str(msg))

	logger.debug("Connected to %s" % url)

	global _connection
	_connection = database

	global _connection_info
	_connection_info = {
		"host": host,
		"port": port,
		"db": db,
		"user": user,
		"password": password,
		"url": url
	}

	return _connection

def connection():
	""" Obtain a connection object to a MongoDB database. If no connection exists, connect() is called without argument.

	.. note::
		connection() is a singleton; i.e., any call to this function will
		return the same connection object.
	"""
	if (_connection == None):
		logger.debug("New connection requested by PID %s" % os.getpid())
		connect()

	return _connection

def connection_information():
	""" Obtain information about the connection to MongoDB, as a dictionary.
	"""
	if (_connection == None):
		logger.debug("New connection information requested by PID %s" % os.getpid())
		connect()

	return copy.deepcopy(_connection_info)

@contextlib.contextmanager
def protect():
	try:
		yield

	except pymongo.errors.ConnectionFailure as e:
		raise errors.DBConnectionError("Unable to access the database. Reason: " + str(e))

	except pymongo.errors.OperationFailure as e:
		try:
			error = connection().previous_error()
		except:
			error = None

		if (error == None):
			msg, code = str(e), None
		else:
			msg, code = error["err"], error.get("code")

		if ("unauthorized" in msg) or ("auth fails" in msg):
			raise errors.DBConnectionError("Incorrect credentials.")

		if (code != None):
			msg += " (error code: %s)" % code

		raise errors.DBOperationError("Unable to perform the operation. Reason: " + msg)

	except pymongo.errors.PyMongoError as e:
		raise errors.DBOperationError("Unable to perform the operation. Reason: " + str(e))


import os, sys, ConfigParser
import pymongo

def __property (cp, section, key, default, coerce = None):
	try:
		if (coerce == "int"):
			return cp.getint(section, key)

		if (coerce == "float"):
			return cp.getfloat(section, key)

		return cp.get(section, key)

	except ConfigParser.NoSectionError:
		return default

	except ConfigParser.NoOptionError:
		return default

__cwd = os.path.dirname(os.path.abspath(__file__))
__connection = None

def connect (host = None, port = None, db = None):
	global __connection

	if (__connection != None):
		return

	if (host == None) or (port == None) or (db == None):
		cp = ConfigParser.RawConfigParser()

		if (cp.read(os.path.join(__cwd, "connection.cfg")) == []):
			raise Exception("Unable to locate 'connection.cfg'.")

	if (host == None):
		host = __property(cp, "db", "host", "localhost")

	if (port == None):
		port = __property(cp, "db", "port", 27017, "int")

	if (db == None):
		db = __property(cp, "db", "database", "MetagenomeDB")

	try:
		connection = pymongo.connection.Connection(host, port)[db]

#		connection.add_son_manipulator(pymongo.son_manipulator.NamespaceInjector())
#		connection.add_son_manipulator(pymongo.son_manipulator.AutoReference(connection))

	except pymongo.errors.ConnectionFailure, msg:
		raise Exception("Unable to connect to database '%s' on %s:%s. Message was: %s" % (db, host, port, msg))

	__connection = connection

def connection():
	if (__connection == None):
		connect()

	return __connection
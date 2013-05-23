
g = optparse.OptionGroup(p, "connection to the database")

connection_parameters = {}
def declare_connection_parameter (option, opt, value, parser):
	connection_parameters[opt[2:]] = value

g.add_option("--host", dest = "connection_host", metavar = "HOSTNAME",
	type = "string", action = "callback", callback = declare_connection_parameter,
	help = """Host name or IP address of the MongoDB server (optional). Default:
'host' property in ~/.MetagenomeDB, or 'localhost' if not found.""")

g.add_option("--port", dest = "connection_port", metavar = "INTEGER",
	type = "string", action = "callback", callback = declare_connection_parameter,
	help = """Port of the MongoDB server (optional). Default: 'port' property
in ~/.MetagenomeDB, or 27017 if not found.""")

g.add_option("--db", dest = "connection_db", metavar = "STRING",
	type = "string", action = "callback", callback = declare_connection_parameter,
	help = """Name of the database in the MongoDB server (optional). Default:
'db' property in ~/.MetagenomeDB, or 'MetagenomeDB' if not found.""")

g.add_option("--user", dest = "connection_user", metavar = "STRING",
	type = "string", action = "callback", callback = declare_connection_parameter,
	help = """User for the MongoDB server connection (optional). Default:
'user' property in ~/.MetagenomeDB, or none if not found.""")

g.add_option("--password", dest = "connection_password", metavar = "STRING",
	type = "string", action = "callback", callback = declare_connection_parameter,
	help = """Password for the MongoDB server connection (optional). Default:
'password' property in ~/.MetagenomeDB, or none if not found.""")

p.add_option_group(g)

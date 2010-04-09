
debug_level = 0

def set_debug_level (level):
	global debug_level
	debug_level = level
	log("set_debug_level", "Debug level set to %s" % level)

def log (method, message):
	print "MetagenomeDB: %s(): %s" % (method, message)

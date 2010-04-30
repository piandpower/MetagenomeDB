
debug_level = 0
display_warnings = True

def set_debug_level (level):
	global debug_level
	debug_level = level
	log("set_debug_level", "Debug level set to %s" % level)

def show_warnings (boolean):
	global display_warnings
	display_warnings = boolean
	log("show_warnings", "Warnings will %sbe displayed" % { True: '', False: "not " }[boolean])

def log (method, message):
	print "MetagenomeDB: %s(): %s" % (method, message)

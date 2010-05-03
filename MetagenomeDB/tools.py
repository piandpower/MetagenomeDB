# tools.py: Routines for MetagenomeDB tools (see Tools/)

import re, json, csv
import tree

__PROPERTY = re.compile("^(\[)?((?:,?(?:string|integer|float|boolean))+)$")

# slight improvement of boolean()
def __formatter_boolean (value):
	if (value.lower() == "false"):
		return False

	elif (value.lower() == "true"):
		return True

	else:
		return boolean(value)

__FORMATTER = {
	"string": lambda x: str(x),
	"integer": lambda x: int(x),
	"float": lambda x: float(x),
	"boolean": __formatter_boolean
}

def parse (value, separator = '!'):
	if (separator in value):
		value, modifier = value.split(separator)

		m = __PROPERTY.match(modifier.lower())
		if (m == None):
			raise ValueError("Malformed property modifier: '%s'" % modifier)

		is_list = (m.group(1) == '[')
		types = m.group(2).split(',')

		def formatter (value, types):
			for type in types:
				try:
					return __FORMATTER[type](value)
				except:
					continue

			raise ValueError("Unable to cast '%s' into any of: %s" % (value, ', '.join(types)))

		if (is_list):
			value = [formatter(v, types) for v in value.split(',')]
		else:
			value = formatter(value, types)

	return value

def parser (fn, format):
	if (format == "json"):
		try:
			data = json.load(open(fn, 'r'))

			if (type(data) == dict):
				data = [data]

			elif (type(data) != list):
				raise ValueError("Unexpected JSON type: %s" % type(data))

		except Exception as msg:
			error("Error while reading '%s': %s" % (fn, msg))

		data = [tree.traverse(
			entry,
			selector = lambda x: True,
			key_modifier = lambda x: str(x), # hack to work around a bug in Python 2.6, which doesn't allow kwargs with unicode strings.
			value_modifier = lambda x: parse(x)
		) for entry in data]

		returndata

	elif (format == "csv"):
		def generator():
			for line in csv.reader(open(fn, 'r'), delimiter = ',', quotechar='"'):
				map = {}
				for item in line:
					key, value = item.split('=')
					tree.set(map, key.split('.'), parse(value))

				yield map

		return generator()

	else:
		raise ValueError("Unknown format '%s'" % format)

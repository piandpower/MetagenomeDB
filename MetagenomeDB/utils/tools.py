# tools.py: Routines for MetagenomeDB tools (see tools/)

import re, json, csv, sys
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

# Parse a string-formatted value into the corresponding Python object
# Format: "value^([)type(,type)" with type in 'string', 'integer', 'float' or 'boolean'
# Examples:
#	"5^integer" -> 5
#	"3,4^[integer" -> [3, 4]
#	"1^integer,string" -> 1
#	"a^integer,string" -> "a"
#	"true^boolean" -> True
def parse (value, separator = '^'):
	if (separator in value):
		value, modifier = value.rsplit(separator, 1)

		m = __PROPERTY.match(modifier.lower())
		if (m == None):
			raise ValueError("Malformed value modifier: '%s'" % modifier)

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

REPLACE = 1
APPEND = 2
APPEND_IF_UNIQUE = 3
REMOVE = 4

# Parse either a JSON-formatted or CSV-formatted file, returning key/values
# as an iterator. 'format' must be either 'json' or 'csv'.
def parser (fn, format):
	if (fn == '-'):
		i = sys.stdin
	else:
		i = open(fn, 'rU')

	if (format == "json"):
		try:
			data = json.load(i)

			if (type(data) == dict):
				data = [data]

			elif (type(data) != list):
				raise ValueError("Unexpected JSON type: %s" % type(data))

		except Exception as msg:
			raise Exception("Error while reading '%s': %s" % (fn, msg))

		data = [tree.traverse(
			entry,
			selector = lambda x: True,
			key_modifier = lambda x: str(x), # hack to work around a bug in Python 2.6, which doesn't allow kwargs with unicode strings.
			value_modifier = lambda x: (parse(x), REPLACE)
		) for entry in data]

		return data

	elif (format == "csv"):
		def extract_key_value (text):
			in_quote = False
			reached_pivot = False
			key, value = '', ''
			command = None

			for c in text:
				if (c == '"'):
					in_quote = not in_quote
					continue

				if (not in_quote) and (not reached_pivot) and (c in ('=', '+', '-', '&')):
					reached_pivot = True
					command = {
						'=': REPLACE,
						'&': APPEND,
						'+': APPEND_IF_UNIQUE,
						'-': REMOVE,
					}[c]
					continue

				if (reached_pivot):
					value += c
				else:
					key += c

			if (not reached_pivot):
				raise Exception("Invalid entry (no key/value separator): %s" % text)

			return key.strip(), value.strip(), command

		def generator():
			for line in csv.reader(i, delimiter = ',', quotechar='"'):
				line = filter(lambda x: x != '', line)

				if (len(line) == 0): # empty lines
					continue

				if (line[0].startswith('#')): # commented lines
					continue

				map = {}
				for item in line:
					key, value, command = extract_key_value(item)
					tree.set(map, tree.validate_key(key), (parse(value), command))

				yield map

		return generator()

	else:
		raise ValueError("Unknown format '%s'" % format)

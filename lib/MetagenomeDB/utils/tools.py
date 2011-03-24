# tools.py: Routines for MetagenomeDB tools (see tools/)

from __future__ import absolute_import

import re, json, csv, sys
from . import tree
from .. import errors

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
	"string": lambda x: str(x).strip('"'),
	"integer": lambda x: int(x),
	"float": lambda x: float(x),
	"boolean": __formatter_boolean
}

# Split a string according to a separator, while taking quotes into account
# e.g., '"a,b","c"' will result in ['"a,b"', '"c"']
def psplit (text, separator):
	in_quote, reached_pivot, pivot_n = False, False, 0
	values = ['']
	for c in text:
		if (c == '"'):
			in_quote = not in_quote

		if (not in_quote) and (not reached_pivot) and (c == separator):
			reached_pivot = True
			pivot_n += 1
			values.append('')
			continue

		values[pivot_n] += c

	return filter(lambda x: x != '', values)

def parse_key_and_value (text):
	in_quote, reached_pivot = False, False
	key, value = '', ''

	command = None
	for c in text:
		if (c == '"'):
			in_quote = not in_quote

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
		raise errors.MetagenomeDBError("Invalid entry (no key/value separator): %s" % text)

	return key.strip().strip('"'), value.strip(), command

# Parse a string-formatted value into the corresponding Python object
# Format: "value^([)type(,type)" with type in 'string', 'integer', 'float' or 'boolean'
# Examples:
#	"5^integer" -> 5
#	"3,4^[integer" -> [3, 4]
#	"1^integer,string" -> 1
#	"a^integer,string" -> "a"
#	"true^boolean" -> True
def parse_value_and_modifier (value, separator = '^'):
	if (separator in value):
		value, modifier = psplit(value, separator)

		m = __PROPERTY.match(modifier)
		if (m == None):
			raise errors.MetagenomeDBError("Malformed value modifier: '%s'" % modifier)

		is_list = (m.group(1) == '[')
		types = m.group(2).split(',')

		def formatter (value, types):
			for type in types:
				try:
					return __FORMATTER[type](value)
				except:
					continue

			raise errors.MetagenomeDBError("Unable to cast '%s' into any of: %s" % (value, ', '.join(types)))

		if (is_list):
			return [formatter(v, types) for v in psplit(value, ",")]
		else:
			return formatter(value, types)

	return value.strip('"')

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
				raise errors.MetagenomeDBError("Unexpected JSON type: %s" % type(data))

		except Exception as msg:
			raise errors.MetagenomeDBError("Error while reading '%s': %s" % (fn, msg))

		data = [tree.traverse(
			entry,
			selector = lambda x: True,
			key_modifier = lambda x: str(x), # hack to work around a bug in Python 2.6, which doesn't allow kwargs with unicode strings.
			value_modifier = lambda x: (parse_value_and_modifier(x), REPLACE)
		) for entry in data]

		return data

	elif (format == "csv"):
		def generator():
			for line in csv.reader(i, delimiter = ',', quotechar='"'):
				line = filter(lambda x: x != '', line)

				if (len(line) == 0): # empty lines
					continue

				if (line[0].startswith('#')): # commented lines
					continue

				map = {}
				for item in line:
					key, value, command = parse_key_and_value(item)
					tree.set(map, tree.validate_key(key), (parse_value_and_modifier(value), command))

				yield map

		return generator()

	else:
		raise errors.MetagenomeDBError("Unknown format '%s'" % format)

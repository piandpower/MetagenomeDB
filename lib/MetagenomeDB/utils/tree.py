# Manipulation of a JSON objects as nested dictionaries

def expand_key (key, separator = '.'):
	""" Expand a dot-notation key into a list
	"""
	key_t = type(key)

	if (key_t == list):
		key = tuple(key)

	elif (key_t == str) or (key_t == unicode):
		key = tuple(key.split(separator))

	elif (key_t != tuple):
		raise ValueError("Malformed key: '%s'" % key)

	if (len(key) == 0):
		raise ValueError("Empty key")

	for i, subkey in enumerate(key):
		if (subkey.startswith('$')) and (i+1 < len(key)):
			raise ValueError("Malformed key '%s': special keys ('%s'?) must be last" % (separator.join(key), subkey))

	return key

def set (dictionary, key, value):
	""" Insert a nested key into a dictionary

	Parameters:
		- **dictionary**: dictionary to populate
		- **key**: nested key, as a list
		- **value**: value to set

	Example:
		> m = {}
		> set(m, ('a', 'b', 'c'), 1)
		> print m
		{'a': {'b': {'c': 1}}}
	"""
	is_leaf, root = (len(key) == 1), key[0]

	if (is_leaf):
		dictionary[root] = value
	else:
		if (not root in dictionary):
			dictionary[root] = {}

		set(dictionary[root], key[1:], value)

def get (dictionary, key):
	""" Query a nested key from a dictionary

	Parameters:
		- **dictionary**: dictionary to query
		- **key**: nested key, as a list
	"""
	is_leaf, root = (len(key) == 1), key[0]

	if (is_leaf):
		return dictionary[root]
	else:
		return get(dictionary[root], key[1:])

def delete (dictionary, key):
	""" Delete a nested key from a dictionary

	Parameters:
		- **dictionary**: dictionary to modify
		- **key**: nested key to delete, as a list
	"""
	is_leaf, root = (len(key) == 1), key[0]

	if (type(dictionary) != dict):
		raise KeyError(root)

	if (is_leaf):
		del dictionary[root]

	else:
		delete(dictionary[root], key[1:])
		if (len(dictionary[root]) == 0):
			del dictionary[root]

def contains (dictionary, key):
	""" Test if a dictionary contains a nested key
	
	Parameters:
		- **dictionary**: dictionary to evaluate
		- **key**: nested key to test, as a list
	"""
	is_leaf, root = (len(key) == 1), key[0]

	if (root in dictionary):
		if (is_leaf):
			return True

		if (type(dictionary[root]) != dict):
			return False

		return contains(dictionary[root], key[1:])

	return False

def items (dictionary):
	""" Iterate through a nested dictionary and return all
	keys (as lists) and values

	Parameters:
		- **dictionary**: dictionary to browse

	Example:
		> m = {'a': {'b': {'c': 1}, 'd': 2}}
		> print items(m)
		[(('a', 'b', 'c'), 1), (('a', 'd'), 2)]
	"""
	def walk (node, b = []):
		items = []

		for key in node:
			branch, value = b + list(expand_key(key)), node[key]

			if (type(value) == dict):
				items.extend(walk(value, branch))
			else:
				items.append((tuple(branch), value))

		return items

	return walk(dictionary)

def expand (dictionary, separator = '.'):
	""" Transform a dictionary with dot-notation keys into a nested dictionary

	Parameters:
		- **dictionary**: dictionary to transform

	Example:
		> m = {"a.b.c": 1}
		> print expand(m)
		{"a": {"b": {"c": 1}}}
	"""
	d = {}
	for key, value in dictionary.iteritems():
		set(d, expand_key(key, separator), value)

	return d

def flatten (dictionary, separator = '.'):
	""" Transform a nested dictionary into a dictionary with dot-notations

	Parameters:
		- **dictionary**: dictionary to transform

	Example:
		> m = {"a": {"b": {"c": 1}}}
		> print flatten(m)
		{"a.b.c": 1}
	"""
	d = {}
	for (key, value) in items(dictionary):
		# hack: we don't want to flatten special MongoDB
		# keys (everything starting with a '$')
		if (key[-1].startswith('$')):
			d[separator.join(key[:-1])] = {key[-1]: value}
		else:
			d[separator.join(key)] = value

	return d

def traverse (dictionary, selector = lambda x: False, key_modifier = lambda x: x, value_modifier = lambda x: x):
	""" Traverse a nested dictionary and modify keys or values

	Parameters:
		- **dictionary**: dictionary to transform
		- **selector**: boolean function receiving each key and sub-key; if
		  returns True, then this key and its value will be modified
		- **key_modifier**: function receiving a key to modify; its return is
		  used as the new key value
		- **value_modifier**: function receiving a value to modify; its return
		  is used as the new value
	"""
	tree = {}

	for key in dictionary:
		value = dictionary[key]
		selected = selector(key)

		if (selected):
			key = key_modifier(key)

		if (type(value) == dict):
			tree[key] = traverse(value, selector, key_modifier, value_modifier)

		elif (selected):
			tree[key] = value_modifier(value)

		else:
			tree[key] = value

	return tree

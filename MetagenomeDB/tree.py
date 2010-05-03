# Manipulation of a tree as a nested dictionary

def validate_key (key, separator = '.'):
	key_t = type(key)

	if (key_t == list):
		key = tuple(key)

	elif (key_t == str):
		key = tuple(key.split(separator))

	elif (key_t != tuple):
		raise ValueError("Malformed key hierarchy: '%s'" % key)

	if (len(key) == 0):
		raise ValueError("Empty key hierarchy")

	return key

# Insert a key/value pair into an existing dictionary
# - d: dictionary to consider
# - keys: hiearchy of keys, as a list
# - value: value to associate to the last key in the hierarchy
# Example:
#   > m = {}
#   > set(m, ('a', 'b', 'c'), 1)
#   > print m
#   {'a': {'b': {'c': 1}}}
def set (d, keys, value):
	leaf, key = (len(keys) == 1), keys[0]

	if (leaf):
		d[key] = value
	else:
		if (not key in d):
			d[key] = {}

		set(d[key], keys[1:], value)

# Retrieve the value associated to a hierarchy of key
# - d: dictionary to consider
# - keys: hiearchy of keys, as a list
def get (d, keys):
	leaf, key = (len(keys) == 1), keys[0]

	if (leaf):
		return d[key]
	else:
		return get(d[key], keys[1:])

# Iterate through a given nested dictionary and return all
# key hierarchies as lists of keys
# - d: dictionary to consider
# Example:
#   > m = {'a': {'b': {'c': 1}, 'd': 2}}
#   > print keys(m)
#   [(('a', 'b', 'c'), 1), (('a', 'd'), 2)]
def keys (d, path = []):
	branches = []
	for key in d:
		value = d[key]
		path_ = path + [key]

		if (type(value) == dict):
			branches.extend(keys(value, path_))
		else:
			branches.append((tuple(path_), value))

	return branches

# Delete a hiearchy of keys
def delete (d, keys):
	leaf, key = (len(keys) == 1), keys[0]

	if (type(d) != dict):
		raise KeyError(key)

	if (leaf):
		del d[key]

	else:
		delete(d[key], keys[1:])
		if (len(d[key]) == 0):
			del d[key]

# Test if a dictionary contains a value for a given hiearchy of keys
def contains (d, keys):
	leaf, key = (len(keys) == 1), keys[0]

	if (key in d):
		if (leaf):
			return True

		if (type(d[key]) != dict):
			return False

		return contains(d[key], keys[1:])

	return False

# Traverse a nested dictionary and modify selected key and/or values
# - d: dictionary to consider
# - selector: boolean function; should return true for key that should be modified
# - key_modifier: function that will be applied on selected keys
# - value_modifier: function that will be applied on values of selected keys
def traverse (d, selector = lambda x: False, key_modifier = lambda x: x, value_modifier = lambda x: x):
	tree = {}

	for key in d:
		value = d[key]
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

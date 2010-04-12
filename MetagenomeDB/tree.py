# Manipulation of a tree as a nested dictionary

def _check_keys (keys):
	kt = type(keys)

	if (kt == list):
		keys = tuple(keys)
	elif (kt != tuple):
		keys = (keys,)

	if (len(keys) == 0):
		raise ValueError("Empty set of keys")

	return keys

def set (map, keys, value):
	keys = _check_keys(keys)
	leaf, key = (len(keys) == 1), keys[0]

	if (leaf):
		map[key] = value
	else:
		if (not key in map):
			map[key] = {}

		set(map[key], keys[1:], value)

def get (map, keys):
	keys = _check_keys(keys)
	leaf, key = (len(keys) == 1), keys[0]

	if (leaf):
		return map[key]
	else:
		return get(map[key], keys[1:])

def iterate (map, path = []):
	branches = []
	for key in map:
		value = map[key]
		path_ = path + [key]

		if (type(value) == dict):
			branches.extend(iterate(value, path_))
		else:
			branches.append((tuple(path_), value))

	return branches

def delete (map, keys):
	keys = _check_keys(keys)
	leaf, key = (len(keys) == 1), keys[0]

	if (type(map) != dict):
		raise KeyError(key)

	if (leaf):
		del map[key]

	else:
		delete(map[key], keys[1:])
		if (len(map[key]) == 0):
			del map[key]

def contains (map, keys):
	keys = _check_keys(keys)
	leaf, key = (len(keys) == 1), keys[0]

	if (key in map):
		if (leaf):
			return True

		if (type(map[key]) != dict):
			return False

		return contains(map[key], keys[1:])

	return False

def traverse (tree, selector = lambda x: False, key_modifier = lambda x: x, value_modifier = lambda x: x):
	tree_ = {}

	for key in tree:
		value = tree[key]
		selected = selector(key)

		if (selected):
			key = key_modifier(key)

		if (type(value) == dict):
			tree_[key] = traverse(value, selector, key_modifier, value_modifier)

		elif (selected):
			tree_[key] = value_modifier(value)

		else:
			tree_[key] = value

	return tree_

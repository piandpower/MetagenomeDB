
def id_modifier (expression):
	""" Evaluate the provided expression, replacing any '%' symbol by a
		variable that will contain the identifier to modify. If a '%' symbol
		is needed in the expression, escape it by doubling it (i.e., '%%')

		Example:
			% -> [identifier]
			%.split() -> [identifier].split()
			% %% 2 - > [identifier] % 2
	"""
	placeholder = re.compile("(?<!%)%(?!%)")

	try:
		return eval("lambda item: " + placeholder.sub("item", expression).replace("%%", "%"))

	except SyntaxError as e:
		error("invalid setter:\n%s\n%s^ syntax error" % (e.text, ' ' * (e.offset - 1)))

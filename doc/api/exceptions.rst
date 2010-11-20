Exceptions
==========

Classes used to represent exceptions. When using the MetagenomeDB API it is recommanded to use the ``try``/``except`` syntax to catch such exceptions and display meaningful error messages. For example::

	import MetagenomeDB as mdb

	try:
		mdb.connect(database = "My database")

	# here we catch any exception related to the database connection
	except mdb.ConnectionError as msg:
		print "Connection error: %s" % msg

	# here we catch any other exception thrown by the toolkit
	except mdb.MetagenomeDBerror as msg:
		print "General error: %s" % msg

(see the Python `documentation <http://docs.python.org/tutorial/errors.html>`_ about handling exceptions)

.. automodule:: errors
   :members:

.. toctree::
   :hidden:

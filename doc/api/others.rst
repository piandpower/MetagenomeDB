Additional functions
====================

In addition to the :class:`~objects.Sequence` and :class:`~objects.Collection` classes and their methods, some more functions are available as part of the API:

Setting the verbosity
---------------------

Most methods of the MetagenomeDB API log messages about the information they process, the result of this processing, and their interaction with the underlying database. Those messages are of three different types, listed here from the least to the most important (or severe):

- **debug** messages: debugging messages as encountered during code execution. Those are useful only to keep track of low-level processes, such as object addition or query. Except for debugging purpose those messages are not important for the normal use of the API, and are filtered out by default.
- **warning** messages: reports conditions that might cause a problem in the future but are not immediately preventing the normal execution of your code. Typically, this is when the API falls back on default behavior after an invalid request is made (e.g., access to an non-existent database, or deletion of an uncommitted object). The user should be aware of this default behavior and act accordingly, as it may change the behavior of his code in way he didn't expect. By default, all messages of this level and above are displayed.
- **error** messages: reports conditions that typically prevent the normal execution of your code. You must address the issue and re-execute the failed instruction(s).

The following functions allow to filter the type of messages that will be displayed on the standard error stream when using the API:

.. automodule:: MetagenomeDB
   :members:

Example of use::

	>>> import MetagenomeDB as mdb
	>>> mdb.max_verbosity()
	2010-11-22 15:08:06,873	DEBUG: Verbosity set to 'debug'. set_verbosity() in __init__.py, line 34

Similarly, all command-line tools have a ``-v`` (or ``--verbose``) option to set verbosity to its maximum.

Connecting to the database
--------------------------

By default, information about how the toolkit must connect to the MongoDB server are stored in a file `.MetagenomeDB` in the home directory (see :doc:`../installation`). However you can override those settings by using the :func:`~connection.connect()` method:

.. automodule:: connection
   :members:

.. toctree::
   :hidden:

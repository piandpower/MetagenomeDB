Installation
============

**MetagenomeDB** relies on another Python library to function, Pymongo_ (version 1.9 or above). The latest version of Pymongo must be installed, for example by typing ``sudo easy_install Pymongo`` on the command line.

That's it. The only other requirement is, of course, a working MongoDB_ server, either on your computer or on a computer that can be accessed through TCP/IP.

MetagenomeDB can be installed using two methods:

Using GitHub
''''''''''''

All versions of MetagenomeDB, including the latest developer releases, can be downloaded at https://github.com/BioinformaticsCore/MetagenomeDB

Once the archive in your computer, installing it can be done by typing ``sudo easy_install [path to your archive]`` in a console (see the ``easy_install`` documentation: http://packages.python.org/distribute/easy_install.html).

If you want more control (such as requesting the library and the tools to be installed in specific directories), you should first unzip the archive, then type ``sudo python setup.py`` plus any needed option from the archive's content directory (see the ``setup.py`` documentation: http://docs.python.org/install/index.html). For example, to ensure the various mdb-* tools are installed in /usr/local/bin/ you can type ``sudo python setup.py install --install-scripts=/usr/local/bin/``.

GitHub is the preferred source if you are interested in the most recent, albeit potentially unstable, releases of MetagenomeDB.

Using PyPI
''''''''''

All production-ready versions of MetagenomeDB are registered against the PyPI_ package manager. Thanks to this, you can install the toolkit by typing ``sudo easy_install MetagenomeDB`` on the command line.

Final step
''''''''''

By default MetagenomeDB will read a file named ``.MetagenomeDB`` in your home directory to know how to access the MongoDB database. A template file named ``docs/examples/MetagenomeDB_configuration.txt`` is provided. Change its name to ``.MetagenomeDB``, move it in your home directory, then update it with your own parameters.

Optionally, you can provide those information when importing MetagenomeDB in your script::

	import MetagenomeDB as mdb

	mdb.connect(host = "localhost", port = 1234, database = "MyDatabase")

From then you can store and retrieve objects::

	c = mdb.Collection.find_one({"name": "my_collection"})

	for sequence in c.list_sequences():
		print sequence["name"], sequence["sequence"]

.. _MongoDB: http://www.mongodb.org/
.. _Pymongo: http://api.mongodb.org/python
.. _PyPI: http://pypi.python.org/

.. toctree::
   :hidden:

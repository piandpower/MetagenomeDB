MetagenomeDB |release| Documentation
====================================

Overview
--------
**MetagenomeDB** is a Python_-based toolkit designed to easily store, retrieve and annotate metagenomic sequences. This documentation attempts to explain everything you need to know to use **MetagenomeDB**.

:doc:`introduction`
  Introduction to the MetagenomeDB toolkit.

:doc:`installation`
  How to install the MetagenomeDB toolkit.

:doc:`tutorial`
  How to use MetagenomeDB for common tasks.

:doc:`api/index`
  Documentation for the Python library.

:doc:`tools/index`
  Documentation for the command-line tools.

.. toctree::
   :hidden:

   introduction
   installation
   tutorial
   api/index
   tools/index

About this documentation
------------------------

This documentation is generated using the `Sphinx <http://sphinx.pocoo.org/>`_ documentation generator. The source files for the documentation are located in the *doc/* directory of the
**MetagenomeDB** distribution. To generate the documentation locally run the
following command from the root directory of the **MetagenomeDB** source:

.. code-block:: bash

  $ python setup.py doc

.. _Python: http://www.python.org/
.. _MongoDB: http://www.mongodb.org/

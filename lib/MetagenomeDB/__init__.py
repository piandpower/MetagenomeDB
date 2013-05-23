
__version_major__ = 0
__version_minor__ = 2
__revision__ = 20
__build__ = "CEE3EF9"

version = "%s.%s (revision %s, build %s)" % (
	__version_major__,
	__version_minor__,
	__revision__,
	__build__
)

import logging
logger = logging.getLogger("MetagenomeDB")

__formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s	%(funcName)s() in %(filename)s, line %(lineno)d")
__handler = logging.StreamHandler()
__handler.setFormatter(__formatter)

logger.addHandler(__handler)

import backend
from connection import *
import errors
from objects import *
import tools
from utils import tree

def set_verbosity (level):
	""" Set the verbosity level for the MetagenomeDB API.

	Parameters:
		- **level**: either 'debug', 'warning' or 'error' (case insensitive).
		  Only messages of this level or above will be displayed.
	"""
	level_code = {
		"debug": logging.DEBUG,
#		"info": logging.INFO,
		"warning": logging.WARNING,
		"error": logging.ERROR,
#		"critical": logging.CRITICAL
	}.get(level.lower().strip(), logging.NOTSET)

	logger.setLevel(level_code)
	logger.debug("Verbosity set to '%s'." % level)

def min_verbosity():
	""" Set the verbosity to the minimal level.

	.. note::
		Equivalent to :func:`~MetagenomeDB.set_verbosity` with **level** set to
		"error"
	"""
	set_verbosity("error")

def normal_verbosity():
	""" Set the verbosity to the normal level.

	.. note::
		Equivalent to :func:`~MetagenomeDB.set_verbosity` with **level** set to
		"warning"
	"""
	set_verbosity("warning")

def max_verbosity():
	""" Set the verbosity to the maximal level.

	.. note::
		Equivalent to :func:`~MetagenomeDB.set_verbosity` with **level** set to
		"debug"
	"""
	set_verbosity("debug")

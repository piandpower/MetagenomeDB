
version = "0.2.2b"

import logging

logging.basicConfig(
	level = logging.WARNING,
	format = "%(asctime)s	%(levelname)s: %(message)s	%(funcName)s() in %(filename)s, line %(lineno)d"
)

logger = logging.getLogger("MetagenomeDB")

from connection import connect, connection
import backend, errors
from objects import Direction
from sequence import Sequence
from collection import Collection
from utils import tree, tools

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

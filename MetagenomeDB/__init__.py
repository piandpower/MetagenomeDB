
import logging

logging.basicConfig(
	level = logging.WARNING,
	format = "%(asctime)s	%(levelname)s: %(message)s	%(funcName)s() in %(filename)s, line %(lineno)d"
)

logger = logging.getLogger("MetagenomeDB")

from connection import connect, connection
from objects import Collection, Sequence, Direction
from errors import *
from utils import tree, tools

def set_verbosity (level):
	level_code = {
		"debug": logging.DEBUG,
		"info": logging.INFO,
		"warning": logging.WARNING,
		"error": logging.ERROR,
		"critical": logging.CRITICAL
	}.get(level.lower().strip(), logging.NOTSET)

	logger.setLevel(level_code)
	logger.info("Verbosity set to '%s'." % level)

def min_verbosity():
	set_verbosity("error")

def normal_verbosity():
	set_verbosity("warning")

def max_verbosity():
	set_verbosity("debug")

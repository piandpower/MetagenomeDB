
from ui import *
from parsing import *

import os

def include (template_name, globals):
	fn = os.path.join(os.path.dirname(__file__), "mdb_%s.py" % template_name)
	assert (os.path.exists(fn))
	execfile(fn, globals)

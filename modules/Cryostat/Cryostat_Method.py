from cPickle import load
from XMethod import _XMethod, XMethodError

def Method (fd = None):

	try:
		method = load (fd) if fd != None else _Method()
		if not isinstance (method, _Method):
			raise AttributeError

	except (
		UnpicklingError, AttributeError,
		EOFError, ImportError, IndexError
	):
		raise XMethodError ('Not a Cryostat method')

	return method

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Method (_XMethod):

	def __init__ (self):
		_XMethod.__init__ (self)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def set_cryostat_type (self, value):
		self['cryostat_type'] = value

	def set_insert_type (self, value):
		self['insert_type'] = value

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def get_cryostat_type (self, default_value = None):
		return self.get ('cryostat_type', default_value)

	def get_insert_type (self, default_value = None):
		return self.get ('insert_type', default_value)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from XMethod       import _XMethod, XMethodError
from cPickle       import load, UnpicklingError

def Method (fd = None):
	try:
		method = load (fd) if fd != None else _Method()
		if not isinstance (method, _Method) : raise AttributeError

	except (UnpicklingError, AttributeError, EOFError, ImportError, IndexError):
		raise XMethodError ('Not a resistivity method')

	return method

class _Method (_XMethod):

	def __init__ (self):
		_XMethod.__init__ (self)

	# ++++++++++++++++++++++++++++++++++++++++++

	def set_TCON_Method (self, method):
		self['tconMethod'] = method

	def get_TCON_Method (self, method = None):
		return self.get ('tconMethod', method)

	# ++++++++++++++++++++++++++++++++++++++++++

	def set_XHIRES_Method (self, method):
		self['xhiresMethod'] = method

	def get_XHIRES_Method (self, method = None):
		return self.get ('xhiresMethod', method)

	# ++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, runMode):
		self['runMode'] = runMode

	def getRunMode (self, runMode = None):
		return self.get ('runMode', runMode)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from XMethod       import _XMethod, XMethodError
from cPickle       import load, UnpicklingError

def Method (fd = None):
	try:
		method = load (fd) if fd != None else _Method()
		if not isinstance (method, _Method) : raise AttributeError

	except (UnpicklingError, AttributeError, EOFError, ImportError, IndexError):
		raise XMethodError ('Not a susceptibility method')

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

	def set_XLIA_Method (self, method):
		self['xliaMethod'] = method

	def get_XLIA_Method (self, method = None):
		return self.get ('xliaMethod', method)

	# ++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, runMode):
		self['runMode'] = runMode

	def getRunMode (self, runMode = None):
		return self.get ('runMode', runMode)

	# ++++++++++++++++++++++++++++++++++++++++++

	def setLinacMaxDepth (self, maxDepth):
		self['LinacMaxDepth'] = maxDepth

	def getLinacMaxDepth (self, maxDepth = None):
		return self.get ('LinacMaxDepth', maxDepth)

	# ++++++++++++++++++++++++++++++++++++++++++

	def setLinacStepSize (self, stepSize):
		self['LinacStepSize'] = stepSize

	def getLinacStepSize (self, stepSize = None):
		return self.get ('LinacStepSize', stepSize)

	# ++++++++++++++++++++++++++++++++++++++++++

	def setLinacProbeUp (self, probeUp):
		self['LinacProbeUp'] = probeUp

	def getLinacProbeUp (self, probeUp = None):
		return self.get ('LinacProbeUp', probeUp)

	# ++++++++++++++++++++++++++++++++++++++++++

	def setLinacProbeDown (self, probeDown):
		self['LinacProbeDown'] = probeDown

	def getLinacProbeDown (self, probeDown = None):
		return self.get ('LinacProbeDown', probeDown)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


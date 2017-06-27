from XMethod       import _XMethod, XMethodError
from cPickle       import load, UnpicklingError

def Method (fd = None):
	try:
		method = load (fd) if fd != None else _Method()
		if not isinstance (method, _Method) : raise AttributeError

	except (
		UnpicklingError, AttributeError,
		EOFError, ImportError, IndexError
	):
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

	def set_XSMU_Method (self, method):
		self['xsmuMethod'] = method

	def get_XSMU_Method (self, method = None):
		return self.get ('xsmuMethod', method)

	# ++++++++++++++++++++++++++++++++++++++++++

	def set_mgps_method (self, method):
		self['mgps_method'] = method

	def get_mgps_method (self, method = None):
		return self.get ('mgps_method', method)

	# ++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, runMode):
		self['runMode'] = runMode

	def getRunMode (self, runMode = None):
		return self.get ('runMode', runMode)

	# ++++++++++++++++++++++++++++++++++++++++++

	def set_rh_settings (self, total_cycle, H_max, H_step):

		self ['rh_settings'] = {

			'total_cycle' : total_cycle,
			'H_max'       : H_max,
			'H_set'       : H_step
		}

	def get_rh_settings (self, total_cycle = None,
					     H_max = None, H_step = None):

		try:

			rh_settings = self ['rh_settings']

			total_cycle = rh_settings.get ('total_cycle', total_cycle)
			H_max       = rh_settings.get ('H_max'      , H_max      )
			H_step      = rh_settings.get ('H_step'     , H_step     )

		except KeyError : pass

		return (total_cycle, H_max, H_step)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

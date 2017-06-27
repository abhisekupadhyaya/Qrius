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
		raise XMethodError ('Not an MGPS method')

	return method

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Method (_XMethod):

	def __init__ (self):
		_XMethod.__init__ (self)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setSourceParameters (self, mode, autorange, range, value):

		self['sourceParameters'] = {

			'mode'      : mode,
			'autorange' : autorange,
			'range'     : range,
			'value'     : value
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setMeterParameters (self,
		hm_autorange, hm_range, cm_autorange,
		cm_range, vm_autorange, vm_range):

		self['meterParameters'] = {

			'hm_autorange'  : hm_autorange,
			'hm_range'      : hm_range,
			'cm_autorange'  : cm_autorange,
			'cm_range'      : cm_range,
			'vm_autorange'  : vm_autorange,
			'vm_range'      : vm_range
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setAcquisitionSettings (self, delay, filterLength):

		self['acquisitionSettings'] = {
			'delay'        : delay,
			'filterLength' : filterLength
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getSourceParameters (self,
						     mode      = None,
							 autorange = None,
							 range     = None,
							 value     = None):

		try:
			parameters = self['sourceParameters']

			mode      = parameters.get ('mode'      , mode     )
			autorange = parameters.get ('autorange' , autorange)
			range     = parameters.get ('range'     , range    )
			value     = parameters.get ('value'     , value    )

		except KeyError : pass

		return (mode, autorange, range, value)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMeterParameters (self,
		hm_autorange = None, hm_range = None,
		cm_autorange = None, cm_range = None,
		vm_autorange = None, vm_range = None):

		try:
			parameters = self['meterParameters']
			hm_autorange = parameters.get ('hm_autorange', hm_autorange)
			hm_range     = parameters.get ('hm_range'    , hm_range)
			cm_autorange = parameters.get ('cm_autorange', cm_autorange)
			cm_range     = parameters.get ('cm_range'    , cm_range)
			vm_autorange = parameters.get ('vm_autorange', vm_autorange)
			vm_range     = parameters.get ('vm_range'    , vm_range)

		except KeyError : pass

		return (
			cm_autorange, cm_range,
			vm_autorange, vm_range)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getAcquisitionSettings (self,
								delay        = None,
								filterLength = None):

		try:
			settings = self['acquisitionSettings']
			delay        = settings.get ('delay'        , delay       )
			filterLength = settings.get ('filterLength' , filterLength)

		except KeyError : pass

		return (delay, filterLength)

	# ++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, run_mode):
		self['run_mode'] = run_mode

	def getRunMode (self, run_mode = None):
		return self.get ('run_mode', run_mode)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

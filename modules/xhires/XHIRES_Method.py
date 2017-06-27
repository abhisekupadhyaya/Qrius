from cPickle import load
from XMethod import _XMethod, XMethodError

def Method (fd = None):

	try:
		method = load (fd) if fd != None else _Method()
		if not isinstance (method, _Method):
			raise AttributeError

	except (UnpicklingError, AttributeError, EOFError, ImportError, IndexError):
		raise XMethodError ('Not an XHIRES method')

	return method

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Method (_XMethod):

	def __init__ (self):
		_XMethod.__init__ (self)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setSourceParameters (self, vs_autorange, vs_range, vs_value):

		self['sourceParameters'] = {
			'vs_autorange' : vs_autorange,
			'vs_range'     : vs_range,
			'vs_value'     : vs_value
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setMeterParameters (self, cm_autorange, cm_range,
							vm_autorange, vm_range):

		self['meterParameters'] = {
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

	def set_IV_RampSettings (self, finalVoltage, voltageStep, bipolar):

		self['IV_RampSettings'] = {
			'finalVoltage' : finalVoltage,
			'voltageStep'  : voltageStep,
			'bipolar'      : bipolar
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setOhmmeterSettings (self, maxVoltage, bipolar):

		self['ohmmeterSettings'] = {
			'maxVoltage'   : maxVoltage,
			'bipolar'      : bipolar
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getSourceParameters (self,
							 vs_autorange = None,
							 vs_range     = None,
							 vs_value     = None):

		try:
			parameters = self['sourceParameters']
			vs_autorange = parameters.get ('vs_autorange' , vs_autorange)
			vs_range     = parameters.get ('vs_range'     , vs_range    )
			vs_value     = parameters.get ('vs_value'     , vs_value    )

		except KeyError : pass

		return (vs_autorange, vs_range, vs_value)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMeterParameters (self,
							cm_autorange  = None,
							cm_range      = None,
							vm_autorange  = None,
							vm_range      = None):

		try:
			parameters = self['meterParameters']
			cm_autorange  = parameters.get ('cm_autorange'  , cm_autorange )
			cm_range      = parameters.get ('cm_range'      , cm_range     )
			vm_autorange  = parameters.get ('vm_autorange'  , vm_autorange )
			vm_range      = parameters.get ('vm_range'      , vm_range     )

		except KeyError : pass

		return (
			cm_autorange  , cm_range,
			vm_autorange  , vm_range)

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

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def get_IV_RampSettings (self,
							 finalVoltage = None,
							 voltageStep  = None,
							 bipolar      = None):

		try:
			settings = self['IV_RampSettings']
			finalVoltage = settings.get ('finalVoltage' , finalVoltage)
			voltageStep  = settings.get ('voltageStep'  , voltageStep )
			bipolar      = settings.get ('bipolar'      , bipolar     )

		except KeyError : pass

		return (finalVoltage, voltageStep, bipolar)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getOhmmeterSettings (self,
							 maxVoltage   = None,
							 bipolar      = None):

		try:
			settings = self['ohmmeterSettings']
			maxVoltage   = settings.get ('maxVoltage'   , maxVoltage  )
			bipolar      = settings.get ('bipolar'      , bipolar     )

		except KeyError : pass

		return (maxVoltage, bipolar)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

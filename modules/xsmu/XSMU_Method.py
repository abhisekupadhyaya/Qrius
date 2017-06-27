from cPickle import load
from XMethod import _XMethod, XMethodError

def Method (fd = None):

	try:
		method = load (fd) if fd != None else _Method()
		if not isinstance (method, _Method):
			raise AttributeError

	except (UnpicklingError, AttributeError, EOFError, ImportError, IndexError):
		raise XMethodError ('Not an XSMU method')

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

	def setMeterParameters (self, cm_autorange, cm_range,
							vm_autorange, vm_range, vm2_autorange, vm2_range):

		self['meterParameters'] = {
			'cm_autorange'  : cm_autorange,
			'cm_range'      : cm_range,
			'vm_autorange'  : vm_autorange,
			'vm_range'      : vm_range,
			'vm2_autorange' : vm2_autorange,
			'vm2_range'     : vm2_range
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setAcquisitionSettings (self, delay, filterLength):

		self['acquisitionSettings'] = {
			'delay'        : delay,
			'filterLength' : filterLength
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def set_IV_RampSettings (self, finalCurrent, finalVoltage, maxPower,
							 currentStep, voltageStep, bipolar, resTrackMode):

		self['IV_RampSettings'] = {
			'finalCurrent' : finalCurrent,
			'finalVoltage' : finalVoltage,
			'maxPower'     : maxPower,
			'currentStep'  : currentStep,
			'voltageStep'  : voltageStep,
			'bipolar'      : bipolar,
			'resTrackMode' : resTrackMode
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	
	def set_IV_TimeResolvedRampSettings (self, finalCurrent, finalVoltage, maxPower,
							 currentStep, voltageStep, bipolar, resTrackMode):

		self['IV_RampSettings'] = {
			'finalCurrent' : finalCurrent,
			'finalVoltage' : finalVoltage,
			'maxPower'     : maxPower,
			'currentStep'  : currentStep,
			'voltageStep'  : voltageStep,
			'bipolar'      : bipolar,
			'resTrackMode' : resTrackMode
		}

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setOhmmeterSettings (self, maxCurrent, maxVoltage,
							 maxPower, bipolar, resTrackMode):

		self['ohmmeterSettings'] = {
			'maxCurrent'   : maxCurrent,
			'maxVoltage'   : maxVoltage,
			'maxPower'     : maxPower,
			'bipolar'      : bipolar,
			'resTrackMode' : resTrackMode
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
							cm_autorange  = None,
							cm_range      = None,
							vm_autorange  = None,
							vm_range      = None,
							vm2_autorange = None,
							vm2_range     = None):

		try:
			parameters = self['meterParameters']
			cm_autorange  = parameters.get ('cm_autorange'  , cm_autorange )
			cm_range      = parameters.get ('cm_range'      , cm_range     )
			vm_autorange  = parameters.get ('vm_autorange'  , vm_autorange )
			vm_range      = parameters.get ('vm_range'      , vm_range     )
			vm2_autorange = parameters.get ('vm2_autorange' , vm2_autorange)
			vm2_range     = parameters.get ('vm2_range'     , vm2_range    )

		except KeyError : pass

		return (
			cm_autorange  , cm_range,
			vm_autorange  , vm_range,
			vm2_autorange , vm2_range)

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
							 finalCurrent = None,
							 finalVoltage = None,
							 maxPower     = None,
							 currentStep  = None,
							 voltageStep  = None,
							 bipolar      = None,
							 resTrackMode = None):

		try:
			settings = self['IV_RampSettings']
			finalCurrent = settings.get ('finalCurrent' , finalCurrent)
			finalVoltage = settings.get ('finalVoltage' , finalVoltage)
			maxPower     = settings.get ('maxPower'     , maxPower    )
			currentStep  = settings.get ('currentStep'  , currentStep )
			voltageStep  = settings.get ('voltageStep'  , voltageStep )
			bipolar      = settings.get ('bipolar'      , bipolar     )
			resTrackMode = settings.get ('resTrackMode' , resTrackMode)

		except KeyError : pass

		return (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	
	def get_IV_TimeResolvedRampSettings (self,
							 finalCurrent = None,
							 finalVoltage = None,
							 maxPower     = None,
							 currentStep  = None,
							 voltageStep  = None,
							 bipolar      = None,
							 resTrackMode = None):

		try:
			settings = self['IV_RampSettings']
			finalCurrent = settings.get ('finalCurrent' , finalCurrent)
			finalVoltage = settings.get ('finalVoltage' , finalVoltage)
			maxPower     = settings.get ('maxPower'     , maxPower    )
			currentStep  = settings.get ('currentStep'  , currentStep )
			voltageStep  = settings.get ('voltageStep'  , voltageStep )
			bipolar      = settings.get ('bipolar'      , bipolar     )
			resTrackMode = settings.get ('resTrackMode' , resTrackMode)

		except KeyError : pass

		return (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getOhmmeterSettings (self,
							 maxCurrent   = None,
							 maxVoltage   = None,
							 maxPower     = None,
							 bipolar      = None,
							 resTrackMode = None):

		try:
			settings = self['ohmmeterSettings']
			maxCurrent   = settings.get ('maxCurrent'   , maxCurrent  )
			maxVoltage   = settings.get ('maxVoltage'   , maxVoltage  )
			maxPower     = settings.get ('maxPower'     , maxPower    )
			bipolar      = settings.get ('bipolar'      , bipolar     )
			resTrackMode = settings.get ('resTrackMode' , resTrackMode)

		except KeyError : pass

		return (maxCurrent, maxVoltage, maxPower, bipolar, resTrackMode)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

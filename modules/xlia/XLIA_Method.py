from XMethod       import _XMethod, XMethodError
from cPickle       import load, UnpicklingError

def Method (fd = None):
	try:
		method = load (fd) if fd != None else _Method()
		if not isinstance (method, _Method) : raise AttributeError

	except (UnpicklingError, AttributeError, EOFError, ImportError, IndexError):
		raise XMethodError ('Not an XLIA method')

	return method

class _Method (_XMethod):

	def __init__ (self):
		_XMethod.__init__ (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, mode):
		self['runMode'] = mode

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setReferenceParameters (self, amplitude, frequency, phase):
		self['referenceParameters'] = {
			'amplitude' : amplitude,
			'frequency' : frequency,
			'phase'     : phase
		}

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setMeasurementSettings (
		self, inputChannel,
		preAmpCoupling, preAmpGain,
		postAmpGain, intgtrTC) :

		self['measurementSettings'] = {
			'inputChannel'   : inputChannel,
			'preAmpCoupling' : preAmpCoupling,
			'preAmpGain'     : preAmpGain,
			'postAmpGain'    : postAmpGain,
			'intgtrTC'       : intgtrTC
		}

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setAcquisitionSettings (
		self, delay, filterLength, driveMode,
		driveCurrentSetPoint, driveVoltageSetPoint):

		self['acquisitionSettings'] = {
			'delay'                : delay,
			'filterLength'         : filterLength,
			'driveMode'            : driveMode,
			'driveCurrentSetPoint' : driveCurrentSetPoint,
			'driveVoltageSetPoint' : driveVoltageSetPoint
		}

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def set_VF_RampSettings (
		self, initialFrequency, finalFrequency,
		linearFreqStep, logFreqStep, frequencySteppingMode):

		self['VF_RampSettings'] = {
			'initialFrequency'      : initialFrequency,
			'finalFrequency'        : finalFrequency,
			'linearFreqStep'        : linearFreqStep,
			'logFreqStep'           : logFreqStep,
			'frequencySteppingMode' : frequencySteppingMode
		}

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getRunMode (self, runMode):
		return self.get ('runMode', runMode)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getReferenceParameters (self,
								amplitude = None,
								frequency = None,
								phase     = None):

		try:
			parameters = self['referenceParameters']
			amplitude  = parameters.get ('amplitude' , amplitude)
			frequency  = parameters.get ('frequency' , frequency)
			phase      = parameters.get ('phase'     , phase    )

		except KeyError : pass
		return (amplitude, frequency, phase)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMeasurementSettings (self,
								inputChannel   = None,
								preAmpCoupling = None,
								preAmpGain     = None,
								postAmpGain    = None,
								intgtrTC       = None):

		try:
			settings       = self['measurementSettings']
			inputChannel   = settings.get ('inputChannel'   , inputChannel  )
			preAmpCoupling = settings.get ('preAmpCoupling' , preAmpCoupling)
			preAmpGain     = settings.get ('preAmpGain'     , preAmpGain    )
			postAmpGain    = settings.get ('postAmpGain'    , postAmpGain   )
			intgtrTC       = settings.get ('intgtrTC'       , intgtrTC      )

		except KeyError : pass

		return (inputChannel, preAmpCoupling,
		  preAmpGain, postAmpGain, intgtrTC)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getAcquisitionSettings (self,
								delay                = None,
								filterLength         = None,
								driveMode            = None,
								driveCurrentSetPoint = None,
								driveVoltageSetPoint = None):

		try:
			settings             = self['acquisitionSettings']

			delay                = settings.get ('delay'        , delay)
			filterLength         = settings.get ('filterLength' , filterLength)
			driveMode            = settings.get ('driveMode'    , driveMode)

			driveCurrentSetPoint = settings.get (
				'driveCurrentSetPoint', driveCurrentSetPoint)

			driveVoltageSetPoint = settings.get (
				'driveVoltageSetPoint', driveVoltageSetPoint)

		except KeyError: pass

		return (delay, filterLength, driveMode,
			driveCurrentSetPoint, driveVoltageSetPoint)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def get_VF_RampSettings (self,
							 initialFrequency      = None,
							 finalFrequency        = None,
							 linearFreqStep        = None,
							 logFreqStep           = None,
							 frequencySteppingMode = None):
		try:
			settings = self['VF_RampSettings']

			initialFrequency = settings.get (
				'initialFrequency', initialFrequency)

			finalFrequency = settings.get ('finalFrequency', finalFrequency)
			linearFreqStep = settings.get ('linearFreqStep', linearFreqStep)
			logFreqStep    = settings.get ('logFreqStep', logFreqStep)

			frequencySteppingMode = settings.get (
				'frequencySteppingMode', frequencySteppingMode)

		except KeyError: pass

		return (initialFrequency, finalFrequency,
			linearFreqStep, logFreqStep, frequencySteppingMode)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

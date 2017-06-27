from TCON_DataType import StepEntry
from TCON_DataType import StepTable
from XMethod       import _XMethod, XMethodError
from cPickle       import load, UnpicklingError

def Method (fd = None):
	try:
		method = load (fd) if fd != None else _Method()
		if not isinstance (method, _Method) : raise AttributeError

	except (UnpicklingError, AttributeError, EOFError, ImportError, IndexError):
		raise XMethodError ('Not a TCON method')

	return method

class _Method (_XMethod):

	def __init__ (self):
		_XMethod.__init__ (self)

	# ++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, mode):
		self['runMode'] = mode

	def setIsothermalSettings (self, setpoint):
		self['isothermalSettings'] = {
			'setpoint' : setpoint
		}

	def setRampSettings (self, finalTemperature, rampRate):
		self['rampSettings'] = {
			'finalTemperature' : finalTemperature,
			'rampRate'         : rampRate
		}

	def setStepSettings (self, stepTable):

		rows = dict()

		for i in range (len (stepTable)):

			entry = stepTable[i]

			row = {
				'initialTemperature' : entry.initialTemperature,
				'finalTemperature'   : entry.finalTemperature,
				'step'               : entry.step,
				'preDelay'           : entry.preDelay,
				'postDelay'          : entry.postDelay,
				'period'             : entry.period,
				'tolerance'          : entry.tolerance
			}

			rows[i] = row

		self['stepTable'] = rows

	def set_PID_Settings (self, P, I, D, IRange):
		PID = {
			'P' : P,
			'I' : I,
			'D' : D,
			'IRange' : IRange
		}

		self['PID'] = PID

	def set_cryostat_settings (self, method):
		self['cryostat_settings'] = method

	# ++++++++++++++++++++++++++++++++++++++++++

	def getRunMode (self, runMode = None):
		return self.get ('runMode', runMode)

	def getIsothermalSettings (self, setpoint = None):

		try:
			settings = self['isothermalSettings']
			setpoint = settings.get ('setpoint', setpoint)

		except KeyError : pass
		return setpoint

	def getRampSettings (self,
						 finalTemperature = None,
						 rampRate         = None):

		try:
			settings = self['rampSettings']
			finalTemperature = settings.get (
				'finalTemperature', finalTemperature)
			rampRate         = settings.get ('rampRate', rampRate)

		except KeyError : pass
		return (finalTemperature, rampRate)

	def getStepSettings (self):

		stepTable = StepTable()

		try:
			rows = self['stepTable']

			for i in sorted (rows.keys()):

				row   = rows.get (i)
				initialTemperature = row.get ('initialTemperature')
				finalTemperature   = row.get ('finalTemperature')
				step               = row.get ('step')
				preDelay           = row.get ('preDelay')
				postDelay          = row.get ('postDelay')
				period             = row.get ('period')
				tolerance          = row.get ('tolerance')

				entry = StepEntry (
					initialTemperature, finalTemperature,
					step, preDelay, postDelay, tolerance, period)

				stepTable.append (entry)

		except KeyError : pass

		return stepTable

	def get_PID_Settings (self,
						  P      = None,
						  I      = None,
						  D      = None,
						  IRange = None):

		try:
			PID    = self['PID']
			P      = PID.get ('P'      , P     )
			I      = PID.get ('I'      , I     )
			D      = PID.get ('D'      , D     )
			IRange = PID.get ('IRange' , IRange)

		except KeyError : pass
		return (P, I, D, IRange)

	def get_cryostat_settings (self, default_method = None):
		return self.get ('cryostat_settings', default_method)

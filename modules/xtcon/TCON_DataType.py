from time import time as systime
from TCON_Constants import *

class DataPoint:

	def __init__ (
			self, time = None, sampleTemperature = 0,
			heaterTemperature = 0, coldJuncTemperature = 0,
			heaterSetpoint = 0, heaterPower = 0):

		self.time = time if time != None else systime()
		self.sampleTemperature = sampleTemperature
		self.heaterTemperature = heaterTemperature
		self.coldJuncTemperature = coldJuncTemperature
		self.heaterSetpoint = heaterSetpoint
		self.heaterPower = heaterPower

class DataSet:

	def __init__ (self):
		self.dataset = []

	def clear (self):
		self.dataset = []

	def append (self, datapoint):
		self.dataset.append (datapoint)

	def size (self):
		return len (self.dataset)

	def empty (self):
		return len (self.dataset) == 0

	def __getitem__ (self, i): # Overloads [] operator
		return self.dataset[i]

	def getColumn (self, col):

		column = []
		for i in range (0, len (self.dataset)):

			datapoint = self.dataset[i]
			values = {
				DATASET_COL_TIME               : datapoint.time,
				DATASET_COL_SAMPLE_TEMPERATURE : datapoint.sampleTemperature,
				DATASET_COL_HEATER_TEMPERATURE : datapoint.heaterTemperature,
				DATASET_COL_CJ_TEMPERATURE     : datapoint.coldJuncTemperature,
				DATASET_COL_HEATER_SETPOINT    : datapoint.heaterSetpoint,
				DATASET_COL_HEATER_POWER       : datapoint.heaterPower
			}

			column.append (values.get (col))

		return column

class StepEntry:

	def __init__ (
		self,
		initialTemperature = None,
		finalTemperature   = None,
		step               = None,
		preDelay           = None,
		postDelay          = None,
		tolerance          = None,
		period             = None):

		self.initialTemperature = (initialTemperature
							 if initialTemperature != None else 0.0)

		self.finalTemperature   = (finalTemperature
							 if finalTemperature != None else 0.0)

		self.step      = step      if step      != None else 0.0
		self.preDelay  = preDelay  if preDelay  != None else 0.0
		self.postDelay = postDelay if postDelay != None else 0.0
		self.period    = period    if period    != None else 300.0
		self.tolerance = tolerance if tolerance != None else 0.1

	def contains (self, t):
		_min = min (self.finalTemperature, self.initialTemperature)
		_max = max (self.finalTemperature, self.initialTemperature)
		return (t != self.finalTemperature) and (t >= _min) and (t <= _max)

	def incomplete (self):

		if (self.initialTemperature == 0.0
		or  self.finalTemperature == 0.0):
			return True

		elif (self.initialTemperature != self.finalTemperature
		and self.step == 0.0):
			return True

		elif (self.period != 0.0 and self.tolerance == 0.0):
			return True

		else:
			return False

class StepTable:

	def __init__ (self):
		self.stepTable = []

	def __getitem__ (self, i): # Overloads x[i] operator
		return self.stepTable[i]

	def __setitem__ (self, i, entry): # Overloads x[i] = y operator
		self.stepTable[i] = entry

	def __len__ (self):
		return len (self.stepTable)

	def size (self):
		return len (self.stepTable)

	def empty (self):
		return len (self.stepTable) == 0

	def clear (self):
		self.stepTable = []

	def append (self, entry):
		self.stepTable.append (entry)

	def activeStepIndex (self, activeStepIndex, setpoint):

		for step in self.stepTable[activeStepIndex:]:
			if step.incomplete() or step.contains (setpoint):
				break

		index = None if step.incomplete() else self.stepTable.index(step)
		return index

	def nextTemperature (self, activeStepIndex, setpoint):

		activeStep = self.stepTable[activeStepIndex]

		if (setpoint == activeStep.finalTemperature):
			activeStepIndex += 1
			activeStep = self.stepTable[activeStepIndex]

		if not activeStep.incomplete():
			setpoint += activeStep.step
			setpoint = activeStep.step * round (setpoint / activeStep.step)
			if not activeStep.contains (setpoint):
				setpoint = activeStep.finalTemperature

		else:
			activeStepIndex = None
			setpoint = None

		return (activeStepIndex, setpoint)

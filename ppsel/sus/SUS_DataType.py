from time import time as systime
from SUS_Constants import *

class DataPoint:

	def __init__ (self, time = None,
				  refFrequency = 0.0,
				  currentAmplitude = 0.0, currentPhase = 0.0,
				  signalAmplitude = 0.0, signalPhase = 0.0,
				  chiP = 0.0, chiDP = 0.0,
				  sampleTemperature = 0.0, heaterTemperature = 0.0,
				  probePosition = 0.0):

		self.time                = time if (time != None) else systime()
		self.refFrequency        = refFrequency
		self.currentAmplitude    = currentAmplitude
		self.currentPhase        = currentPhase
		self.signalAmplitude     = signalAmplitude
		self.signalPhase         = signalPhase
		self.chiP                = chiP
		self.chiDP               = chiDP
		self.sampleTemperature   = sampleTemperature
		self.heaterTemperature   = heaterTemperature
		self.probePosition       = probePosition

class DataSet:

	def __init__ (self):
		self._dataset = []

	def clear (self):
		self._dataset = []

	def append (self, datapoint):
		self._dataset.append (datapoint)

	def size (self):
		return len (self._dataset)

	def empty (self):
		return True if (self.size() == 0) else False

	def __getitem__ (self, i): # Overloads [] operator
		return self._dataset[i]

	def getColumn (self, col):

		column = []
		for i in range (0, len (self._dataset)):

			datapoint = self._dataset[i]
			values = {
				DATASET_COL_TIME               : datapoint.time,
				DATASET_COL_REF_FREQ           : datapoint.refFrequency,
				DATASET_COL_CURRENT_AMPL       : datapoint.currentAmplitude,
				DATASET_COL_CURRENT_PHASE      : datapoint.currentPhase,
				DATASET_COL_SIGNAL_AMPL        : datapoint.signalAmplitude,
				DATASET_COL_SIGNAL_PHASE       : datapoint.signalPhase,
				DATASET_COL_CHIP               : datapoint.chiP,
				DATASET_COL_CHIDP              : datapoint.chiDP,
				DATASET_COL_SAMPLE_TEMPERATURE : datapoint.sampleTemperature,
				DATASET_COL_HEATER_TEMPERATURE : datapoint.heaterTemperature,
				DATASET_COL_PROBE_POSITION     : datapoint.probePosition
			}

			column.append (values.get (col))

		return column

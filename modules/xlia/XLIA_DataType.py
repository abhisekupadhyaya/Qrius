from time import time as systime
from XLIA_Constants import *

class DataPoint:

	def __init__ (self, time = None,
				  refAmplitude = 0.0, refFrequency = 0.0, refPhase = 0.0,
				  currentAmplitude = 0.0, currentPhase = 0.0,
				  signalAmplitude = 0.0, signalPhase = 0.0):

		self.time                = time if (time != None) else systime()
		self.refAmplitude        = refAmplitude
		self.refFrequency        = refFrequency
		self.refPhase            = refPhase
		self.currentAmplitude    = currentAmplitude
		self.currentPhase        = currentPhase
		self.signalAmplitude     = signalAmplitude
		self.signalPhase         = signalPhase

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
		for datapoint in self.dataset:

			values = {
				DATASET_COL_TIME           : datapoint.time,
				DATASET_COL_REF_AMPL       : datapoint.refAmplitude,
				DATASET_COL_REF_FREQ       : datapoint.refFrequency,
				DATASET_COL_REF_PHASE      : datapoint.refPhase,
				DATASET_COL_CURRENT_AMPL   : datapoint.currentAmplitude,
				DATASET_COL_CURRENT_PHASE  : datapoint.currentPhase,
				DATASET_COL_SIGNAL_AMPL    : datapoint.signalAmplitude,
				DATASET_COL_SIGNAL_PHASE   : datapoint.signalPhase
			}

			column.append (values.get (col))

		return column

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

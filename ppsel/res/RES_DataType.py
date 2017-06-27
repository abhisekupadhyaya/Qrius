from time import time as systime
from RES_Constants import *

class DataPoint:

	def __init__ (
			self, time = None,
			current = 0.0, voltage = 0.0, resistance = 0.0,
			sampleTemperature = 0.0, heaterTemperature = 0.0,
			magnetic_field = 0.0):

		self.time                = time if time != None else systime()
		self.current             = current
		self.voltage             = voltage
		self.resistance          = resistance
		self.sampleTemperature   = sampleTemperature
		self.heaterTemperature   = heaterTemperature
		self.magnetic_field      = magnetic_field

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
			DATASET_COL_CURRENT            : datapoint.current,
			DATASET_COL_VOLTAGE            : datapoint.voltage,
			DATASET_COL_RESISTANCE         : datapoint.resistance,
			DATASET_COL_SAMPLE_TEMPERATURE : datapoint.sampleTemperature,
			DATASET_COL_HEATER_TEMPERATURE : datapoint.heaterTemperature,
			DATASET_COL_MAGNETIC_FIELD     : datapoint.magnetic_field
			}

			column.append (values.get (col))

		return column

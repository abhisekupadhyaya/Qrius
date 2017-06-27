from time import time as systime
from XHIRES_Constants import *

class DataPoint:

	def __init__ (
		self, time = None, current = 0.0,
		voltage = 0.0, resistance = 0.0):

		self.time       = time if time != None else systime()
		self.current    = current
		self.voltage    = voltage
		self.resistance = resistance

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
				DATASET_COL_TIME       : datapoint.time,
				DATASET_COL_CURRENT    : datapoint.current,
				DATASET_COL_VOLTAGE    : datapoint.voltage,
				DATASET_COL_RESISTANCE : datapoint.resistance
			}

			column.append (values.get (col))

		return column

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

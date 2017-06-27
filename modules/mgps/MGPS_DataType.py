from time import time as systime
from MGPS_Constants import *

class DataPoint:

	def __init__ (
		self, time = None,
		magnetic_field = 0.0, current = 0.0, voltage = 0.0):

		self.time 		 	= time if time != None else systime()
		self.magnetic_field = magnetic_field
		self.current    	= current
		self.voltage    	= voltage

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
				DATASET_COL_TIME       		 : datapoint.time,
				DATASET_COL_MAGNETIC_FIELD   : datapoint.magnetic_field,
				DATASET_COL_CURRENT    		 : datapoint.current,
				DATASET_COL_VOLTAGE    		 : datapoint.voltage
			}

			column.append (values.get (col))

		return column

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

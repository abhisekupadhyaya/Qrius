from time import time as systime
from XMC_Constants import *

class DataPoint:

	def __init__ (self, time = None, position = 0):

		self.time = time if time != None else systime()
		self.position = position

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
				DATASET_COL_POSITION           : datapoint.position
			}

			column.append (values.get (col))

		return column

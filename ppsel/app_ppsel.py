#!/usr/bin/python
# coding: utf-8

from Tkinter import Button, NSEW
from ppsel_constants import *

class GUI:

	def __init__(self, master):
		"""
		"""
		self.master = master
		master.title ('Physical property selection')
		self.populateWindow (master)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def populateWindow (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 300)

		row = 0; col = 0

		w = Button (
			self.master,
			text = 'Electrical DC conductivity \n I-V, R-T, R-T-H',
			command = self.wResCB, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

		row += 1
		w = Button (
			self.master,
			text = 'Electrical DC high resistivity \n I-V & R-T',
			command = self.wHiResCB, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

		row += 1
		w = Button (
			self.master, text = 'Magnetic AC susceptibility \n χ-F & χ-T',
			command = self.wSusCB, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

	def wResCB (self, *args):
		self.do_callback (OPEN_MODULE, RESISTIVITY)

	def wHiResCB (self, *args):
		self.do_callback (OPEN_MODULE, HIGH_RESISTIVITY)

	def wSusCB (self, *args):
		self.do_callback (OPEN_MODULE, SUSCEPTIBILITY)

from Tkinter import Button, NSEW
from modules_constants import *

class GUI:

	def __init__ (self, master):

		self.master = master
		master.title ('Modules manager')
		self.populateWindow (master)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def populateWindow (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 300)

		# ++++++++++++++++++++++++++++++++++++++++++++++++=

		row = 0; col = 0

		w = Button (
			master, text = 'Cryostat and insert',
			command = self.btn_cryostat_cb, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++=

		row += 1

		w = Button (
			master, text = 'Temperature controller',
			command = self.w_XTCON_CB, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++=

		row += 1

		w = Button (
			master, text = 'I-V source and measurement unit',
			command = self.w_XSMU_CB, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++=

		row += 1

		w = Button (
			master, text = 'Lock-in amplifier',
			command = self.w_XLIA_CB, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++=

		row += 1

		w = Button (
			master, text = 'Sample positioner',
			command = self.w_XMC_CB, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++=

		row += 1

		w = Button (
			master, text = 'High Resistance Measurement unit',
			command = self.w_XHIRES_CB, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++=

		row += 1

		w = Button (
			master, text = 'Magnet Power Supply',
			command = self.w_MGPS_CB, height = 3)

		w.grid (row = row, column = col, sticky = NSEW)

	def btn_cryostat_cb (self, *args):
		self.do_callback (OPEN_DEVICE, CRYOSTAT)

	def w_XTCON_CB (self, *args):
		self.do_callback (OPEN_DEVICE, XTCON)

	def w_XSMU_CB (self, *args):
		self.do_callback (OPEN_DEVICE, XSMU)

	def w_XLIA_CB (self, *args):
		self.do_callback (OPEN_DEVICE, XLIA)

	def w_XMC_CB (self, *args):
		self.do_callback (OPEN_DEVICE, XMC)

	def w_XHIRES_CB (self, *args):
		self.do_callback (OPEN_DEVICE, XHIRES)

	def w_MGPS_CB (self, *args):
		self.do_callback (OPEN_DEVICE, MGPS)

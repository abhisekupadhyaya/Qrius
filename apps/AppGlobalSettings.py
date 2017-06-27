import os
import Preferences
import tkFileDialog

from Tkinter import Label, LabelFrame, Entry, Button, OptionMenu, Frame
from Tkinter import NSEW, N, S, E, W, NORMAL, DISABLED, LEFT, RIGHT
from Tkinter import StringVar, TclError

from XWidget import XFloatEntry

from xsmu    import Driver as XSMU_Driver
from xlia    import Driver as XLIA_Driver
from tcon    import Driver as XTCON_Driver
from XMC     import Driver as XMC_Driver
from xhires  import Driver as XHIRES_Driver
from mgps    import Driver as MGPS_Driver

m_to_mm = 1e3
mm_to_m = 1e-3

class AppGlobalSettings:

	CB_CONTEXT_OK     = 0
	CB_CONTEXT_CANCEL = 1

	def __init__ (self, master):
		self.master = master
		self.populateWindow (master)
		self._callback = self.default_callback

	def default_callback (self, caller, context):
		pass

	def callback (self, cb):
		self._callback = cb

	def populateWindow (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.title ('Qrius: Preferences dialog')
		master.protocol ('WM_DELETE_WINDOW', self.wCancelCB)

		w = LabelFrame (master, text = 'User settings')
		w.grid (row = 0, column = 0, sticky = NSEW,
				padx = 5, pady = 5, ipady = 5)
		self.populateUserPreferencesFrame (w)

		w = LabelFrame (master, text = 'System settings' + (
				'' if self.is_admin() else ' (need to be administrator)'))
		w.grid (row = 1, column = 0, sticky = NSEW,
				padx = 5, pady = 5, ipady = 5)
		self.populateSystemPreferencesFrame (w)
		#self.enable_group (w, enable = True if self.is_admin() else False)

		w = LabelFrame (master, borderwidth = 0)
		w.grid (row = 2, column = 0, sticky = NSEW, padx = 5, pady = 5)
		self.populateOkCancelFrame (w)

	def populateUserPreferencesFrame (self, wFrame):

		wFrame.grid_columnconfigure (0, weight = 0)
		wFrame.grid_columnconfigure (1, weight = 1)
		wFrame.grid_columnconfigure (2, weight = 0)

		col_widths = [10, 30, 10]

		row = 0; col = 0
		w = Label (wFrame, text = 'Data folder',
					anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		self.dataFolder = StringVar()
		self.dataFolder.set (Preferences.getDataFolder())
		w = Entry (wFrame, textvariable = self.dataFolder,
					width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Button (wFrame, text = 'Browse',
					command = self.wDataFolderBrowseCB,
					width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

	def populateSystemPreferencesFrame (self, wFrame):

		wFrame.grid_columnconfigure (0, weight = 1)
		wFrame.grid_columnconfigure (1, weight = 1)

		col_widths = [30, 15]

		row = 0; col = 0
		w = Label (wFrame, text = 'Sample temperature sensor',
					anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		self.strSampleTemperatureSensors = [
			'K-type thermocouple',
			'PT100'
		]

		self.sampleTemperatureSensor = StringVar()
		self.sampleTemperatureSensor.set (
			self.strSampleTemperatureSensors [
				Preferences.getSampleTemperatureSensor()])
		w = OptionMenu (wFrame, self.sampleTemperatureSensor,
						  *self.strSampleTemperatureSensors)
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++

		row += 1; col = 0
		w = Label (wFrame, text = 'Linac stroke length (mm)',
					anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		col += 1

		w = self.linacStrokeLength = XFloatEntry (
				master = wFrame, bg = 'white', justify = LEFT,
				borderwidth = 2, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)
		w.set (Preferences.get_XMC_linacStrokeLength() * m_to_mm)

		# +++++++++++++++++++++++

		row += 1; col = 0
		w = Label (wFrame, text = 'Linac pitch (mm)',
					anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		col += 1

		w = self.linacPitch = XFloatEntry (
				master = wFrame, bg = 'white', justify = LEFT,
				borderwidth = 2, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)
		w.set (Preferences.get_XMC_linacPitch() * m_to_mm)

		# +++++++++++++++++++++++

		row += 1; col = 0
		w = Label (wFrame, text = 'XSMU serial number',
					anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		oDriver = XSMU_Driver()
		serialNos = oDriver.scan()
		self.xsmuSerialNos = serialNos if len (serialNos) > 0 else ['']
		self.xsmuSerialNo = StringVar()
		self.xsmuSerialNo.set (Preferences.get_XSMU_serialNo())
		w = OptionMenu (wFrame, self.xsmuSerialNo, *self.xsmuSerialNos)
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++

		row += 1; col = 0
		w = Label (wFrame, text = 'XTCON serial number',
					anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		oDriver = XTCON_Driver()
		serialNos = oDriver.scan()
		self.xtconSerialNos = serialNos if len (serialNos) > 0 else ['']
		self.xtconSerialNo = StringVar()
		self.xtconSerialNo.set (Preferences.get_XTCON_serialNo())
		w = OptionMenu (wFrame, self.xtconSerialNo, *self.xtconSerialNos)
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++

		row += 1; col = 0
		w = Label (wFrame, text = 'XLIA serial number',
					anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		oDriver = XLIA_Driver()
		serialNos = oDriver.scan()
		self.xliaSerialNos = serialNos if len (serialNos) > 0 else ['']
		self.xliaSerialNo = StringVar()
		self.xliaSerialNo.set (Preferences.get_XLIA_serialNo())
		w = OptionMenu (wFrame, self.xliaSerialNo, *self.xliaSerialNos)
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++

		row += 1; col = 0
		w = Label (wFrame, text = 'XMC serial number',
					anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		oDriver = XMC_Driver()
		serialNos = oDriver.scan()
		self.xmcSerialNos = serialNos if len (serialNos) > 0 else ['']
		self.xmcSerialNo = StringVar()
		self.xmcSerialNo.set (Preferences.get_XMC_serialNo())
		w = OptionMenu (wFrame, self.xmcSerialNo, *self.xmcSerialNos)
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++

		row += 1; col = 0
		w = Label (wFrame, text = 'XHIRES serial number',
					anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		oDriver = XHIRES_Driver()
		serialNos = oDriver.scan()
		self.xhiresSerialNos = serialNos if len (serialNos) > 0 else ['']
		self.xhiresSerialNo = StringVar()
		self.xhiresSerialNo.set (Preferences.get_XHIRES_serialNo())
		w = OptionMenu (wFrame, self.xhiresSerialNo, *self.xhiresSerialNos)
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++

		row += 1; col = 0
		w = Label (wFrame, text = 'MGPS serial number',
					anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		oDriver = MGPS_Driver()
		serialNos = oDriver.scan()
		self.mgpsSerialNos = serialNos if len (serialNos) > 0 else ['']
		self.mgpsSerialNo = StringVar()
		self.mgpsSerialNo.set (Preferences.get_MGPS_serialNo())
		w = OptionMenu (wFrame, self.mgpsSerialNo, *self.mgpsSerialNos)
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

	def populateOkCancelFrame (self, wFrame):

		wFrame.grid_columnconfigure (0, weight = 1)
		wFrame.grid_columnconfigure (1, weight = 0)
		wFrame.grid_columnconfigure (2, weight = 0)

		w = Frame (wFrame)
		w.grid (row = 0, column	= 0, sticky = NSEW)

		w = Button (wFrame, text = 'Ok',
							command = self.wOkCB, width = 10)
		w.grid (row = 0, column	= 1, sticky = NSEW)

		w = Button (wFrame, text = 'Cancel',
							command = self.wCancelCB, width = 10)
		w.grid (row = 0, column	= 2, sticky = NSEW)

	def wDataFolderBrowseCB (self):
		folder = self.dataFolder.get()
		folder = tkFileDialog.askdirectory (initialdir = folder,
				parent = self.master, title = 'Choose Qrius data folder')

		if isinstance (folder, str) and (folder != ''):
			self.dataFolder.set (folder)

	def wOkCB (self):
		# User settings
		Preferences.setDataFolder (self.dataFolder.get())

		Preferences.setSampleTemperatureSensor (
			self.strSampleTemperatureSensors.index (
				self.sampleTemperatureSensor.get()))

		Preferences.set_XMC_linacStrokeLength (
			self.linacStrokeLength.get() * mm_to_m)

		Preferences.set_XMC_linacPitch (
			self.linacPitch.get() * mm_to_m)

		Preferences.set_XSMU_serialNo (self.xsmuSerialNo.get())
		Preferences.set_XTCON_serialNo (self.xtconSerialNo.get())
		Preferences.set_XLIA_serialNo (self.xliaSerialNo.get())
		Preferences.set_XMC_serialNo (self.xmcSerialNo.get())
		Preferences.set_XHIRES_serialNo (self.xhiresSerialNo.get())
		Preferences.set_MGPS_serialNo (self.mgpsSerialNo.get())

		Preferences.flush()
		self.do_callback (context = self.CB_CONTEXT_OK)

	def wCancelCB (self):
		self.do_callback (context = self.CB_CONTEXT_CANCEL)

	def do_callback (self, context):
		self._callback (caller = self, context = context)

	def is_admin (self):
		return True if os.geteuid() == 0 else False

	def enable_group (self, wGroup, enable = True):

		try:

			wGroup.configure (state = NORMAL if enable else DISABLED)

		except TclError:
			pass

		for child in wGroup.winfo_children():
			self.enable_group (child, enable = enable)

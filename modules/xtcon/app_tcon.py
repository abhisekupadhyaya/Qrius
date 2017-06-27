# coding: utf-8
from Tkinter import *
from tkValidatingEntry import *
import tkFont
from tkFileDialog import askopenfile, asksaveasfile
import os

from XWidget import XFloatEntry, XIntegerEntry, XScroll, XTab
from TCON_DataType import StepEntry
from time import time as systime, localtime
from TCON_Constants import *
from TCON_Banner    import banner

import Plot2D
import Preferences

class GUI:

	runModeMenuItems = {
		RUN_MODE_MONITOR      : 'Monitor',
		RUN_MODE_ISOTHERMAL   : 'Isothermal',
		RUN_MODE_LINEAR_RAMP  : 'Linear ramp',
		RUN_MODE_STEPPED_RAMP : 'Step ramp'
	}

	methodFileTypes = [
		('XPLORE method files' , '*.xmt'),
		('All files'           , '*.*')
	]

	def __init__ (self, master, sample):
		self.master = master
		self.sample = sample
		self.master.title ('Temperature Controller')
		self.createWidgets (master)
		self.setRunMode (RUN_MODE_MONITOR)
		self.putBanner()

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def close (self):
		for (w, r, c) in (self.wIsothermalSettingsDisplay,
						  self.wRampSettingsDisplay,
						  self.wSteppedRampDisplay):
			w.close()

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 200)
		master.grid_columnconfigure (1, weight = 1, minsize = 700)
		master.grid_rowconfigure    (0, weight = 1, minsize = 575)
		master.grid_rowconfigure    (1, weight = 0, minsize = 25)

		self.populateMenu (master)

		row = 0; col = 0
		w = XScroll (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populateDisplayPanel (w.interior)

		col += 1
		w = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populatePlotPanel (w)

		row += 1; col = 0
		w = Frame (master)
		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)
		self.populateStatusPanel (w)

	def populateMenu (self, master):

		### Main Menu
		self.mainmenu = Menu (master)
		self.mainmenu.config (borderwidth = 1)
		master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.utilmenu = Menu (self.mainmenu)
		self.utilmenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'Settings', menu = self.utilmenu, underline = 0)

		self.toolmenu = Menu (self.mainmenu)
		self.toolmenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'Tools', menu = self.toolmenu, underline = 0)

		# ++++ Populating file menu ++++

		menu_items = [
			('Connect'     , self.wConnectDeviceCB),
			('Open method' , self.wOpenMethodCB),
			('Save method' , self.wSaveMethodCB),
			('Hide'        ,    self.wHideCB)
		]

		for (l, c) in menu_items:
			self.filemenu.add_command (label = l, command = c)

		# ++++ Populating settings menu ++++

		menu_items = [
			('Isothermal settings',   self.wIsothermalSettingsCB),
			('Linear ramp settings',  self.wRampSettingsCB),
			('Stepped ramp settings', self.wStepSettingsCB),
			('PID settings',          self.wPIDSettingsCB)
		]

		for (l, c) in menu_items:
			self.utilmenu.add_command (label = l, command = c)

		# ++++ Populating tools menu ++++

		menu_items = [
			('Calibration', self.wCalibrationCB)
		]

		for (l, c) in menu_items:
			self.toolmenu.add_command (label = l, command = c)

	def populateDisplayPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# ++++ Instrument control ++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Instrument control')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateInstrumentControlFrame (w)

		# ++++ Heater temperature display ++++

		row += 1; col = 0
		w = LabelFrame (master, text = 'Heater temperature')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateHeaterTemperatureFrame (w)

		# ++++ Heater power and setpoint display ++++

		row += 1; col = 0
		w = LabelFrame (master, text = 'Heater power and setpoint')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateHeaterPowerFrame (w)

		# ++++ Sample temperature display ++++

		row += 1; col = 0
		w = LabelFrame (master, text = 'Sample temperature')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateSampleTemperatureFrame (w)

		# ++++ Start-stop Control ++++

		row += 1; col = 0
		w = LabelFrame (master, text = 'Control')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateControlFrame (w)

		# +++++ Settings display ++++

		row += 1; col = 0

		(w, r, c) = self.wIsothermalSettingsDisplay = (
			GUI_IsothermalSettingsDisplay (master = Frame (master)),
			row, col)

		(w, r, c) = self.wRampSettingsDisplay = (
			GUI_RampSettingsDisplay (master = Frame (master)),
			row, col)

		(w, r, c) = self.wSteppedRampDisplay = (
			GUI_SteppedRampDisplay (master = Frame (master)),
			row, col)

	def populateInstrumentControlFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = self.wTCON = Button (
			master, text = 'Cryostat and insert',
			command = self.wCryostatCB)

		w.grid (row = row, column = col, sticky = NSEW)

	def populateHeaterTemperatureFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		row = 0; col = 0
		w = self.wHeaterTempK = \
			Label (master, text = '0.00', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		self.setParamFont (w)

		col += 1
		w = Label (master, text = 'K', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.setParamFont (w)

		row += 1; col = 0
		w = self.wHeaterTempC = \
			Label (master, text = '0.00', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = '°C', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

	def populateHeaterPowerFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		row = 0; col = 0
		w = self.wHeaterPower = \
			Label (master, text = '0', anchor = E)
		self.setParamFont (w)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = '%', anchor = W)
		self.setParamFont (w)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = self.wHeaterSetpointK = \
			Label (master, text = '0.0', anchor = E)
		self.setParamFont (w)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = 'K', anchor = W)
		self.setParamFont (w)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = self.wHeaterSetpointC = \
			Label (master, text = '0.0', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = '°C', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

	def populateSampleTemperatureFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		row = 0; col = 0
		w = self.wSampleTempK = \
			Label (master, text = '0.00', fg = 'blue', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		self.setParamFont (w)

		col += 1
		w = Label (master, fg = 'blue', text = 'K', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.setParamFont (w)

		row += 1; col = 0
		w = self.wSampleTempC = \
			Label (master, text = '0.00', fg = 'blue', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, fg = 'blue', text = '°C', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

	def populateControlFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 125)
		master.grid_columnconfigure (1, weight = 1, minsize = 125)

		row = 0; col = 0
		w = Label (master, text = "Control mode: ")
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		var = self.runMode = StringVar()
		options = self.runModeMenuItems.values()
		w = self.wRunMode = OptionMenu (
			master, var, *options, command = self.wRunModeCB)
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = self.wStart = Button (
			master, text = 'Start', command = self.wStartCB)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wFinish = Button (
			master, text = 'Finish', state = DISABLED,
			command = self.wFinishCB)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def populatePlotPanel (self, master):

		master.grid_rowconfigure    (0, weight = 1)
		master.grid_columnconfigure (0, weight = 1)

		w = self.wPlots = XTab (master)
		w.grid (row = 0, column = 0, sticky = NSEW)

	def newPlot (self, name):
		return Plot2D.Plot2D (self.wPlots.add (name))

	def clearPlot (self):
		self.wPlots.clear()
		self.putBanner()

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateStatusPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_rowconfigure    (0, weight = 1)

		row = 0; col = 0
		w = self.wStatus = Label (master, text = '...', anchor = W, width = 10)
		w.grid (row = row, column = col, sticky = NSEW)

	def setParamFont (self, widget, mul = 2, weight = 'bold'):
		font = tkFont.Font (widget, widget['font'])
		font.config (size = mul * font['size'], weight = weight)
		widget.config (font = font)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setConnectionStatus (self, status):

		if status == DEVICE_CONNECTING:
			self.filemenu.entryconfig (
				0, label = 'Connecting', state = DISABLED, command = None)

		elif status == DEVICE_CONNECTED:
			self.filemenu.entryconfig (
				0, label = 'Disconnect', state = NORMAL,
				command = self.wDisconnctDeviceCB)

			self.set_status ('Temperature controller conntected')

		elif status == DEVICE_DISCONNECTING:
			self.filemenu.entryconfig (
				0, label = 'Disconnecting', state = DISABLED, command = None)

		elif status == DEVICE_DISCONNECTED:
			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.set_status ('Temperature controller disconnected')

		elif status == DEVICE_NOT_FOUND:
			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.set_status ('Temperature controller not found')

		else: raise ValueError (status)

	def wCryostatCB (self, *args):
		self.do_callback (OPEN_DEVICE, CRYOSTAT_DEVICE)

	def wHideCB (self):
		self.master.withdraw()

	def wConnectDeviceCB (self):
		self.do_callback (CONNECT_DEVICE)

	def wDisconnctDeviceCB (self):
		self.do_callback (DISCONNECT_DEVICE)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wOpenMethodCB (self, *args):

		try:
			(sampleName, sampleID, _) = self.sample.get()

			folder = os.path.join (Preferences.getDataFolder(),
								   sampleName + sampleID,
								   'method')

			if not os.path.exists (folder) : os.makedirs (folder)

			fd = askopenfile (parent = self.master,
				initialdir = folder, filetypes = self.methodFileTypes)

			if fd != None : self.do_callback (OPEN_METHOD, fd)

		except (OSError, IOError) as e:
			self.set_status (str (e))

	def wSaveMethodCB (self, *args):

		try:
			(sampleName, sampleID, _) = self.sample.get()

			folder = os.path.join (Preferences.getDataFolder(),
								   sampleName + sampleID,
								   'method')

			if not os.path.exists (folder) : os.makedirs (folder)

			fd = asksaveasfile (parent = self.master,
				initialdir = folder, filetypes = self.methodFileTypes)

			if fd != None : self.do_callback (SAVE_METHOD, fd)

		except (OSError, IOError) as e:
			self.set_status (str (e))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wIsothermalSettingsCB (self):
		self.do_callback (OPEN_DIALOG, ISOTHERMAL_DIALOG)

	def wRampSettingsCB (self):
		self.do_callback (OPEN_DIALOG, LINEAR_RAMP_DIALOG)

	def wStepSettingsCB (self):
		self.do_callback (OPEN_DIALOG, STEP_TABLE_DIALOG)

	def wPIDSettingsCB (self):
		self.do_callback (OPEN_DIALOG, PID_SETTINGS_DIALOG)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wCalibrationCB (self):
		self.do_callback (OPEN_DIALOG, CALIBRATION_DIALOG)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setHeaterTemperature (self, K):
		self.wHeaterTempK.config (text = str ('%.2f' % K))
		self.wHeaterTempC.config (text = str ('%.2f' % (K - 273)))

	def setHeaterPower (self, pwr):
		self.wHeaterPower.config (text = str ('%.0f' % (100.0 * pwr)))

	def setHeaterSetpoint (self, K):
		self.wHeaterSetpointK.config (text = str ('%.1f' % K))
		self.wHeaterSetpointC.config (text = str ('%.1f' % (K - 273)))

	def setSampleTemperature (self, K):
		self.wSampleTempK.config (text = str ('%.2f' % K))
		self.wSampleTempC.config (text = str ('%.2f' % (K - 273)))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wStartCB (self):
		self.do_callback (START_RUN, self.getRunMode())

	def wFinishCB (self):
		self.do_callback (FINISH_RUN)

	def setRunControlStatus (self, status):

		if status == RUN_STARTING:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config (text = 'Starting', state = DISABLED)
			self.wFinish.config (text = 'Finish', state = DISABLED)

		elif status == RUN_STARTED:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config (text = 'Started', state = DISABLED)
			self.wFinish.config (text = 'Finish', state = NORMAL)

		elif status == RUN_FINISHING:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config (text = 'Started', state = DISABLED)
			self.wFinish.config (text = 'Finishing', state = DISABLED)

		elif status == RUN_FINISHED:
			self.wRunMode.config (state = NORMAL)
			self.wStart.config (text = 'Start', state = NORMAL)
			self.wFinish.config (text = 'Finish', state = DISABLED)

	def set_status (self, text):

		lt = localtime (systime())
		time_stamp = (
			str ('%02d' % lt.tm_hour) + ':' +
			str ('%02d' % lt.tm_min)  + ':' +
			str ('%02d' % lt.tm_sec))

		text = '<' + time_stamp + ':TCON> ' + text
		print text

		old_text = self.wStatus['text']
		new_text = text + '    .    ' + old_text
		new_text = new_text[:1024]
		self.wStatus['text'] = new_text

	def wRunModeCB (self, *args):
		self.do_callback (RUN_MODE, self.getRunMode())

	def getRunMode (self):
		runModes = {v : k for (k, v) in self.runModeMenuItems.items()}
		return runModes.get (self.runMode.get())

	def setRunMode (self, mode):

		self.runMode.set (self.runModeMenuItems.get (mode))

		[w.master.grid_forget()
			for (w, row, col) in (
				self.wIsothermalSettingsDisplay,
				self.wRampSettingsDisplay,
				self.wSteppedRampDisplay)]

		if mode == RUN_MODE_MONITOR : pass

		elif mode == RUN_MODE_ISOTHERMAL:
			(w, row, col) = self.wIsothermalSettingsDisplay
			w.master.grid (row = row, column = col, sticky = NSEW)

		elif mode == RUN_MODE_LINEAR_RAMP:
			(w, row, col) = self.wRampSettingsDisplay
			w.master.grid (row = row, column = col, sticky = NSEW)

		elif mode == RUN_MODE_STEPPED_RAMP:
			(w, row, col) = self.wSteppedRampDisplay
			w.master.grid (row = row, column = col, sticky = NSEW)

		else: raise ValueError (mode)

	def setIsothermalSettingsDisplay (self, heaterSetpoint):
		(w, row, col) = self.wIsothermalSettingsDisplay
		w.set (heaterSetpoint)

	def setRampSettingsDisplay (self, finalTemperature, rate):
		(w, row, col) = self.wRampSettingsDisplay
		w.set (finalTemperature, rate)

	def setSteppedRampDisplay (self, state, *args):
		(w, row, col) = self.wSteppedRampDisplay
		w.set (state, *args)

	def putBanner (self):
		w = GUI_Banner (self.wPlots.add ('Welcome'))
		w.grid (row = 0, column = 0, sticky = NSEW)

class GUI_Banner (Frame):

	def __init__ (self, master):
		Frame.__init__ (self, master)
		self.createWidgets (self)

	def createWidgets (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_rowconfigure (0, weight = 1)
		photo = self.photo = PhotoImage (data = banner)
		w = Label (master, image = photo)
		w.grid (row = 0, column = 0, sticky = NSEW)

class GUI_IsothermalSettings:

	def __init__(self, master, setpoint):
		self.master = master
		self.master.title ('Isothermal settings')
		self.createWidgets()
		self.set (setpoint)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self):

		### Main Menu
		self.mainmenu = Menu (self.master)
		self.mainmenu.config (borderwidth = 1)
		self.master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)
		self.filemenu.add_command (
			label = 'Apply', command = self.wApplyCB)
		self.filemenu.add_command (
			label = 'Cancel', command = self.wCancelCB)

		self.master.grid_rowconfigure (0, weight = 1)
		self.master.grid_columnconfigure (0, weight = 1)

		# ++++ Temperature settings ++++
		w = wFrame = LabelFrame (
				self.master, text = 'Temperature settings')

		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)

		# ++++ Heater setpoint ++++
		w = Label (wFrame, text = 'Heater setpoint (K):', anchor = E)
		w.grid (row = 0, column = 0, sticky = NSEW)

		w = self.wSetpoint = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 0, column = 1, sticky = NSEW)
		w.enable_color (enable = False)

	def wApplyCB (self):
		self.do_callback (APPLY, self.wSetpoint.get())

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, setpoint):
		self.wSetpoint.set (setpoint)

class GUI_IsothermalSettingsDisplay:

	instances = []

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		self.instances.append (self)
		self.set (heaterSetpoint = 0.0)

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Isothermal settings')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

		self.populateSettings (w)

	def populateSettings (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 150)
		master.grid_columnconfigure (1, weight = 1, minsize = 50)
		master.grid_columnconfigure (2, weight = 0, minsize = 50)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Heater setpoint', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wHeaterSetpoint = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = 'K', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

	def _set (self, heaterSetpoint):
		self.wHeaterSetpoint.config (text = str ('%.1f' % heaterSetpoint))

	def set (self, heaterSetpoint):
		for o in self.instances:
			o._set (heaterSetpoint)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_RampSettings:

	def __init__(self, master, finalTemperature, rate):
		self.master = master
		self.master.title ('Ramp settings')
		self.createWidgets()
		self.set (finalTemperature, rate)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self):

		### Main Menu
		self.mainmenu = Menu (self.master)
		self.mainmenu.config (borderwidth = 1)
		self.master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)
		self.filemenu.add_command (
			label = 'Apply', command = self.wApplyCB)
		self.filemenu.add_command (
			label = 'Cancel', command = self.wCancelCB)

		self.master.grid_rowconfigure (0, weight = 1)
		self.master.grid_columnconfigure (0, weight = 1)

		# ++++ Temperature settings ++++
		w = wFrame = LabelFrame (
				self.master, text = 'Temperature settings')

		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)

		# ++++ Final temperature ++++
		w = Label (wFrame, text = 'Final temperature (K):', anchor = E)
		w.grid (row = 0, column = 0, sticky = NSEW)

		w = self.wFinalTemperature = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 0, column = 1, sticky = NSEW)
		w.enable_color (enable = False)

		# ++++ Final temperature ++++
		w = Label (wFrame, text = 'Ramp rate (K/min):', anchor = E)
		w.grid (row = 1, column = 0, sticky = NSEW)

		w = self.wRate = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 1, column = 1, sticky = NSEW)
		w.enable_color (enable = False)

	def wApplyCB (self):
		self.do_callback (
			APPLY,
			self.wFinalTemperature.get(),
			self.wRate.get())

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, finalTemperature, rate):
		self.wFinalTemperature.set (finalTemperature)
		self.wRate.set (rate)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_RampSettingsDisplay:

	instances = []

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		self.instances.append (self)
		self.set (finalTemperature = 0.0, rate = 0.0)

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Linear ramp settings')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

		self.populateSettings (w)

	def populateSettings (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 150)
		master.grid_columnconfigure (1, weight = 1, minsize = 50)
		master.grid_columnconfigure (2, weight = 0, minsize = 50)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Final temperature', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wFinalTemperature = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = 'K', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Rate', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wRate = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = 'K/min', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

	def _set (self, finalTemperature, rate):
		self.wFinalTemperature.config (text = str ('%.1f' % finalTemperature))
		self.wRate.config (text = str ('%.1f' % rate))

	def set (self, finalTemperature, rate):
		for o in self.instances:
			o._set (finalTemperature, rate)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_StepSettings:

	def __init__(self, master, stepTable):
		self.master = master
		self.master.title ('Temperature ramp settings')
		self.createWidgets()

		self.stepIndex = 0
		self.stepTable = stepTable

		self.setEntryBoxes (self.stepIndex)
		self.fillRampTable()

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self):

		### Main Menu
		self.mainmenu = Menu (self.master)
		self.mainmenu.config (borderwidth = 1)
		self.master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (label = 'New', command = self.wNewCB)
		#self.filemenu.add_command (label = 'Open', command = self.wOpenCB)
		#self.filemenu.add_command (label = 'Save', command = self.wSaveCB)
		#self.filemenu.add_separator()
		self.filemenu.add_command (label = 'Apply', command = self.wApplyCB)
		self.filemenu.add_command (label = 'Cancel', command = self.wCancelCB)

		self.master.grid_rowconfigure (0, weight = 1)
		self.master.grid_columnconfigure (0, weight = 1)

		# ++++ Temperature ramp (step mode) ++++
		w = wFrame = LabelFrame (
				self.master, text = 'Temperature ramp (step mode)')

		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)
		w.grid_columnconfigure (2, weight = 0)
		w.grid_columnconfigure (3, weight = 1)
		w.grid_rowconfigure (0, weight = 0)
		w.grid_rowconfigure (1, weight = 0)
		w.grid_rowconfigure (2, weight = 0)
		w.grid_rowconfigure (3, weight = 0)
		w.grid_rowconfigure (4, weight = 1)

		# ++++ Step zones ++++
		w = Label (wFrame, text = 'Ramp index:', anchor = E)
		w.grid (row = 0, column = 0, sticky = NSEW)

		w = self.wRampIndex = XIntegerEntry (
				wFrame, bg = 'white', width = 1,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 0, column = 1, sticky = NSEW)
		w.enable_color (enable = False)
		w.callback (self.wRampIndexCB)

		# ++++ Initial temperature ++++
		w = Label (wFrame, text = 'Initial temperature (K):', anchor = E)
		w.grid (row = 0, column = 2, sticky = NSEW)

		w = self.wInitialTemperature = XFloatEntry (
				wFrame, bg = 'white', width = 1,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 0, column = 3, sticky = NSEW)
		w.enable_color (enable = False)
		w.callback (self.wInitialTemperatureCB)

		# ++++ Final temperature ++++
		w = Label (wFrame, text = 'Final temperature (K):', anchor = E)
		w.grid (row = 1, column = 0, sticky = NSEW)

		w = self.wFinalTemperature = XFloatEntry (
				wFrame, bg = 'white', width = 1,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 1, column = 1, sticky = NSEW)
		w.enable_color (enable = False)
		w.callback (self.wFinalTemperatureCB)

		# ++++ Temperature step ++++
		w = Label (wFrame, text = 'Temperature step (K):', anchor = E)
		w.grid (row = 1, column = 2, sticky = NSEW)

		w = self.wStep = XFloatEntry (
				wFrame, bg = 'white', width = 1,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 1, column = 3, sticky = NSEW)
		w.enable_color (enable = False)
		w.callback (self.wStepCB)

		# ++++ Pre-stabilization delay ++++
		w = Label (wFrame, text = 'Pre-stabilization delay (sec):', anchor = E)
		w.grid (row = 2, column = 0, sticky = NSEW)

		w = self.wPreDelay = XFloatEntry (
				wFrame, bg = 'white', width = 1,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 2, column = 1, sticky = NSEW)
		w.enable_color (enable = False)
		w.callback (self.wPreDelayCB)

		# ++++ Post-stabilization delay ++++
		w = Label (wFrame, text = 'Post-stabilization delay (sec):', anchor = E)
		w.grid (row = 2, column = 2, sticky = NSEW)

		w = self.wPostDelay = XFloatEntry (
				wFrame, bg = 'white', width = 1,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 2, column = 3, sticky = NSEW)
		w.enable_color (enable = False)
		w.callback (self.wPostDelayCB)

		# ++++ Temperature tolerance ++++
		w = Label (wFrame, text = 'Temperature tolerance (K):', anchor = E)
		w.grid (row = 3, column = 0, sticky = NSEW)

		w = self.wTolerance = XFloatEntry (
				wFrame, bg = 'white', width = 1,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 3, column = 1, sticky = NSEW)
		w.enable_color (enable = False)
		w.callback (self.wToleranceCB)

		# ++++ Monitoring period ++++
		w = Label (wFrame, text = 'Monitoring period (sec):', anchor = E)
		w.grid (row = 3, column = 2, sticky = NSEW)

		w = self.wPeriod = XFloatEntry (
				wFrame, bg = 'white', width = 1,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 3, column = 3, sticky = NSEW)
		w.enable_color (enable = False)
		w.callback (self.wPeriodCB, w.WHEN_ALWAYS)

		# ++++ Ramp table ++++
		w = self.wRampTable = Text (wFrame, bg = 'white', borderwidth = 2)
		w.grid (row = 4, column = 0, columnspan = 4, sticky = NSEW)
		w.config (font = tkFont.Font (family = 'Courier', size = 12))
		w.config (width = 61, height = 15)
		w.config (state = DISABLED)

	def wRampIndexCB (self, w, e):

		if (w.get() < len (self.stepTable)):
			self.stepIndex = w.get()
		else:
			self.stepIndex = len (self.stepTable) - 1

		self.setEntryBoxes (self.stepIndex)

	def wInitialTemperatureCB (self, w, e):
		self.stepTable[self.stepIndex].initialTemperature = w.get()
		self.fillRampTable()

	def wFinalTemperatureCB (self, w, e):
		self.stepTable[self.stepIndex].finalTemperature = w.get()
		self.fillRampTable()

	def wStepCB (self, w, e):
		self.stepTable[self.stepIndex].step = w.get()
		self.fillRampTable()

	def wPreDelayCB (self, w, e):
		self.stepTable[self.stepIndex].preDelay = w.get()
		self.fillRampTable()

	def wPostDelayCB (self, w, e):
		self.stepTable[self.stepIndex].postDelay = w.get()
		self.fillRampTable()

	def wToleranceCB (self, w, e):
		self.stepTable[self.stepIndex].tolerance = w.get()
		self.fillRampTable()

	def wPeriodCB (self, w, e):
		self.stepTable[self.stepIndex].period = w.get()
		self.fillRampTable()
		self.selectNextRamp()

	def wNewCB (self):
		for i in range (0, len (self.stepTable)):
			self.stepTable[i] = StepEntry()
		self.setEntryBoxes (0)
		self.fillRampTable()

	def wOpenCB (self):
		self.loadRampTable ('table.txt')
		self.setEntryBoxes (0)
		self.fillRampTable()

	def wSaveCB (self):
		self.saveRampTable ('table.txt')

	def wApplyCB (self):
		self.do_callback (APPLY, self.stepTable)

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def selectNextRamp (self):
		self.stepIndex = self.stepIndex + 1
		if self.stepIndex == len (self.stepTable):
			self.stepIndex = 0
		self.setEntryBoxes (self.stepIndex)
		self.wInitialTemperature.focus()
		self.wInitialTemperature.selection_range (0, END)

	def setEntryBoxes (self, stepIndex):
		entry = self.stepTable[stepIndex]
		self.wRampIndex.set (stepIndex)
		self.wInitialTemperature.set (entry.initialTemperature)
		self.wFinalTemperature.set (entry.finalTemperature)
		self.wStep.set (entry.step)
		self.wPreDelay.set (entry.preDelay)
		self.wPostDelay.set (entry.postDelay)
		self.wTolerance.set (entry.tolerance)
		self.wPeriod.set (entry.period)

	def fillRampTable (self):

		text = ''
		header = (''
			+ ' Ramp    Init   Final    Temp     Pre    Post    Temp   obsrv\n'
			+ 'Index    Temp    Temp    step   delay   delay    stab  period\n'
			+ '-------------------------------------------------------------\n'
			+ '          (K)     (K)     (K)   (sec)   (sec)     (K)   (sec)\n'
			+ '-------------------------------------------------------------')
			  #   0   100.0   450.0     1.0    60.0    60.0    0.10    60.0

		text += header

		for i in range (0, len (self.stepTable)):
			entry = self.stepTable[i]
			text += ('\n'
				+ str ('%5d' % i)
				+ str ('%8.1f' % entry.initialTemperature)
				+ str ('%8.1f' % entry.finalTemperature)
				+ str ('%8.1f' % entry.step)
				+ str ('%8.1f' % entry.preDelay)
				+ str ('%8.1f' % entry.postDelay)
				+ str ('%8.2f' % entry.tolerance)
				+ str ('%8.1f' % entry.period))

		self.wRampTable.config (state = NORMAL)
		self.wRampTable.delete ('1.0', END)
		self.wRampTable.insert ('1.0', text)
		self.wRampTable.config (state = DISABLED)

	def saveRampTable (self, filename):

		fd = open (filename, 'w')

		text = ''
		header = (''
			+ '#  Ramp    Init   Final    Temp     Pre    Post    Temp   obsrv\n'
			+ '# Index    Temp    Temp    step   delay   delay    stab  period\n'
			+ '# -------------------------------------------------------------\n'
			+ '#           (K)     (K)     (K)   (sec)   (sec)     (K)   (sec)\n'
			+ '# -------------------------------------------------------------')
			   #    0   100.0   450.0     1.0    60.0    60.0    0.10    60.0

		text += header

		for i in range (0, len (self.stepTable)):
			entry = self.stepTable[i]
			text += ('\n  '
				+ str ('%5d' % i)
				+ str ('%8.1f' % entry.initialTemperature)
				+ str ('%8.1f' % entry.finalTemperature)
				+ str ('%8.1f' % entry.step)
				+ str ('%8.1f' % entry.preDelay)
				+ str ('%8.1f' % entry.postDelay)
				+ str ('%8.2f' % entry.tolerance)
				+ str ('%8.1f' % entry.period))

		fd.write (text)
		fd.close()

	def loadRampTable (self, filename):

		fd = open (filename, 'r')

		for line in fd:

				line = line.split ('#')[0] if (line.find ('#') != -1) else line
				words = [w for w in line.split()]

				if len (words) < 8:
					continue

				stepIndex = int (words[0])
				if stepIndex >= len (self.stepTable):
					continue

				entry                    = self.stepTable[stepIndex]
				entry.initialTemperature = float (words[1])
				entry.finalTemperature   = float (words[2])
				entry.step               = float (words[3])
				entry.preDelay           = float (words[4])
				entry.postDelay          = float (words[5])
				entry.tolerance          = float (words[6])
				entry.period             = float (words[7])

		fd.close()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_SteppedRampDisplay:

	instances = []

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		self.instances.append (self)
		self.set (
			rampIndex      = 0,
			heaterSetpoint = 0.0,
			state          = STEP_STATE_IDLE)

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Stepped ramp status')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

		self.populateSettings (w)

	def populateSettings (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 115)
		master.grid_columnconfigure (1, weight = 1, minsize = 135)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Ramp index', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wRampIndex = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Heater setpoint', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wHeaterSetpoint = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'State', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wState = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = self.wKey = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

	def set (self, rampIndex, heaterSetpoint, state, *args):
		for o in self.instances:
			o._set (rampIndex, heaterSetpoint, state, *args)

	def _set (self, rampIndex, heaterSetpoint, state, *args):

		rampIndex = str (rampIndex)
		heaterSetpoint = str ('%.1f' % heaterSetpoint) + ' K'

		if state == STEP_STATE_IDLE:
			self.wRampIndex.config (text = '...')
			self.wHeaterSetpoint.config (text = '...')
			self.setIdle()

		elif state == STEP_STATE_PREDELAY:
			self.wRampIndex.config (text = rampIndex)
			self.wHeaterSetpoint.config (text = heaterSetpoint)
			self.setPreDelay (*args)

		elif state == STEP_STATE_CHECK_STABILITY:
			self.wRampIndex.config (text = rampIndex)
			self.wHeaterSetpoint.config (text = heaterSetpoint)
			self.setStability (*args)

		elif state == STEP_STATE_POSTDELAY:
			self.wRampIndex.config (text = rampIndex)
			self.wHeaterSetpoint.config (text = heaterSetpoint)
			self.setPostDelay (*args)

		elif state == STEP_STATE_STABLE:
			self.wRampIndex.config (text = rampIndex)
			self.wHeaterSetpoint.config (text = heaterSetpoint)
			self.setStable()

		elif state == STEP_STATE_FINISHED:
			self.wRampIndex.config (text = '...')
			self.wHeaterSetpoint.config (text = '...')
			self.setFinished()

		else: raise ValueError (state)

	def setIdle (self):
		self.wState.config  (text = 'Idle')
		self.wKey.config (text = '')
		self.wValue.config (text = '')

	def setPreDelay (self, remaining_time):
		self.wState.config  (text = 'Pre delay')
		self.wKey.config (text = 'Remaining time')
		self.wValue.config (text = str ('%.1f' % remaining_time) + ' sec')

	def setStability (self, dT, dt):
		self.wState.config  (text = 'Stabilizing')
		self.wKey.config (text = 'Fluctuation')
		self.wValue.config (
			text = str ('%.2f' % dT) + 'K over ' + str ('%.1f' % dt) + ' sec')

	def setPostDelay (self, remaining_time):
		self.wState.config  (text = 'Post delay')
		self.wKey.config (text = 'Remaining time')
		self.wValue.config (text = str ('%.1f' % remaining_time) + ' sec')

	def setStable (self):
		self.wState.config  (text = 'Stable')
		self.wKey.config (text = '')
		self.wValue.config (text = '')

	def setFinished (self):
		self.wState.config  (text = 'Finished')
		self.wKey.config (text = '')
		self.wValue.config (text = '')

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_PIDSettings:

	def __init__(self, master, P, I, D, IRange):
		self.master = master
		self.master.title ('Temperature control parameters')
		self.createWidgets()
		self.set (P, I, D, IRange)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self):

		### Main Menu
		self.mainmenu = Menu (self.master)
		self.mainmenu.config (borderwidth = 1)
		self.master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)
		self.filemenu.add_command (
			label = 'Apply', command = self.wApplyCB)
		self.filemenu.add_command (
			label = 'Cancel', command = self.wCancelCB)

		self.master.grid_rowconfigure (0, weight = 1)
		self.master.grid_columnconfigure (0, weight = 1)

		# ++++ Temperature settings ++++
		w = wFrame = LabelFrame (
				self.master, text = 'PID parameters')

		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)

		# ++++ Formulae ++++
		row = 0
		text = '• err = T_setpoint - T_actual'
		w = Label (wFrame, text = text, anchor = W)
		w.grid (row = row, column = 0, columnspan = 2, sticky = NSEW)

		row += 1
		text = '• H(%) = 100 x (P x err  +  I x ∫ err * dt  +  D x d/dt(err))'
		w = Label (wFrame, text = text, anchor = W)
		w.grid (row = row, column = 0, columnspan = 2, sticky = NSEW)

		row += 1
		text = '• IRange: abs(err) over which integral remains active'
		w = Label (wFrame, text = text, anchor = W)
		w.grid (row = row, column = 0, columnspan = 2, sticky = NSEW)

		# ++++ P ++++
		row += 1
		w = Label (wFrame, text = 'Proportional (P):', anchor = E)
		w.grid (row = row, column = 0, sticky = NSEW)

		w = self.wP = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = 1, sticky = NSEW)
		w.enable_color (enable = False)

		# ++++ I ++++
		row += 1
		w = Label (wFrame, text = 'Integral (I):', anchor = E)
		w.grid (row = row, column = 0, sticky = NSEW)

		w = self.wI = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = 1, sticky = NSEW)
		w.enable_color (enable = False)

		# ++++ D ++++
		row += 1
		w = Label (wFrame, text = 'Differential (D):', anchor = E)
		w.grid (row = row, column = 0, sticky = NSEW)

		w = self.wD = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = 1, sticky = NSEW)
		w.enable_color (enable = False)

		# ++++ IRange ++++
		row += 1
		w = Label (wFrame, text = 'IRange:', anchor = E)
		w.grid (row = row, column = 0, sticky = NSEW)

		w = self.wIRange = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = 1, sticky = NSEW)
		w.enable_color (enable = False)

	def wApplyCB (self):
		self.do_callback (
			APPLY,
			self.wP.get(), self.wI.get(),
			self.wD.get(), self.wIRange.get())

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, P, I, D, IRange):
		self.wP.set (P)
		self.wI.set (I)
		self.wD.set (D)
		self.wIRange.set (IRange)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_Calibration:

	def __init__(self, master, Pt100_R, TC_mV):
		self.master = master
		self.master.title ('TCON Calibration')
		self.createWidgets (master)

		self.setPt100_R (Pt100_R)
		self.setTC_mV (TC_mV)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self, master):

		### Main Menu
		self.mainmenu = Menu (master)
		self.mainmenu.config (borderwidth = 1)
		master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		file_menuitems = [
			('New',    self.wLoadDefaultCB),
			('Apply',  self.wSaveCB),
			('Cancel', self.wLoadCB)
		]

		for (label, command) in file_menuitems:
			self.filemenu.add_command (label = label, command = command)

		# +++++++++++++++++++++++++++++++++++

		master.grid_columnconfigure (0, weight = 1, minsize = 200)

		row = 0; col = 0
		master.grid_rowconfigure (row, weight = 1)

		w = LabelFrame (master, text = 'Pt100 calibration')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populatePt100Frame (w)

		row += 1
		master.grid_rowconfigure (row, weight = 1)

		w = LabelFrame (master, text = 'Thermo-couple calibration')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populate_TC_Frame (w)

		row += 1
		master.grid_rowconfigure (row, weight = 1)

		w = LabelFrame (master, text = 'Calibrator configuration')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateConfigurationFrame (w)

	def populatePt100Frame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		master.grid_rowconfigure (row, weight = 1)

		w = Button (
			master, text = 'Heater',
			command = self.wHtrPt100CB)

		w.grid (row = row, column = col, sticky = NSEW)

		row += 1
		master.grid_rowconfigure (row, weight = 1)

		w = Button (
			master, text = 'Sample',
			command = self.wCJPt100CB)

		w.grid (row = row, column = col, sticky = NSEW)

	def populate_TC_Frame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		master.grid_rowconfigure (row, weight = 1)

		w = Button (master, text = 'Low', command = self.wTCGain0mVCB)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1
		master.grid_rowconfigure (row, weight = 1)

		w = Button (master, text = 'High', command = self.wTCGain4p99mVCB)
		w.grid (row = row, column = col, sticky = NSEW)

	def populateConfigurationFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_rowconfigure 	(0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)
		master.grid_rowconfigure 	(1, weight = 1)

		row = 0; col = 0
		w = Label (master, text = 'Resistance (Ohm):', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wPt100_R = XFloatEntry (
				master, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)
		w.enable_color (enable = False)

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV):', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wTC_mV = XFloatEntry (
				master, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)
		w.enable_color (enable = False)

	def wSaveCB (self):
		self.do_callback (SAVE_CALIBRATION)

	def wLoadCB (self):
		self.do_callback (LOAD_CALIBRATION)

	def wLoadDefaultCB (self):
		self.do_callback (LOAD_DEFAULT_CALIBRATION)

	def wHtrPt100CB (self):
		self.do_callback (HTR_PT100_CALIBRATION, self.wPt100_R.get())

	def wCJPt100CB (self):
		self.do_callback (CJ_PT100_CALIBRATION, self.wPt100_R.get())

	def wTCGain0mVCB(self):
		self.do_callback (TC_GAIN_CALIB_0)

	def wTCGain4p99mVCB(self):
		self.do_callback (TC_GAIN_CALIB_499, self.wTC_mV.get())

	def setPt100_R (self, R):
		self.wPt100_R.set(R)

	def setTC_mV (self, mV):
		self.wTC_mV.set(mV)

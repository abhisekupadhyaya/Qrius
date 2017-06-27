# coding: utf-8

from tkFont            import Font
from Tkinter           import *
from time              import time as systime, localtime
from tkFileDialog      import askopenfile, asksaveasfile
import os

from XWidget           import XFloatEntry, XIntegerEntry, XScroll, XTab
from XSMU_Constants    import *
from XSMU_Banner       import banner
import Plot2D
import Preferences

class GUI:

	run_modes = {
		RUN_MODE_ITime             : 'I-Time',
		RUN_MODE_VTime             : 'V-Time',
		RUN_MODE_IV                : 'I-V',
		RUN_MODE_IV_TIME_RESOLVED  : 'I-V Time Resolved',
		RUN_MODE_RTime             : 'R-Time'
	}

	methodFileTypes = [
		('XPLORE method files' , '*.xmt'),
		('All files'           , '*.*')
	]

	def __init__ (self, master, sample):
		self.master = master
		self.sample = sample
		self.master.title ('XPLORE Source and Measurement unit')
		self.createWidgets (master)
		self.blank_parameters()
		self.putBanner()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def close (self):
		for w in (self.wAcquisitionSettings,
				  self.wIVRampSettings,
				  self.wOhmmeterSettings):
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

		# ++++ Populating File menu +++++

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (
			label = 'Connect', command = self.wConnectDeviceCB)

		self.filemenu.add_command (
			label = 'Open method', command = self.wOpenMethodCB)

		self.filemenu.add_command (
			label = 'Save method', command = self.wSaveMethodCB)

		self.filemenu.add_command (
			label = 'Hide', command = self.wHideCB)

		# ++++ Populating Settings menu +++++

		self.utilmenu = Menu (self.mainmenu)
		self.utilmenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'Settings', menu = self.utilmenu, underline = 0)

		self.utilmenu.add_command (
			label   = 'I-V measurement settings',
			command = self.wIVRampSettingsCB)
		
		self.utilmenu.add_command (
			label   = 'I-V Time Resolved measurement settings',
			command = self.wIVTimeResolvedRampSettingsCB)

		self.utilmenu.add_command (
			label   = 'Resistance measurement settings',
			command = self.wOhmmeterSettingsCB)

		self.utilmenu.add_command (
			label   = 'Acquisition settings',
			command = self.wAcquisitionSettingsCB)

		self.utilmenu.add_separator()

		self.utilmenu.add_command (
			label   = 'Source parameters',
			command = self.wSourceParametersCB)

		self.utilmenu.add_command (
			label   = 'Meter parameters',
			command = self.wMeterParametersCB)

	def populateDisplayPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# ++++ Run control ++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Run control')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateControlFrame (w)

		# ++++ Source parameters display ++++

		row += 1; col = 0
		w = LabelFrame (master, text = 'Source')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateSourceFrame (w)

		# ++++ Meter parameters display ++++

		row += 1; col = 0
		w = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populateMeterFrame (w)

		# ++++ Acquisition settings display ++++

		row += 1; col = 0
		w = self.wAcquisitionSettings = \
			GUI_AcquisitionSettingsDisplay (master = Frame (master))

		w.master.grid (row = row, column = col, sticky = NSEW)

		# ++++ Run type specific settings display ++++

		row += 1; col = 0
		self.grid_IVRampSettings = (row, col)

		self.wIVRampSettings = \
			GUI_IVRampSettingsDisplay (master = Frame (master))
		
		self.wIVTimeResolvedRampSettings = \
			GUI_IVTimeResolvedRampSettingsDisplay (master = Frame (master))

		self.grid_OhmmeterSettings = (row, col)

		self.wOhmmeterSettings = \
			GUI_OhmmeterSettingsDisplay (master = Frame (master))

	def populateControlFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 110)
		master.grid_columnconfigure (1, weight = 1, minsize = 110)

		row = 0; col = 0
		w = Label (master, text = "Run mode", anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		options = self.run_modes.values()
		var = self.run_mode = StringVar()
		w = self.wRunMode = OptionMenu (
			master, var, *options, command = self.wRunModeCB)
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = self.wStart = \
			Button (master, text = 'Start', command = self.wStartCB)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wFinish = Button (master, text = 'Finish',
			state = DISABLED, command = self.wFinishCB)
		w.grid (row = row, column = col, sticky = NSEW)

	def populateSourceFrame (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 100)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)
		master.grid_columnconfigure (2, weight = 0, minsize = 30)

		row = 0; col = 0
		w = Label (master, text = 'Source mode', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wSourceMode = Label (master, anchor = E)
		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

		row += 1; col = 0
		w = Label (master, text = 'Range', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wSourceRangeValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wSourceRangeUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = Label (master, text = 'Target', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wSourceValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w, mul = 1.0)

		col += 1
		w = self.wSourceUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w, mul = 1.0)

		# ++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Drive', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wVM2Value = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w, mul = 1.0)

		col += 1
		w = self.wVM2Unit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w, mul = 1.0)

	def populateMeterFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Ammeter')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateAmmeterFrame (w)

		row += 1
		w = LabelFrame (master, text = 'Voltmeter')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateVoltmeterFrame (w)

	def populateAmmeterFrame (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 100)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)
		master.grid_columnconfigure (2, weight = 0, minsize =  30)

		# +++++++++++ Range ++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Range', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wCMRangeValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wCMRangeUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++ Value +++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Current', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wCMValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w, mul = 1.0)

		col += 1
		w = self.wCMUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w, mul = 1.0)


	def populateVoltmeterFrame (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 100)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)
		master.grid_columnconfigure (2, weight = 0, minsize =  30)

		# +++++++++++++ Range ++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Range', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wVMRangeValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wVMRangeUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++ Reading +++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wVMValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w, mul = 1.0)

		col += 1
		w = self.wVMUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w, mul = 1.0)

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

		row = 0; col = 0
		w = self.wStatus = Label (master, text = '...', width = 80, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

	def updateParamFont (self, widget, mul = 2, weight = 'bold'):
		font = Font (widget, widget['font'])
		font.config (size = int (round (mul * font['size'])), weight = weight)
		widget.config (font = font)

	def blank_parameters (self):

		widgets = (
			self.wSourceMode,
			self.wSourceRangeValue,
			self.wSourceRangeUnit,
			self.wSourceValue,
			self.wSourceUnit,
			self.wVM2Value,
			self.wVM2Unit,
			self.wCMRangeValue,
			self.wCMRangeUnit,
			self.wCMValue,
			self.wCMUnit,
			self.wVMRangeValue,
			self.wVMRangeUnit,
			self.wVMValue,
			self.wVMUnit
		)

		for w in widgets: w['text'] = '...'

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def getRunMode (self):
		run_modes = {v : k for (k, v) in self.run_modes.items()}
		return run_modes.get (self.run_mode.get())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def wIVRampSettingsCB (self, *args):
		self.do_callback (OPEN_DIALOG, IV_RAMP_SETTINGS_DIALOG)
	
	def wIVTimeResolvedRampSettingsCB (self, *args):
		self.do_callback (OPEN_DIALOG, IV_TIME_RESOLVED_RAMP_SETTINGS_DIALOG)

	def wOhmmeterSettingsCB (self, *args):
		self.do_callback (OPEN_DIALOG, OHMMETER_SETTINGS_DIALOG)

	def wAcquisitionSettingsCB (self, *args):
		self.do_callback (OPEN_DIALOG, ACQUISITION_SETTINGS_DIALOG)

	def wSourceParametersCB (self, *args):
		self.do_callback (OPEN_DIALOG, SOURCE_PARAMETERS_DIALOG)

	def wMeterParametersCB (self, *args):
		self.do_callback (OPEN_DIALOG, METER_SETTINGS_DIALOG)

	def wRunModeCB (self, item):
		self.do_callback (RUN_MODE, self.getRunMode())

	def wStartCB (self):
		self.do_callback (START_RUN, self.getRunMode())

	def wFinishCB (self):
		self.do_callback (FINISH_RUN)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def wConnectDeviceCB (self):
		self.do_callback (CONNECT_DEVICE)

	def wDisconnectDeviceCB (self):
		self.do_callback (DISCONNECT_DEVICE)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wHideCB (self):
		self.master.withdraw()

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

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setConnection (self, connection):

		if connection == DEVICE_CONNECTING :

			self.filemenu.entryconfig (
				0, label = 'Connecting', state = DISABLED, command = None)

		elif connection == DEVICE_CONNECTED :

			self.filemenu.entryconfig (
				0, label = 'Disconnect', state = NORMAL,
				command = self.wDisconnectDeviceCB)

			self.set_status ('Source-meter connected')

		elif connection == DEVICE_DISCONNECTING :

			self.filemenu.entryconfig (
				0, label = 'Disconnecting', state = DISABLED, command = None)

		elif connection == DEVICE_DISCONNECTED :

			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.set_status ('Source-meter disconnected')
			self.blank_parameters()

		elif connection == DEVICE_NOT_FOUND :

			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.set_status ('Source-meter not found')
			self.blank_parameters()

		else: raise ValueError (connection)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, run_mode):

		self.run_mode.set (self.run_modes.get (run_mode))

		for w in (self.wIVRampSettings, self.wIVTimeResolvedRampSettings, self.wOhmmeterSettings):
			w.master.grid_forget()

		options = {

			RUN_MODE_IV                  : (
				self.grid_IVRampSettings, self.wIVRampSettings),
			
			RUN_MODE_IV_TIME_RESOLVED    : (
				self.grid_IVRampSettings, self.wIVRampSettings),

			RUN_MODE_RTime               : (
				self.grid_OhmmeterSettings, self.wOhmmeterSettings)
		}

		if run_mode in options:
			((row, col), w) = options.get (run_mode)
			w.master.grid (row = row, column = col, sticky = NSEW)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setRunControlStatus (self, status):

		if status == RUN_STARTING:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config   (text = 'Starting', state = DISABLED)
			self.wFinish.config  (text = 'Finish',   state = DISABLED)

		elif status == RUN_STARTED:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config   (text = 'Start',  state = DISABLED)
			self.wFinish.config  (text = 'Finish', state = NORMAL)

		elif status == RUN_FINISHING:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config   (text = 'Start',     state = DISABLED)
			self.wFinish.config  (text = 'Finishing', state = DISABLED)

		elif status == RUN_FINISHED:
			self.wRunMode.config (state = NORMAL)
			self.wStart.config   (text = 'Start',  state = NORMAL)
			self.wFinish.config  (text = 'Finish', state = DISABLED)

		else: raise ValueError (status)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setSourceParameters (self, mode, autorange, range, value):

		modes = {

			SOURCE_MODE_CS : 'Constant current',
			SOURCE_MODE_VS : 'Constant voltage'
		}

		self.wSourceMode['text'] = modes.get (mode)

		# +++++++++++++++++++++++++++++++++++++++++++++++++

		ranges = {

			SOURCE_MODE_CS : {

				CM_RANGE_10uA  : ('±10',  'μA'),
				CM_RANGE_100uA : ('±100', 'μA'),
				CM_RANGE_1mA   : ('±1',   'mA'),
				CM_RANGE_10mA  : ('±10',  'mA'),
				CM_RANGE_100mA : ('±100', 'mA')
			},

			SOURCE_MODE_VS : {

				VS_RANGE_10V  : ('±10',  'V'),
				VS_RANGE_100V : ('±100', 'V')
			}
		}

		(fullscale, unit) = ranges[mode][range]
		self.wSourceRangeValue['text'] = fullscale
		self.wSourceRangeUnit ['text'] = unit

		# +++++++++++++++++++++++++++++++++++++++++++++++++

		src_fmts = {

			SOURCE_MODE_CS : {

				CM_RANGE_10uA  : ('%+07.3f', 1e6, 'μA'),
				CM_RANGE_100uA : ('%+07.2f', 1e6, 'μA'),
				CM_RANGE_1mA   : ('%+07.4f', 1e3, 'mA'),
				CM_RANGE_10mA  : ('%+07.3f', 1e3, 'mA'),
				CM_RANGE_100mA : ('%+07.2f', 1e3, 'mA')
			},

			SOURCE_MODE_VS : {

				VS_RANGE_10V  : ('%+08.4f', 1.0, 'V'),
				VS_RANGE_100V : ('%+08.3f', 1.0, 'V')
			}
		}

		(fmt, mult, unit) = src_fmts[mode][range]
		self.wSourceValue ['text'] = str (fmt % (value * mult))
		self.wSourceUnit  ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setRange (self, cm_autorange, cm_range):

		cm_ranges = {
			CM_RANGE_100uA : ('±10',  'μA'),
			CM_RANGE_100uA : ('±100', 'μA'),
			CM_RANGE_1mA   : ('±1',   'mA'),
			CM_RANGE_10mA  : ('±10',  'mA'),
			CM_RANGE_100mA : ('±100', 'mA')
		}

		(fullscale, unit) = cm_ranges.get (cm_range)
		self.wCMRangeValue ['text'] = fullscale
		self.wCMRangeUnit  ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM_setRange (self, vm_autorange, vm_range):

		vm_ranges = {
			VM_RANGE_1mV   : ('±1',   'mV'),
			VM_RANGE_10mV  : ('±10',  'mV'),
			VM_RANGE_100mV : ('±100', 'mV'),
			VM_RANGE_1V    : ('±1',    'V'),
			VM_RANGE_10V   : ('±10',   'V'),
			VM_RANGE_100V  : ('±100',  'V')
		}

		(fullscale, unit) = vm_ranges.get (vm_range)
		self.wVMRangeValue ['text'] = fullscale
		self.wVMRangeUnit  ['text'] = unit

	def VM2_setRange (self, vm2_autorange, vm2_range): pass

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setReading (self, range, reading):

		fmts = {
			CM_RANGE_10uA  : ('%+09.5f', 1e6, 'μA'),
			CM_RANGE_100uA : ('%+09.4f', 1e6, 'μA'),
			CM_RANGE_1mA   : ('%+09.6f', 1e3, 'mA'),
			CM_RANGE_10mA  : ('%+09.5f', 1e3, 'mA'),
			CM_RANGE_100mA : ('%+09.4f', 1e3, 'mA')
		}

		(fmt, mult, unit) = fmts.get (range, ('%e', 1.0, 'A'))
		self.wCMValue['text'] = str (fmt % (reading * mult))
		self.wCMUnit ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM_setReading (self, range, reading):

		fmts = {
			VM_RANGE_1mV   : ('%+09.6f', 1e3, 'mV'),
			VM_RANGE_10mV  : ('%+09.5f', 1e3, 'mV'),
			VM_RANGE_100mV : ('%+09.4f', 1e3, 'mV'),
			VM_RANGE_1V    : ('%+09.6f', 1.0,  'V'),
			VM_RANGE_10V   : ('%+09.5f', 1.0,  'V'),
			VM_RANGE_100V  : ('%+09.5f', 1.0,  'V')
		}

		(fmt, mult, unit) = fmts.get (range, ('%e', 1.0, 'V'))
		self.wVMValue['text'] = str (fmt % (reading * mult))
		self.wVMUnit ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM2_setReading (self, range, reading):

		fmts = { VM2_RANGE_10V : ('%+09.5f', 1.0,  'V') }

		(fmt, mult, unit) = fmts.get (range, ('%e', 1.0, 'V'))
		self.wVM2Value['text'] = str (fmt % (reading * mult))
		self.wVM2Unit ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def set_status (self, text):

		lt = localtime (systime())
		time_stamp = (
			str ('%02d' % lt.tm_hour) + ':' +
			str ('%02d' % lt.tm_min)  + ':' +
			str ('%02d' % lt.tm_sec))

		text = '<' + time_stamp + ':XSMU> ' + text
		print text

		old_text = self.wStatus['text']
		new_text = text + '    .    ' + old_text
		new_text = new_text[:1024]
		self.wStatus['text'] = new_text

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setAcquisitionSettings (self, delay, filterLength):
		self.wAcquisitionSettings.set (delay, filterLength)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setIVRampSettings (
		self, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.wIVRampSettings.set (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)
	
	def setIVTimeResolvedRampSettings (
		self, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.wIVTimeResolvedRampSettings.set (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

	def setOhmmeterSettings (
		self, maxCurrent, maxVoltage,
		maxPower, bipolar, resTrackMode):

		self.wOhmmeterSettings.set (
			maxCurrent, maxVoltage, maxPower, bipolar, resTrackMode)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def putBanner (self):
		w = GUI_Banner (self.wPlots.add ('Welcome'))
		w.grid (row = 0, column = 0, sticky = NSEW)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_SourceParameters:

	modes = {
		SOURCE_MODE_CS : 'Constant current',
		SOURCE_MODE_VS : 'Constant voltage'
	}

	autoranges = {
		True  : 'Yes',
		False : 'No'
	}

	cm_ranges = {
		CM_RANGE_10uA  : u'±10μA',
		CM_RANGE_100uA : u'±100μA',
		CM_RANGE_1mA   : u'±1mA',
		CM_RANGE_10mA  : u'±10mA',
		CM_RANGE_100mA : u'±100mA'
	}

	vs_ranges = {
		VS_RANGE_10V  : u'±10V',
		VS_RANGE_100V : u'±100V'
	}

	def __init__ (self, master, mode, autorange,
			   cm_range, cs_value, vs_range, vs_value):

		self.master = master
		self.master.title ('Source parameters')
		self.createWidgets (master)

		self.setMode (mode)
		self.setAutoRange (autorange)
		self.CS_setRange (cm_range, cs_value)
		self.VS_setRange (vs_range, vs_value)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self, master):

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

		# +++++++++++++++++++++++++++++++

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Source mode')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateSourceModeFrame (w)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		self.sourceFrameGrid = (row, col)

		# +++++++++++++++++++++++++++++++

		w = self.wCurrentSourceFrame = \
			LabelFrame (master, text = 'Current source parameters')

		self.populateCurrentSourceFrame (w)

		# +++++++++++++++++++++++++++++++

		w = self.wVoltageSourceFrame = \
			LabelFrame (master, text = 'Voltage source parameters')

		self.populateVoltageSourceFrame (w)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateSourceModeFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [10, 15]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Mode')
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.modes.values()
		var = self.mode = StringVar()

		w = self.wSourceMode = \
			OptionMenu (master, var, *options, command = self.wSourceModeCB)

		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Auto range')
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.autoranges.values()
		var = self.autorange = StringVar()

		w = self.wSourceAutoRange = \
			OptionMenu (master, var, *options,
			   command = self.wSourceAutoRangeCB)

		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateCurrentSourceFrame (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [10, 15]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Range',
			 anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		var = self.cm_range = StringVar()
		options = self.cm_ranges.values()
		w = self.wCurrentSourceRange = OptionMenu (master, var, *options)

		menu = w['menu']
		menu.entryconfig (0, state = DISABLED) # ±10μA
		menu.entryconfig (4, state = DISABLED) # ±100mA

		w.config (anchor = W, width = col_widths[col])
		w.config (state = DISABLED if self.autorange else NORMAL)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Value (μA)',
			 anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.cs_value = XFloatEntry (master, width = col_widths[col])
		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateVoltageSourceFrame (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [10, 15]

		row = 0; col = 0
		w = Label (master, text = 'Range', anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.vs_ranges.values()
		var = self.vs_range = StringVar()
		w = self.wVoltageSourceRange = OptionMenu (master, var, *options)

		menu = w['menu']
		menu.entryconfig (1, state = DISABLED) # ±100V

		w.config (anchor = W, width = col_widths[col])
		w.config (state = DISABLED if self.autorange else NORMAL)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Value (mV)',
			 anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.vs_value = XFloatEntry (master, width = col_widths[col])
		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wSourceModeCB (self, mode):
		self.setMode (self.getMode())

	def wSourceAutoRangeCB (self, autorange):
		self.setAutoRange (self.getAutoRange())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMode (self):
		modes = {v : k for (k, v) in self.modes.items()}
		return modes.get (self.mode.get())

	def getAutoRange (self):
		autoranges = {v : k for (k, v) in self.autoranges.items()}
		return autoranges.get (self.autorange.get())

	def CM_getRange (self):
		cm_ranges = {v : k for (k, v) in self.cm_ranges.items()}
		return cm_ranges.get (self.cm_range.get())

	def VS_getRange (self):
		vs_ranges = {v : k for (k, v) in self.vs_ranges.items()}
		return vs_ranges.get (self.vs_range.get())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wApplyCB (self):

		mode      = self.getMode()
		autorange = self.getAutoRange()

		(range, value) = {

			SOURCE_MODE_CS : (

				self.CM_getRange(),
				self.cs_value.get() * uA_to_A
			),

			SOURCE_MODE_VS : (

				self.VS_getRange(),
				self.vs_value.get() * mV_to_V
			)

		}.get (mode)

		self.do_callback (APPLY, mode, autorange, range, value)

	def wCancelCB (self):
		self.do_callback (CANCEL)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setMode (self, mode):

		self.mode.set (self.modes.get (mode))

		for frame in (self.wCurrentSourceFrame, self.wVoltageSourceFrame):
			frame.grid_forget()

		(row, col) = self.sourceFrameGrid

		frames = {
			SOURCE_MODE_CS : self.wCurrentSourceFrame,
			SOURCE_MODE_VS : self.wVoltageSourceFrame
		}

		w = frames.get (mode)
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

	def setAutoRange (self, autorange):

		self.autorange.set (self.autoranges.get (autorange))

		state_options = {True : DISABLED, False : NORMAL}
		for w in (self.wVoltageSourceRange, self.wCurrentSourceRange):
			w.config (state = state_options.get (autorange))

	def CS_setRange (self, cm_range, cs_value):
		self.cm_range.set (self.cm_ranges.get (cm_range))
		self.cs_value.set (cs_value * A_to_uA)

	def VS_setRange (self, vs_range, vs_value):
		self.vs_range.set (self.vs_ranges.get (vs_range))
		self.vs_value.set (vs_value * V_to_mV)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_MeterParameters:

	autoranges = {
		True  : 'Yes',
		False : 'No'
	}

	cm_ranges = {
		CM_RANGE_10uA  : u'±10μA',
		CM_RANGE_100uA : u'±100μA',
		CM_RANGE_1mA   : u'±1mA',
		CM_RANGE_10mA  : u'±10mA',
		CM_RANGE_100mA : u'±100mA'
	}

	vm_ranges = {
		VM_RANGE_1mV   : u'±1mV',
		VM_RANGE_10mV  : u'±10mV',
		VM_RANGE_100mV : u'±100mV',
		VM_RANGE_1V    : u'±1V',
		VM_RANGE_10V   : u'±10V',
		VM_RANGE_100V  : u'±100V'
	}

	def __init__ (
		self, master, src_mode,
		cm_autorange, cm_range, vm_autorange, vm_range):

		self.master = master
		self.master.title ('Meter parameters')
		self.createWidgets (master)

		self.src_mode = src_mode
		self.CM_setRange (cm_autorange, cm_range)
		self.VM_setRange (vm_autorange, vm_range)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self, master):

		self.mainmenu = Menu (self.master)
		self.mainmenu.config (borderwidth = 1)
		self.master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (label = 'Done', command = self.wApplyCB)
		self.filemenu.add_command (label = 'Cancel', command = self.wCancelCB)

		# +++++++++++++++++++++++++++++++

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)
		col_widths = [15, 10]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'CM Auto range')
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.autoranges.values()
		var = self.cm_autorange = StringVar()

		w = self.wAmmeterAutoRange = OptionMenu (
			master, var, *options, command = self.wAmmeterCB)

		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'CM Range')
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.cm_ranges.values()
		var = self.cm_range = StringVar()
		w = self.wAmmeterRange = OptionMenu (
			master, var, *options, command = self.wAmmeterCB)

		menu = w['menu']
		for index in [CM_RANGE_10uA, CM_RANGE_100mA]:
			menu.entryconfig (index, state = DISABLED)

		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'VM Auto range',
					anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.autoranges.values()
		var = self.vm_autorange = StringVar()
		w = self.wVoltmeterAutoRange = OptionMenu (
			master, var, *options, command = self.wVoltmeterCB)

		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'VM Range',
					anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.vm_ranges.values()
		var = self.vm_range = StringVar()

		w = self.wVoltmeterRange = OptionMenu (
			master, var, *options, command = self.wVoltmeterCB)

		menu = w['menu']
		for index in (VM_RANGE_1mV, VM_RANGE_10mV, VM_RANGE_100V):
			menu.entryconfig (index, state = DISABLED)

		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getVoltmeterRange (self):
		vm_ranges = {v : k for (k, v) in self.vm_ranges.items()}
		return vm_ranges.get (self.vm_range.get())

	def getVoltmeterAutoRange (self):
		autoranges = {v : k for (k, v) in self.autoranges.items()}
		return autoranges.get (self.vm_autorange.get())

	def getAmmeterRange (self):
		cm_ranges = {v : k for (k, v) in self.cm_ranges.items()}
		return cm_ranges.get (self.cm_range.get())

	def getAmmeterAutoRange (self):
		autoranges = {v : k for (k, v) in self.autoranges.items()}
		return autoranges.get (self.cm_autorange.get())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wAmmeterCB (self, *args):

		self.CM_setRange (
			self.getAmmeterAutoRange(),
			self.getAmmeterRange())

		self.do_callback (
			CM_RANGE_CHANGED,
			self.getAmmeterAutoRange(),
			self.getAmmeterRange())

	def wVoltmeterCB (self, *args):

		self.VM_setRange (
			self.getVoltmeterAutoRange(),
			self.getVoltmeterRange())

		self.do_callback (VM_RANGE_CHANGED,
			self.getVoltmeterAutoRange(),
			self.getVoltmeterRange())

	def wApplyCB (self):
		self.do_callback (APPLY)

	def wCancelCB (self):
		self.do_callback (CANCEL)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setRange (self, cm_autorange, cm_range):
		self.setAmmeterAutoRange (cm_autorange)
		self.setAmmeterRange (cm_autorange, cm_range)

	def setAmmeterAutoRange (self, cm_autorange):

		self.cm_autorange.set (self.autoranges.get (cm_autorange))

		state_options = {
			SOURCE_MODE_CS : DISABLED,
			SOURCE_MODE_VS : NORMAL
		}

		self.wAmmeterAutoRange.config (
			state = state_options.get (self.src_mode))

	def setAmmeterRange (self, cm_autorange, cm_range):

		if   self.src_mode == SOURCE_MODE_CS : state = DISABLED
		elif self.src_mode == SOURCE_MODE_VS :
			if   cm_autorange == True  : state = DISABLED
			elif cm_autorange == False : state = NORMAL

		self.wAmmeterRange.config (state = state)
		self.cm_range.set (self.cm_ranges.get (cm_range))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM_setRange (self, vm_autorange, vm_range):
		self.setVoltmeterAutoRange (vm_autorange)
		self.setVoltmeterRange (vm_autorange, vm_range)

	def setVoltmeterAutoRange (self, vm_autorange):
		self.vm_autorange.set (self.autoranges.get (vm_autorange))

	def setVoltmeterRange (self, vm_autorange, vm_range):

		self.wVoltmeterRange.config (
			state = {True : DISABLED, False : NORMAL}.get (vm_autorange))

		self.vm_range.set (self.vm_ranges.get (vm_range))

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_AcquisitionSettings:

	def __init__(self, master, delay, filterLength):

		self.master = master
		master.title ('Acquisition settings')
		self.createWidgets (master)
		self.set (delay, filterLength)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self, master):

		self.mainmenu = Menu (master)
		self.mainmenu.config (borderwidth = 1)
		master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (label = 'Done', command = self.wApplyCB)
		self.filemenu.add_command (label = 'Cancel', command = self.wCancelCB)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		master.grid_columnconfigure (0, weight = 1)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Aquisition Settings')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateAcquisitionSettings (w)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateAcquisitionSettings (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 15]

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row = 0; col = 0

		w = Label (master, text = 'Delay (sec)',
			 width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wDelay = XFloatEntry (master, width = col_widths[col])

		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Filter length',
				width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wFilterLength = \
			XIntegerEntry (master, width = col_widths[col])

		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

	def set (self, delay, filterLength):
		self.wDelay.set (delay)
		self.wFilterLength.set (filterLength)

	def wApplyCB (self):
		self.do_callback (APPLY, self.wDelay.get(), self.wFilterLength.get())

	def wCancelCB (self):
		self.do_callback (CANCEL)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_AcquisitionSettingsDisplay:

	instances = []

	def __init__(self, master):

		self.master = master
		self.createWidgets (master)
		self.synchronize()

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		master.grid_columnconfigure (0, weight = 1)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Aquisition Settings')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateAcquisitionSettings (w)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateAcquisitionSettings (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 15]

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Delay (sec)',
			 width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wDelay = \
			Label (master, width = col_widths[col], anchor = E)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Filter Length',
				width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wFilterLength = \
			Label (master, width = col_widths[col], anchor = E)

		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]
			self.wDelay        ['text'] = first.wDelay        ['text']
			self.wFilterLength ['text'] = first.wFilterLength ['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _set (self, delay, filterLength):
		self.wDelay        ['text'] = str (delay)
		self.wFilterLength ['text'] = str (filterLength)

	def set (self, delay, filterLength):
		for instance in self.instances:
			instance._set (delay, filterLength)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):
		self.wDelay        ['text'] = '...'
		self.wFilterLength ['text'] = '...'

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_IVRampSettings:

	bipolarMenuItems = {
		True  : 'Yes',
		False : 'No'
	}

	resTrackMenuItems = {
		R_TRACK_V_I   : u'V/I',
		R_TRACK_dV_dI : u'ΔV/ΔI'
	}

	def __init__ (
		self, master, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.master = master
		self.master.title ('I-V ramp settings')
		self.createWidgets (master)
		self.set (finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self, master):

		self.mainmenu = Menu (self.master)
		self.mainmenu.config (borderwidth = 1)
		self.master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (label = 'Done', command = self.wApplyCB)
		self.filemenu.add_command (label = 'Cancel', command = self.wCancelCB)

		# +++++++++++++++++++++++++++++++

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Limits')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateLimits (w)

		# +++++++++++++++++++++++++++++++

		row += 1
		w = LabelFrame (master, text = 'Step size')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateStepSize (w)

		# +++++++++++++++++++++++++++++++

		row += 1
		w = LabelFrame (master, text = 'Options')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateOptions (w)

		# +++++++++++++++++++++++++++++++

	def populateLimits (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 10]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalCurrent = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalVoltage = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Power (mW)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxPower = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Whichever happens first',
					width = col_widths[col], anchor = E)

		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

	def populateStepSize (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 10]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wCurrentStep = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wVoltageStep = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def populateOptions (self, master):
		master.grid_columnconfigure (0, weight = 1, minsize = 20)
		master.grid_columnconfigure (1, weight = 1, minsize = 10)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Bipolar', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		var = self.bipolar = StringVar()
		options = self.bipolarMenuItems.values()
		w = self.wBipolarOptions = OptionMenu (master, var, *options)
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		#row += 1; col = 0
		w = Label (master, text = 'Tracking mode', anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		#col += 1
		options = self.resTrackMenuItems.values()
		var = self.resTrackMode = StringVar()
		w = self.wResTrackOptions = OptionMenu (master, var, *options)
		w.config (anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def wApplyCB (self):

		bipolarModes  = {v : k for (k, v) in self.bipolarMenuItems.items()}
		resTrackModes = {v : k for (k, v) in self.resTrackMenuItems.items()}

		self.do_callback (APPLY,
			uA_to_A * self.wFinalCurrent.get(),
			mV_to_V * self.wFinalVoltage.get(),
			mW_to_W * self.wMaxPower.get(),
			uA_to_A * self.wCurrentStep.get(),
			mV_to_V * self.wVoltageStep.get(),
			bipolarModes.get (self.bipolar.get()),
			resTrackModes.get (self.resTrackMode.get()))

	def wCancelCB (self):
		self.do_callback (CANCEL)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def set (self, finalCurrent, finalVoltage, maxPower,
		  currentStep, voltageStep, bipolar, resTrackMode):

		self.wFinalCurrent.set (A_to_uA * finalCurrent)
		self.wFinalVoltage.set (V_to_mV * finalVoltage)
		self.wMaxPower.set     (W_to_mW * maxPower)
		self.wCurrentStep.set  (A_to_uA * currentStep)
		self.wVoltageStep.set  (V_to_mV * voltageStep)
		self.bipolar.set       (self.bipolarMenuItems.get (bipolar))
		self.resTrackMode.set  (self.resTrackMenuItems.get (resTrackMode))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_IVRampSettingsDisplay:

	bipolarMenuItems = {
		True  : 'Yes',
		False : 'No'
	}

	resTrackMenuItems = {
		R_TRACK_V_I   : u'V/I',
		R_TRACK_dV_dI : u'ΔV/ΔI'
	}

	instances = []

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		self.synchronize()

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Limits')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateLimits (w)

		# +++++++++++++++++++++++++++++++

		row += 1
		w = LabelFrame (master, text = 'Step size')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateStepSize (w)

		# +++++++++++++++++++++++++++++++

		row += 1
		w = LabelFrame (master, text = 'Options')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateOptions (w)

		# +++++++++++++++++++++++++++++++

	def populateLimits (self, master):
		master.grid_columnconfigure (0, weight = 1, minsize = 20)
		master.grid_columnconfigure (1, weight = 1, minsize = 10)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalCurrent = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalVoltage = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Power (mW)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxPower = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Whichever happens first', anchor = E)
		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

	def populateStepSize (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 10]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wCurrentStep = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wVoltageStep = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def populateOptions (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 200)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Bipolar', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wBipolar = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		# row += 1; col = 0
		w = Label (master, text = 'R track mode', anchor = W)
		# w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		# col += 1
		w = self.wResTrackMode = Label (master, anchor = E)
		# w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]
			self.wFinalCurrent ['text'] = first.wFinalCurrent ['text']
			self.wFinalVoltage ['text'] = first.wFinalVoltage ['text']
			self.wMaxPower     ['text'] = first.wMaxPower     ['text']
			self.wCurrentStep  ['text'] = first.wCurrentStep  ['text']
			self.wVoltageStep  ['text'] = first.wVoltageStep  ['text']
			self.wBipolar      ['text'] = first.wBipolar      ['text']
			self.wResTrackMode ['text'] = first.wResTrackMode ['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _set (self, finalCurrent, finalVoltage, maxPower,
		  currentStep, voltageStep, bipolar, resTrackMode):

		self.wFinalCurrent ['text'] = str (A_to_uA * finalCurrent)
		self.wFinalVoltage ['text'] = str (V_to_mV * finalVoltage)
		self.wMaxPower     ['text'] = str (W_to_mW * maxPower)
		self.wCurrentStep  ['text'] = str (A_to_uA * currentStep)
		self.wVoltageStep  ['text'] = str (V_to_mV * voltageStep)
		self.wBipolar      ['text'] = self.bipolarMenuItems.get (bipolar)
		self.wResTrackMode ['text'] = self.resTrackMenuItems.get (resTrackMode)

	def set (self, finalCurrent, finalVoltage, maxPower,
		  currentStep, voltageStep, bipolar, resTrackMode):

		for instance in self.instances:
			instance._set (finalCurrent, finalVoltage, maxPower,
				  currentStep, voltageStep, bipolar, resTrackMode)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):
		self.wFinalCurrent ['text'] = '...'
		self.wFinalVoltage ['text'] = '...'
		self.wMaxPower     ['text'] = '...'
		self.wCurrentStep  ['text'] = '...'
		self.wVoltageStep  ['text'] = '...'
		self.wBipolar      ['text'] = '...'
		self.wResTrackMode ['text'] = '...'

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_IVTimeResolvedRampSettings:

	bipolarMenuItems = {
		True  : 'Yes',
		False : 'No'
	}

	resTrackMenuItems = {
		R_TRACK_V_I   : u'V/I',
		R_TRACK_dV_dI : u'ΔV/ΔI'
	}

	def __init__ (
		self, master, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.master = master
		self.master.title ('I-V Time Resolved ramp settings')
		self.createWidgets (master)
		self.set (finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self, master):

		self.mainmenu = Menu (self.master)
		self.mainmenu.config (borderwidth = 1)
		self.master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (label = 'Done', command = self.wApplyCB)
		self.filemenu.add_command (label = 'Cancel', command = self.wCancelCB)

		# +++++++++++++++++++++++++++++++

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Limits')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateLimits (w)

		# +++++++++++++++++++++++++++++++

		row += 1
		w = LabelFrame (master, text = 'Step size')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateStepSize (w)

		# +++++++++++++++++++++++++++++++

		row += 1
		w = LabelFrame (master, text = 'Options')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateOptions (w)

		# +++++++++++++++++++++++++++++++

	def populateLimits (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 10]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalCurrent = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalVoltage = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Power (mW)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxPower = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Whichever happens first',
					width = col_widths[col], anchor = E)

		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

	def populateStepSize (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 10]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wCurrentStep = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wVoltageStep = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def populateOptions (self, master):
		master.grid_columnconfigure (0, weight = 1, minsize = 20)
		master.grid_columnconfigure (1, weight = 1, minsize = 10)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Bipolar', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		var = self.bipolar = StringVar()
		options = self.bipolarMenuItems.values()
		w = self.wBipolarOptions = OptionMenu (master, var, *options)
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		#row += 1; col = 0
		w = Label (master, text = 'Tracking mode', anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		#col += 1
		options = self.resTrackMenuItems.values()
		var = self.resTrackMode = StringVar()
		w = self.wResTrackOptions = OptionMenu (master, var, *options)
		w.config (anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def wApplyCB (self):

		bipolarModes  = {v : k for (k, v) in self.bipolarMenuItems.items()}
		resTrackModes = {v : k for (k, v) in self.resTrackMenuItems.items()}

		self.do_callback (APPLY,
			uA_to_A * self.wFinalCurrent.get(),
			mV_to_V * self.wFinalVoltage.get(),
			mW_to_W * self.wMaxPower.get(),
			uA_to_A * self.wCurrentStep.get(),
			mV_to_V * self.wVoltageStep.get(),
			bipolarModes.get (self.bipolar.get()),
			resTrackModes.get (self.resTrackMode.get()))

	def wCancelCB (self):
		self.do_callback (CANCEL)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def set (self, finalCurrent, finalVoltage, maxPower,
		  currentStep, voltageStep, bipolar, resTrackMode):

		self.wFinalCurrent.set (A_to_uA * finalCurrent)
		self.wFinalVoltage.set (V_to_mV * finalVoltage)
		self.wMaxPower.set     (W_to_mW * maxPower)
		self.wCurrentStep.set  (A_to_uA * currentStep)
		self.wVoltageStep.set  (V_to_mV * voltageStep)
		self.bipolar.set       (self.bipolarMenuItems.get (bipolar))
		self.resTrackMode.set  (self.resTrackMenuItems.get (resTrackMode))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_IVTimeResolvedRampSettingsDisplay:

	bipolarMenuItems = {
		True  : 'Yes',
		False : 'No'
	}

	resTrackMenuItems = {
		R_TRACK_V_I   : u'V/I',
		R_TRACK_dV_dI : u'ΔV/ΔI'
	}

	instances = []

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		self.synchronize()

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Limits')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateLimits (w)

		# +++++++++++++++++++++++++++++++

		row += 1
		w = LabelFrame (master, text = 'Step size')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateStepSize (w)

		# +++++++++++++++++++++++++++++++

		row += 1
		w = LabelFrame (master, text = 'Options')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateOptions (w)

		# +++++++++++++++++++++++++++++++

	def populateLimits (self, master):
		master.grid_columnconfigure (0, weight = 1, minsize = 20)
		master.grid_columnconfigure (1, weight = 1, minsize = 10)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalCurrent = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalVoltage = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Power (mW)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxPower = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Whichever happens first', anchor = E)
		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

	def populateStepSize (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 10]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wCurrentStep = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wVoltageStep = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def populateOptions (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 200)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Bipolar', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wBipolar = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		# row += 1; col = 0
		w = Label (master, text = 'R track mode', anchor = W)
		# w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		# col += 1
		w = self.wResTrackMode = Label (master, anchor = E)
		# w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]
			self.wFinalCurrent ['text'] = first.wFinalCurrent ['text']
			self.wFinalVoltage ['text'] = first.wFinalVoltage ['text']
			self.wMaxPower     ['text'] = first.wMaxPower     ['text']
			self.wCurrentStep  ['text'] = first.wCurrentStep  ['text']
			self.wVoltageStep  ['text'] = first.wVoltageStep  ['text']
			self.wBipolar      ['text'] = first.wBipolar      ['text']
			self.wResTrackMode ['text'] = first.wResTrackMode ['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _set (self, finalCurrent, finalVoltage, maxPower,
		  currentStep, voltageStep, bipolar, resTrackMode):

		self.wFinalCurrent ['text'] = str (A_to_uA * finalCurrent)
		self.wFinalVoltage ['text'] = str (V_to_mV * finalVoltage)
		self.wMaxPower     ['text'] = str (W_to_mW * maxPower)
		self.wCurrentStep  ['text'] = str (A_to_uA * currentStep)
		self.wVoltageStep  ['text'] = str (V_to_mV * voltageStep)
		self.wBipolar      ['text'] = self.bipolarMenuItems.get (bipolar)
		self.wResTrackMode ['text'] = self.resTrackMenuItems.get (resTrackMode)

	def set (self, finalCurrent, finalVoltage, maxPower,
		  currentStep, voltageStep, bipolar, resTrackMode):

		for instance in self.instances:
			instance._set (finalCurrent, finalVoltage, maxPower,
				  currentStep, voltageStep, bipolar, resTrackMode)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):
		self.wFinalCurrent ['text'] = '...'
		self.wFinalVoltage ['text'] = '...'
		self.wMaxPower     ['text'] = '...'
		self.wCurrentStep  ['text'] = '...'
		self.wVoltageStep  ['text'] = '...'
		self.wBipolar      ['text'] = '...'
		self.wResTrackMode ['text'] = '...'

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_OhmmeterSettings:

	bipolarMenuItems = {
		True  : 'Yes',
		False : 'No'
	}

	resTrackMenuItems = {
		R_TRACK_V_I   : u'V/I',
		R_TRACK_dV_dI : u'ΔV/ΔI'
	}

	def __init__ (
		self, master, maxCurrent, maxVoltage,
		maxPower, bipolar, resTrackMode):

		self.master = master
		self.master.title ('Resistance measurement settings')
		self.createWidgets (master)
		self.set (maxCurrent, maxVoltage, maxPower, bipolar, resTrackMode)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self, master):

		self.mainmenu = Menu (self.master)
		self.mainmenu.config (borderwidth = 1)
		self.master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (label = 'Done', command = self.wApplyCB)
		self.filemenu.add_command (label = 'Cancel', command = self.wCancelCB)

		# +++++++++++++++++++++++++++++++

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Limits')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateLimits (w)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = LabelFrame (master, text = 'Options')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateOptions (w)

		# +++++++++++++++++++++++++++++++

	def populateLimits (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 10]

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxCurrent = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxVoltage = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Power (mW)',
					width = col_widths[col], anchor = W)

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxPower = \
				XFloatEntry (master, width = col_widths[col])

		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Whichever happens first',
					width = col_widths[col], anchor = E)

		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

	def populateOptions (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 200)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Bipolar', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		var = self.bipolar = StringVar()
		options = self.bipolarMenuItems.values()
		w = self.wBipolarOptions = OptionMenu (master, var, *options)
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		#row += 1; col = 0
		w = Label (master, text = 'R track mode', anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		#col += 1
		var = self.resTrackMode = StringVar()
		options = self.resTrackMenuItems.values()
		w = self.wResTrackOptions = OptionMenu (master, var, *options)
		w.config (anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def wApplyCB (self):

		bipolarModes  = {v : k for (k, v) in self.bipolarMenuItems.items()}
		resTrackModes = {v : k for (k, v) in self.resTrackMenuItems.items()}

		self.do_callback (
			APPLY,
			uA_to_A * self.wMaxCurrent.get(),
			mV_to_V * self.wMaxVoltage.get(),
			mW_to_W * self.wMaxPower.get(),
			bipolarModes.get (self.bipolar.get()),
			resTrackModes.get (self.resTrackMode.get()))

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, maxCurrent, maxVoltage, maxPower, bipolar, resTrackMode):
		self.wMaxCurrent.set  (A_to_uA * maxCurrent)
		self.wMaxVoltage.set  (V_to_mV * maxVoltage)
		self.wMaxPower.set    (W_to_mW * maxPower)
		self.bipolar.set      (self.bipolarMenuItems.get (bipolar))
		self.resTrackMode.set (self.resTrackMenuItems.get (resTrackMode))

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_OhmmeterSettingsDisplay:

	instances = []

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		self.synchronize()

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		# +++++++++++++++++++++++++++++++

		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Limits')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateLimits (w)

		# +++++++++++++++++++++++++++++++

		row += 1
		w = LabelFrame (master, text = 'Options')
		w.grid (row = row, column = col,
				sticky = NSEW, padx = 5, pady = 5)

		self.populateOptions (w)

		# +++++++++++++++++++++++++++++++

	def populateLimits (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 200)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Current (μA)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxCurrent = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Voltage (mV)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxVoltage = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Power (mW)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxPower = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Whichever happens first', anchor = E)
		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

	def populateOptions (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 200)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Bipolar', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wBipolar = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

		# row += 1; col = 0
		w = Label (master, text = 'R track mode', anchor = W)
		# w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		# col += 1
		w = self.wResTrackMode = Label (master, anchor = E)
		# w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]
			self.wMaxCurrent   ['text'] = first.wMaxCurrent   ['text']
			self.wMaxVoltage   ['text'] = first.wMaxVoltage   ['text']
			self.wMaxPower     ['text'] = first.wMaxPower     ['text']
			self.wBipolar      ['text'] = first.wBipolar      ['text']
			self.wResTrackMode ['text'] = first.wResTrackMode ['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _set (self, maxCurrent, maxVoltage, maxPower, bipolar, resTrackMode):

		bipolarModes = {
			True  : 'Yes',
			False : 'No'
		}

		resTrackModes = {
			R_TRACK_V_I   : u'V/I',
			R_TRACK_dV_dI : u'ΔV/ΔI'
		}

		self.wMaxCurrent   ['text'] = str (A_to_uA * maxCurrent)
		self.wMaxVoltage   ['text'] = str (V_to_mV * maxVoltage)
		self.wMaxPower     ['text'] = str (W_to_mW * maxPower)
		self.wBipolar      ['text'] = bipolarModes.get (bipolar)
		self.wResTrackMode ['text'] = resTrackModes.get (resTrackMode)

	def set (self, maxCurrent, maxVoltage, maxPower, bipolar, resTrackMode):

		for instance in self.instances:
			instance._set (maxCurrent, maxVoltage,
				  maxPower, bipolar, resTrackMode)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):
		self.wMaxCurrent   ['text'] = '...'
		self.wMaxVoltage   ['text'] = '...'
		self.wMaxPower     ['text'] = '...'
		self.wBipolar      ['text'] = '...'
		self.wResTrackMode ['text'] = '...'

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# coding: utf-8

from tkFont            import Font
from Tkinter           import *
from time              import time as systime, localtime
from tkFileDialog      import askopenfile, asksaveasfile
import os

from XWidget           import XFloatEntry, XIntegerEntry, XScroll, XTab
from XHIRES_Constants  import *
from XHIRES_Banner     import banner
import Plot2D
import Preferences

class GUI:

	run_modes = {
		RUN_MODE_ITime : 'I-Time',
		RUN_MODE_IV    : 'I-V',
		RUN_MODE_RTime : 'R-Time'
	}

	methodFileTypes = [
		('XPLORE method files' , '*.xmt'),
		('All files'           , '*.*')
	]

	def __init__ (self, master, sample):
		self.master = master
		self.sample = sample
		self.master.title ('XPLORE High Resistance Measurement unit')
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
		w = Label (master, text = 'Range', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wVSRangeValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wVSRangeUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Drive', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wVSValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w, mul = 1.0)

		col += 1
		w = self.wVSUnit = Label (master, anchor = W)
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
			self.wVSRangeValue,
			self.wVSRangeUnit,
			self.wVSValue,
			self.wVSUnit,
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

			self.set_status ('HiRes connected')

		elif connection == DEVICE_DISCONNECTING :

			self.filemenu.entryconfig (
				0, label = 'Disconnecting', state = DISABLED, command = None)

		elif connection == DEVICE_DISCONNECTED :

			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.set_status ('HiRes disconnected')
			self.blank_parameters()

		elif connection == DEVICE_NOT_FOUND :

			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.set_status ('HiRes not found')
			self.blank_parameters()

		else: raise ValueError (connection)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, run_mode):

		self.run_mode.set (self.run_modes.get (run_mode))

		for w in (self.wIVRampSettings, self.wOhmmeterSettings):
			w.master.grid_forget()

		options = {

			RUN_MODE_IV    : (
				self.grid_IVRampSettings, self.wIVRampSettings),

			RUN_MODE_RTime : (
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

	def VS_setRange (self, vs_autorange, vs_range, vs_value):

		ranges = {
			VS_RANGE_10V  : ('±10',  'V'),
			VS_RANGE_100V : ('±100', 'V')
		}

		(fullscale, unit) = ranges[vs_range]
		self.wVSRangeValue['text'] = fullscale
		self.wVSRangeUnit ['text'] = unit

		# +++++++++++++++++++++++++++++++++++++++++++++++++

		src_fmts = {
			VS_RANGE_10V  : ('%+08.3f', 1.0, 'V'),
			VS_RANGE_100V : ('%+08.2f', 1.0, 'V')
		}

		(fmt, mult, unit) = src_fmts[vs_range]
		self.wVSValue ['text'] = str (fmt % (vs_value * mult))
		self.wVSUnit  ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setRange (self, cm_autorange, cm_range):

		cm_ranges = {
			CM_RANGE_10nA    : ('±10',  'nA'),
			CM_RANGE_1uA     : ('±1',   'uA')
		}

		(fullscale, unit) = cm_ranges.get (cm_range)
		self.wCMRangeValue ['text'] = fullscale
		self.wCMRangeUnit  ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM_setRange (self, vm_autorange, vm_range):

		vm_ranges = {
			VM_RANGE_100V  : ('±100',  'V')
		}

		(fullscale, unit) = vm_ranges.get (vm_range)
		self.wVMRangeValue ['text'] = fullscale
		self.wVMRangeUnit  ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setReading (self, range, reading):

		fmts = {
			CM_RANGE_10nA  : ('%+09.5f', 1e9, 'nA'),
			CM_RANGE_1uA   : ('%+09.6f', 1e6, 'uA')
		}

		(fmt, mult, unit) = fmts.get (range, ('%e', 1.0, 'A'))
		self.wCMValue['text'] = str (fmt % (reading * mult))
		self.wCMUnit ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM_setReading (self, range, reading):

		fmts = {
			VM_RANGE_100V  : ('%+09.4f', 1.0,  'V')
		}

		(fmt, mult, unit) = fmts.get (range, ('%e', 1.0, 'V'))
		self.wVMValue['text'] = str (fmt % (reading * mult))
		self.wVMUnit ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def set_status (self, text):

		lt = localtime (systime())
		time_stamp = (
			str ('%02d' % lt.tm_hour) + ':' +
			str ('%02d' % lt.tm_min)  + ':' +
			str ('%02d' % lt.tm_sec))

		text = '<' + time_stamp + ':XHIRES> ' + text
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
		self, finalVoltage, voltageStep, bipolar):

		self.wIVRampSettings.set (
			finalVoltage, voltageStep, bipolar)

	def setOhmmeterSettings (self, maxVoltage, bipolar):

		self.wOhmmeterSettings.set (maxVoltage, bipolar)

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

	vs_autoranges = {
		True  : 'Yes',
		False : 'No'
	}

	vs_ranges = {
		VS_RANGE_10V  : u'±10V',
		VS_RANGE_100V : u'±100V'
	}

	def __init__ (self, master, vs_autorange,
			   vs_range, vs_value):

		self.master = master
		self.master.title ('Source parameters')
		self.createWidgets (master)

		self.VS_setAutoRange (vs_autorange)
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
		w = self.wVoltageSourceFrame = \
			LabelFrame (master, text = 'Voltage source parameters')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

		self.populateVoltageSourceFrame (w)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateVoltageSourceFrame (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [10, 15]

		row = 0; col = 0
		w = Label (master, text = 'Auto range')
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.vs_autoranges.values()
		var = self.vs_autorange = StringVar()

		w = self.wVSAutoRange = \
			OptionMenu (master, var, *options,
			   command = self.wVSAutoRangeCB)

		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Range', anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.vs_ranges.values()
		var = self.vs_range = StringVar()
		w = self.wVoltageSourceRange = OptionMenu (master, var, *options)

		#menu = w['menu']
		#menu.entryconfig (1, state = ENABLED) # ±100V

		w.config (anchor = W, width = col_widths[col])
		w.config (state = DISABLED if self.vs_autorange else NORMAL)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Value (V)',
			 anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.vs_value = XFloatEntry (master, width = col_widths[col])
		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wVSAutoRangeCB (self, autorange):
		self.VS_setAutoRange (self.VS_getAutoRange())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VS_getAutoRange (self):
		vs_autoranges = {v : k for (k, v) in self.vs_autoranges.items()}
		return vs_autoranges.get (self.vs_autorange.get())

	def VS_getRange (self):
		vs_ranges = {v : k for (k, v) in self.vs_ranges.items()}
		return vs_ranges.get (self.vs_range.get())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wApplyCB (self):

		autorange = self.VS_getAutoRange()

		(range, value) = (self.VS_getRange(), self.vs_value.get())

		self.do_callback (APPLY, autorange, range, value)

	def wCancelCB (self):
		self.do_callback (CANCEL)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VS_setAutoRange (self, autorange):

		self.vs_autorange.set (self.vs_autoranges.get (autorange))

		state_options = {True : DISABLED, False : NORMAL}
		self.wVoltageSourceRange.config (state = state_options.get (autorange))

	def VS_setRange (self, vs_range, vs_value):
		self.vs_range.set (self.vs_ranges.get (vs_range))
		self.vs_value.set (vs_value)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_MeterParameters:

	autoranges = {
		True  : 'Yes',
		False : 'No'
	}

	cm_ranges = {
		CM_RANGE_10nA  : u'±10nA',
		CM_RANGE_1uA   : u'±1μA'
	}

	vm_ranges = {
		VM_RANGE_100V  : u'±100V'
	}

	def __init__ (
		self, master,
		cm_autorange, cm_range, vm_autorange, vm_range):

		self.master = master
		self.master.title ('Meter parameters')
		self.createWidgets (master)

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

		self.wAmmeterAutoRange.config (state = NORMAL)

	def setAmmeterRange (self, cm_autorange, cm_range):

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

	def __init__ (
		self, master, finalVoltage, voltageStep, bipolar):

		self.master = master
		self.master.title ('I-V ramp settings')
		self.createWidgets (master)
		self.set (finalVoltage, voltageStep, bipolar)

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
		w = Label (master, text = 'Voltage (V)',
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

	def populateStepSize (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 10]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Voltage (V)',
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

	def wApplyCB (self):

		bipolarModes  = {v : k for (k, v) in self.bipolarMenuItems.items()}

		self.do_callback (APPLY,
			self.wFinalVoltage.get(),
			self.wVoltageStep.get(),
			bipolarModes.get (self.bipolar.get()))

	def wCancelCB (self):
		self.do_callback (CANCEL)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def set (self, finalVoltage, voltageStep, bipolar):

		self.wFinalVoltage.set (finalVoltage)
		self.wVoltageStep.set  (voltageStep)
		self.bipolar.set       (self.bipolarMenuItems.get (bipolar))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_IVRampSettingsDisplay:

	bipolarMenuItems = {
		True  : 'Yes',
		False : 'No'
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
		w = Label (master, text = 'Voltage (V)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalVoltage = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++
		# +++++++++++++++++++++++++++++++

	def populateStepSize (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		col_widths = [20, 10]

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Voltage (V)', anchor = W)
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

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]
			self.wFinalVoltage ['text'] = first.wFinalVoltage ['text']
			self.wVoltageStep  ['text'] = first.wVoltageStep  ['text']
			self.wBipolar      ['text'] = first.wBipolar      ['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _set (self, finalVoltage, voltageStep, bipolar):

		self.wFinalVoltage ['text'] = str (finalVoltage)
		self.wVoltageStep  ['text'] = str (voltageStep)
		self.wBipolar      ['text'] = self.bipolarMenuItems.get (bipolar)

	def set (self, finalVoltage, voltageStep, bipolar):

		for instance in self.instances:
			instance._set (finalVoltage, voltageStep, bipolar)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):
		self.wFinalVoltage ['text'] = '...'
		self.wVoltageStep  ['text'] = '...'
		self.wBipolar      ['text'] = '...'

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

	def __init__ (
		self, master, maxVoltage, bipolar):

		self.master = master
		self.master.title ('Resistance measurement settings')
		self.createWidgets (master)
		self.set (maxVoltage, bipolar)

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
		w = Label (master, text = 'Voltage (V)',
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

	def wApplyCB (self):

		bipolarModes  = {v : k for (k, v) in self.bipolarMenuItems.items()}

		self.do_callback (
			APPLY,
			self.wMaxVoltage.get(),
			bipolarModes.get (self.bipolar.get()))

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, maxVoltage, bipolar):
		self.wMaxVoltage.set  (maxVoltage)
		self.bipolar.set      (self.bipolarMenuItems.get  (bipolar))

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
		w = Label (master, text = 'Voltage (V)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.wMaxVoltage = Label (master, anchor = E)
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

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]
			self.wMaxVoltage   ['text'] = first.wMaxVoltage   ['text']
			self.wBipolar      ['text'] = first.wBipolar      ['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _set (self, maxVoltage, bipolar):

		bipolarModes = {
			True  : 'Yes',
			False : 'No'
		}

		self.wMaxVoltage   ['text'] = str (maxVoltage)
		self.wBipolar      ['text'] = bipolarModes.get (bipolar)

	def set (self, maxVoltage, bipolar):

		for instance in self.instances:
			instance._set (maxVoltage, bipolar)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):
		self.wMaxVoltage   ['text'] = '...'
		self.wBipolar      ['text'] = '...'

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# coding: utf-8

from tkFont            import Font
from Tkinter           import *
from time              import time as systime, localtime
from tkFileDialog      import askopenfile, asksaveasfile
import os

from XWidget           import XFloatEntry, XIntegerEntry, XScroll, XTab
from MGPS_Constants    import *
from MGPS_Banner       import banner
import Plot2D
import Preferences

def updateParamFont (widget, mul = 2, weight = 'bold'):
	font = Font (widget, widget['font'])
	font.config (size = int (round (mul * font['size'])), weight = weight)
	widget.config (font = font)

class GUI:

	run_modes = {
		RUN_MODE_HTime : 'H-Time',
		RUN_MODE_ITime : 'I-Time',
		RUN_MODE_VTime : 'V-Time'
	}

	methodFileTypes = [
		('XPLORE method files' , '*.xmt'),
		('All files'           , '*.*')
	]

	calibrationFileTypes = [
		('CSV files'               , '*.csv'),
	]

	def __init__ (self, master, sample):
		self.master = master
		self.sample = sample
		self.master.title ('XPLORE Magnet Power Supply')
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
		for w in [
			self.wSourceSettings,
			self.wAcquisitionSettings
		]:
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
			label   = 'Acquisition settings',
			command = self.wAcquisitionSettingsCB)

		self.utilmenu.add_separator()

		self.utilmenu.add_command (
			label   = 'Source parameters',
			command = self.wSourceParametersCB)

		self.utilmenu.add_command (
			label   = 'Meter parameters',
			command = self.wMeterParametersCB)

		# ++++ Populating Calibration menu +++++

		self.calibrationmenu = Menu (self.mainmenu)
		self.calibrationmenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'Calibration', menu = self.calibrationmenu, underline = 0)

		self.calibrationmenu.add_command (
			label   = 'Upload Calibration',
			command = self.wUploadCalibrationCB)

	def populateDisplayPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# ++++ Run control ++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Run control')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateControlFrame (w)

		# ++++ Source parameters display ++++

		row += 1; col = 0
		w = self.wSourceSettings = \
			GUI_SourceSettingsDisplay (master = Frame (master))

		w.master.grid (row = row, column = col, sticky = NSEW)

		# ++++ Meter parameters display ++++

		row += 1; col = 0
		w = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populateMeterFrame (w)

		# ++++ Acquisition settings display ++++

		row += 1; col = 0
		w = self.wAcquisitionSettings = (
			GUI_AcquisitionSettingsDisplay (master = Frame (master)))

		w.master.grid (row = row, column = col, sticky = NSEW)

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


	def populateMeterFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Gauss meter')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateGaussMeterFrame (w)

		row += 1
		w = LabelFrame (master, text = 'Ammeter')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateAmmeterFrame (w)

		row += 1
		w = LabelFrame (master, text = 'Voltmeter')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateVoltmeterFrame (w)

	def populateGaussMeterFrame (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 100)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)
		master.grid_columnconfigure (2, weight = 0, minsize =  30)

		# +++++++++++ Range ++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Range', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wHMRangeValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wHMRangeUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++ Value +++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Magnetic Field', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wHMValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		updateParamFont (w, mul = 1.0)

		col += 1
		w = self.wHMUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		updateParamFont (w, mul = 1.0)

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
		updateParamFont (w, mul = 1.0)

		col += 1
		w = self.wCMUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		updateParamFont (w, mul = 1.0)


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
		updateParamFont (w, mul = 1.0)

		col += 1
		w = self.wVMUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		updateParamFont (w, mul = 1.0)

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

			self.wHMRangeValue,
			self.wHMRangeUnit,
			self.wHMValue,
			self.wHMUnit,

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

	def wAcquisitionSettingsCB (self, *args):
		self.do_callback (OPEN_DIALOG, ACQUISITION_SETTINGS_DIALOG)

	def wSourceParametersCB (self, *args):
		self.do_callback (OPEN_DIALOG, SOURCE_PARAMETERS_DIALOG)

	def wMeterParametersCB (self, *args):
		self.do_callback (OPEN_DIALOG, METER_SETTINGS_DIALOG)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def wUploadCalibrationCB (self, *args):

		try:
			(sampleName, sampleID, _) = self.sample.get()

			folder =  os.path.expanduser('~')
			fd = askopenfile (parent = self.master,
				initialdir = folder, filetypes = self.calibrationFileTypes)
			if fd != None : self.do_callback (UPLOAD_CALIBRATION, fd)

		except (OSError, IOError) as e:
			self.set_status (str (e))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

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

			self.set_status ('MGPS connected')

		elif connection == DEVICE_DISCONNECTING :

			self.filemenu.entryconfig (
				0, label = 'Disconnecting', state = DISABLED,
				command = None)

		elif connection == DEVICE_DISCONNECTED :

			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.set_status ('MGPS disconnected')
			self.blank_parameters()

		elif connection == DEVICE_NOT_FOUND :

			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.set_status ('MGPS not found')
			self.blank_parameters()

		else: raise ValueError (connection)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, run_mode):
		self.run_mode.set (self.run_modes.get (run_mode))

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
		self.wSourceSettings.set (mode, autorange, range, value)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HM_setRange (self, hm_autorange, hm_range):

		hm_ranges = {
			HM_RANGE_1 : ('±100',  'mT')
		}

		(fullscale, unit) = hm_ranges.get (hm_range)
		self.wHMRangeValue ['text'] = fullscale
		self.wHMRangeUnit  ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setRange (self, cm_autorange, cm_range):

		cm_ranges = {
			CM_RANGE_1 : ('±6',  'A')
		}

		(fullscale, unit) = cm_ranges.get (cm_range)
		self.wCMRangeValue ['text'] = fullscale
		self.wCMRangeUnit  ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM_setRange (self, vm_autorange, vm_range):

		vm_ranges = {
			VM_RANGE_1   : ('±20',   'V')
		}

		(fullscale, unit) = vm_ranges.get (vm_range)
		self.wVMRangeValue ['text'] = fullscale
		self.wVMRangeUnit  ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HM_setReading (self, range, reading):

		fmts = {
			HM_RANGE_1  : ('%+05.3f', 1e3, 'mT')
		}

		(fmt, mult, unit) = fmts.get (range, ('%e', 1e3, 'mT'))
		self.wHMValue['text'] = str (fmt % (reading * mult))
		self.wHMUnit ['text'] = unit


	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setReading (self, range, reading):

		fmts = {
			CM_RANGE_1  : ('%+05.5f', 1, 'A')
		}

		(fmt, mult, unit) = fmts.get (range, ('%e', 1.0, 'A'))
		self.wCMValue['text'] = str (fmt % (reading * mult))
		self.wCMUnit ['text'] = unit

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM_setReading (self, range, reading):

		fmts = {
			VM_RANGE_1   : ('%+02.3f', 1, 'V')
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

		text = '<' + time_stamp + ':MGPS> ' + text
		print text

		old_text = self.wStatus['text']
		new_text = text + '    .    ' + old_text
		new_text = new_text[:1024]
		self.wStatus['text'] = new_text

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setAcquisitionSettings (self, delay, filterLength):
		self.wAcquisitionSettings.set (delay, filterLength)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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
		SOURCE_MODE_HS : 'Magnetic Field',
		SOURCE_MODE_CS : 'Current'
	}

	autoranges = {
		True  : 'Yes',
		False : 'No'
	}

	cs_ranges = {
		CS_RANGE_1  : u'±6A'
	}

	hs_ranges = {
		HS_RANGE_1  : u'±100mT'
	}

	def __init__ (self, master, mode, autorange, \
				cs_range, cs_value, hs_range, hs_value):

		self.master = master
		self.master.title ('Source parameters')
		self.createWidgets (master)

		self.setMode (mode)
		self.setAutoRange (autorange)
		self.CS_setRange (cs_range, cs_value)
		self.HS_setRange (hs_range, hs_value)

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

		w = self.wMagneticFieldSourceFrame = \
			LabelFrame (master, text = 'Magnetic Field source parameters')

		self.populateMagneticFieldSourceFrame (w)

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
		var = self.cs_range = StringVar()
		options = self.cs_ranges.values()
		w = self.wCurrentSourceRange = OptionMenu (master, var, *options)

		w.config (anchor = W, width = col_widths[col])
		w.config (state = DISABLED if self.autorange else NORMAL)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Value (A)',
			 anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.cs_value = XFloatEntry (master, width = col_widths[col])
		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateMagneticFieldSourceFrame (self, master):
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
		var = self.hs_range = StringVar()
		options = self.hs_ranges.values()
		w = self.wMagneticFieldSourceRange = OptionMenu (master, var, *options)

		w.config (anchor = W, width = col_widths[col])
		w.config (state = DISABLED if self.autorange else NORMAL)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Value (mT)',
			 anchor = W, width = col_widths[col])

		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		w = self.hs_value = XFloatEntry (master, width = col_widths[col])
		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
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

	def CS_getRange (self):
		cs_ranges = {v : k for (k, v) in self.cs_ranges.items()}
		return cs_ranges.get (self.cs_range.get())

	def HS_getRange (self):
		hs_ranges = {v : k for (k, v) in self.hs_ranges.items()}
		return hs_ranges.get (self.hs_range.get())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wApplyCB (self):
		mode      = self.getMode()
		autorange = self.getAutoRange()

		(range, value) = {

			SOURCE_MODE_HS : (

				self.HS_getRange(),
				self.hs_value.get() * mT_to_T
			),

			SOURCE_MODE_CS : (

				self.CS_getRange(),
				self.cs_value.get()
			)

		}.get (mode)

		self.do_callback (APPLY, mode, autorange, range, value)

	def wCancelCB (self):
		self.do_callback (CANCEL)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setMode (self, mode):

		self.mode.set (self.modes.get (mode))

		for frame in (self.wCurrentSourceFrame, self.wMagneticFieldSourceFrame):
			frame.grid_forget()

		(row, col) = self.sourceFrameGrid

		frames = {
			SOURCE_MODE_CS : self.wCurrentSourceFrame,
			SOURCE_MODE_HS : self.wMagneticFieldSourceFrame
		}

		w = frames.get (mode)
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

	def setAutoRange (self, autorange):
		self.autorange.set (self.autoranges.get (autorange))
		state_options = {True : DISABLED, False : NORMAL}

		for w in (self.wCurrentSourceRange,
				  self.wMagneticFieldSourceRange):
			w.config (state = state_options.get (autorange))

	def HS_setRange (self, hs_range, hs_value):
		self.hs_range.set (self.hs_ranges.get (hs_range))
		self.hs_value.set (round ((hs_value * T_to_mT), 2))

	def CS_setRange (self, cs_range, cs_value):
		self.cs_range.set (self.cs_ranges.get (cs_range))
		self.cs_value.set (round (cs_value, 4))

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_MeterParameters:

	autoranges = {
		True  : 'Yes',
		False : 'No'
	}

	hm_ranges = {
		HS_RANGE_1  : u'±100mT'
	}

	cm_ranges = {
		CM_RANGE_1  : u'±6A'
	}

	vm_ranges = {
		VM_RANGE_1   : u'±20V'
	}

	def __init__ ( \
		self, master, \
		hm_autorange, hm_range, \
		cm_autorange, cm_range, \
		vm_autorange, vm_range):

		self.master = master
		self.master.title ('Meter parameters')
		self.createWidgets (master)

		self.HM_setRange (hm_autorange, hm_range)
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
		w = Label (master, text = 'HM Auto range')
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.autoranges.values()
		var = self.hm_autorange = StringVar()

		w = self.wGaussMeterAutoRange = OptionMenu (
			master, var, *options, command = self.wGaussMeterCB)

		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'HM Range')
		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		col += 1
		options = self.hm_ranges.values()
		var = self.hm_range = StringVar()
		w = self.wGaussMeterRange = OptionMenu (
			master, var, *options, command = self.wGaussMeterCB)

		menu = w['menu']
		for index in [HM_RANGE_1]:
			menu.entryconfig (index, state = DISABLED)

		w.config (anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
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
		for index in [CM_RANGE_1]:
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
		for index in [VM_RANGE_1]:
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

	def getGaussMeterAutoRange (self):
		autoranges = {v : k for (k, v) in self.autoranges.items()}
		return autoranges.get (self.hm_autorange.get())

	def getAmmeterAutoRange (self):
		autoranges = {v : k for (k, v) in self.autoranges.items()}
		return autoranges.get (self.cm_autorange.get())

	def getGaussMeterRange (self):
		autoranges = {v : k for (k, v) in self.autoranges.items()}
		return autoranges.get (self.hm_autorange.get())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def wGaussMeterCB (self, *args):

		self.HM_setRange (
			self.getGaussMeterAutoRange(),
			self.getGaussMeterRange())

		self.do_callback (
			CM_RANGE_CHANGED,
			self.getGaussMeterAutoRange(),
			self.getGaussMeterRange())

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

	def HM_setRange (self, hm_autorange, hm_range):
		self.setGaussMeterAutoRange (hm_autorange)
		self.setGaussMeterRange (hm_autorange, hm_range)

	def setGaussMeterAutoRange (self, hm_autorange):
		self.hm_autorange.set (self.autoranges.get (hm_autorange))

	def setGaussMeterRange (self, hm_autorange, hm_range):

		if   hm_autorange == True  : state = DISABLED
		elif hm_autorange == False : state = NORMAL

		self.wGaussMeterRange.config (state = state)
		self.hm_range.set (self.hm_ranges.get (hm_range))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setRange (self, cm_autorange, cm_range):
		self.setAmmeterAutoRange (cm_autorange)
		self.setAmmeterRange (cm_autorange, cm_range)

	def setAmmeterAutoRange (self, cm_autorange):
		self.cm_autorange.set (self.autoranges.get (cm_autorange))

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
		w = LabelFrame (master, text = 'Acquisition Settings')
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

class GUI_SourceSettingsDisplay:

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
		w = self.wFrame = LabelFrame (master, text = 'Source Settings')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateSourceFrame (w)

	def populateSourceFrame (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 100)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)
		master.grid_columnconfigure (2, weight = 0, minsize = 30)

		row = 0; col = 0
		w = Label (master, text = 'Source mode', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wSourceMode = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

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
		updateParamFont (w, mul = 1.0)

		col += 1
		w = self.wSourceUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		updateParamFont (w, mul = 1.0)

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]

			widgets = [
				(self.wSourceMode       , first.wSourceMode       ),
				(self.wSourceRangeValue , first.wSourceRangeValue ),
				(self.wSourceRangeUnit  , first.wSourceRangeUnit  ),
				(self.wSourceValue      , first.wSourceValue      ),
				(self.wSourceUnit       , first.wSourceUnit       ),
			]

			for (wSelf, wFirst) in widgets:
				wSelf['text'] = wFirst['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _set (self, mode, autorange, range, value):

		modes = {

			SOURCE_MODE_HS : 'Magnetic field',
			SOURCE_MODE_CS : 'Current',
		}

		self.wSourceMode['text'] = modes.get (mode)

		# +++++++++++++++++++++++++++++++++++++++++++++++++

		ranges = {

			SOURCE_MODE_HS : {
				HS_RANGE_1 : ('±100',  'mT'),
			},

			SOURCE_MODE_CS : {
				CS_RANGE_1  : ('±6',  'A'),
			}
		}

		(fullscale, unit) = ranges[mode][range]
		self.wSourceRangeValue['text'] = fullscale
		self.wSourceRangeUnit ['text'] = unit

		# +++++++++++++++++++++++++++++++++++++++++++++++++

		src_fmts = {

			SOURCE_MODE_HS : {
				HS_RANGE_1 : ('%+05.2f', 1e3, 'mT'),
			},

			SOURCE_MODE_CS : {
				CS_RANGE_1 : ('%+05.2f', 1, 'A'),
			},
		}

		(fmt, mult, unit) = src_fmts[mode][range]
		self.wSourceValue ['text'] = str (fmt % (value * mult))
		self.wSourceUnit  ['text'] = unit


	def set (self, mode, autorange, range, value):
		for instance in self.instances:
			instance._set (mode, autorange, range, value)

	def label (self, value):
		self.wFrame ['text'] = value

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):

		self.wSourceMode        ['text'] = '...'
		self.wSourceRangeValue  ['text'] = '...'
		self.wSourceRangeUnit   ['text'] = '...'
		self.wSourceValue       ['text'] = '...'
		self.wSourceUnit        ['text'] = '...'

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

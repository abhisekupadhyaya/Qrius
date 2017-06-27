# coding: utf-8

from XLIA_Constants import *
from XLIA_Banner    import banner
from XWidget        import XFloatEntry, XIntegerEntry
from XWidget        import XScroll, XTab

from tkFileDialog import askopenfile, asksaveasfile
import os

from tkFont  import Font
from Tkinter import Frame, LabelFrame
from Tkinter import Label, Menu, OptionMenu, StringVar, Button
from Tkinter import NORMAL, DISABLED, E, W, NSEW, RIGHT, LEFT
from Tkinter import PhotoImage
from time    import time as systime, localtime
from math    import log10

import Plot2D
import Preferences

class GUI:

	run_modes = {
		RUN_MODE_VF    : 'V-F',
		RUN_MODE_VTime : 'V-Time'
	}

	methodFileTypes = [
		('XPLORE method files' , '*.xmt'),
		('All files'           , '*.*')
	]

	def __init__ (self, master, sample):
		self.master = master
		self.sample = sample
		self.master.title ('Xplore Lock-in Amplifier')
		self.createWidgets (master)
		self.blank_parameters()
		self.putBanner()

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def close (self):

		for (w, r, c) in (self.wReferenceSettingsDisplay,
						  self.wMeasurementSettingsDisplay,
						  self.wAcquisitionSettingsDisplay,
						  self.wVFRampSettingsDisplay):
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

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (
			label = 'Connect', command = self.wConnectCB)

		self.filemenu.add_command (
			label = 'Open method', command = self.wOpenMethodCB)

		self.filemenu.add_command (
			label = 'Save method', command = self.wSaveMethodCB)

		self.filemenu.add_command (
			label = 'Hide', command = self.wHideCB)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		self.utilmenu = Menu (self.mainmenu)
		self.utilmenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'Settings', menu = self.utilmenu, underline = 0)

		self.utilmenu.add_command (label = 'Reference settings',
							command = self.wReferenceSettingsCB)

		self.utilmenu.add_command (label = 'Measurement settings',
							command = self.wMeasurementSettingsCB)

		self.utilmenu.add_separator()

		self.utilmenu.add_command (label = 'Acquisition settings',
							command = self.wAcquisitionSettingsCB)

		self.utilmenu.add_command (label = 'V-F ramp settings',
							command = self.wVFRampSettingsCB)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateDisplayPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# ++++ Run control ++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Run control')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateControlFrame (w)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		(w, r, c) = self.wReferenceSettingsDisplay = (
			GUI_ReferenceSettingsDisplay (master = Frame (master)),
			row, col)

		w.master.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		(w, r, c) = self.wMeasurementSettingsDisplay = (
			GUI_MeasurementSettingsDisplay (master = Frame (master)),
			row, col)

		w.master.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = self.wReadoutDisplay = \
			GUI_OutputDisplay (master = Frame (master))

		w.master.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		(w, r, c) = self.wAcquisitionSettingsDisplay = (
			GUI_AcquisitionSettingsDisplay (master = Frame (master)),
			row, col)

		w.master.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		(w, r, c) = self.wVFRampSettingsDisplay = (
			GUI_VFRampSettingsDisplay (master = Frame (master)),
			row, col)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateControlFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 100)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)

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
		row = 0; col = 0
		w = self.wStatus = Label (master, text = '...', anchor = W, width = 30)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def wConnectCB (self):
		self.do_callback (CONNECT_DEVICE)

	def wDisconnectCB (self):
		self.do_callback (DISCONNECT_DEVICE)

	def wHideCB (self):
		self.master.withdraw()

	def wReferenceSettingsCB (self):
		self.do_callback (OPEN_DIALOG, REFERENCE_PARAMETER_DIALOG)

	def wMeasurementSettingsCB (self):
		self.do_callback (OPEN_DIALOG, MEASUREMENT_SETTINGS_DIALOG)

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

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def setConnectionStatus (self, status):

		if status == DEVICE_CONNECTING:
			self.filemenu.entryconfig (
				0, label = 'Connecting', state = DISABLED, command = None)

		elif status == DEVICE_CONNECTED:
			self.filemenu.entryconfig (
				0, label = 'Disconnect', state = NORMAL,
				command = self.wDisconnectCB)

			self.set_status ('Lock-in amplifier connected')

		elif status == DEVICE_DISCONNECTING:
			self.filemenu.entryconfig (
				0, label = 'Disconnecting', state = DISABLED, command = None)

		elif status == DEVICE_DISCONNECTED:
			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectCB)

			self.blank_parameters()
			self.set_status ('Lock-in amplifier disconnected')

		elif status == DEVICE_NOT_FOUND:
			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectCB)

			self.blank_parameters()
			self.set_status ('Lock-in amplifier not found')

		else: raise ValueError (status)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def set_status (self, text):

		lt = localtime (systime())
		time_stamp = (
			str ('%02d' % lt.tm_hour) + ':' +
			str ('%02d' % lt.tm_min)  + ':' +
			str ('%02d' % lt.tm_sec))

		text = '<' + time_stamp + ':XLIA> ' + text
		print text

		old_text = self.wStatus['text']
		new_text = text + '    .    ' + old_text
		new_text = new_text[:1024]
		self.wStatus['text'] = new_text

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def setReferenceParameters (self, ampl, freq, phase):
		(w, r, c) = self.wReferenceSettingsDisplay
		w.set (ampl, freq, phase)

	def setMeasurementSettings (
		self, inputChannel, preAmpCoupling,
		preAmpGain, postAmpGain, intgtrTC):

		(w, r, c) = self.wMeasurementSettingsDisplay
		w.set (inputChannel, preAmpCoupling,
			   preAmpGain, postAmpGain, intgtrTC)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def setReadoutDisplay (
		self, ampl, phase, inphase,
		quad, preAmpGain, postAmpGain):

		self.wReadoutDisplay.set (
			ampl, phase, inphase,
			quad, preAmpGain, postAmpGain)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, run_mode):

		self.run_mode.set (self.run_modes.get (run_mode))

		for (w, row, col) in (self.wVFRampSettingsDisplay,):
			w.master.grid_forget()

		options = {
			RUN_MODE_VF : self.wVFRampSettingsDisplay
		}

		if run_mode in options:
			w = options.get (run_mode)
			if w != None:
				(w, row, col) = w
				w.master.grid (row = row, column = col, sticky = NSEW)


	def getRunMode (self):
		run_modes = {v : k for (k, v) in self.run_modes.items()}
		return run_modes.get (self.run_mode.get())

	def wRunModeCB (self, *args):
		self.do_callback (RUN_MODE, self.getRunMode())

	def wStartCB (self):
		self.do_callback (START_RUN, self.getRunMode())

	def wFinishCB (self):
		self.do_callback (FINISH_RUN)

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

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def wAcquisitionSettingsCB (self):
		self.do_callback (OPEN_DIALOG, ACQUISITION_SETTINGS_DIALOG)

	def setAcquisitionSettings (
		self, delay, filterLength, driveMode,
		driveCurrentSetPoint, driveVoltageSetPoint):

		(w, r, c) = self.wAcquisitionSettingsDisplay
		w.set (delay, filterLength, driveMode,
			   driveCurrentSetPoint, driveVoltageSetPoint)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def wVFRampSettingsCB (self):
		self.do_callback (OPEN_DIALOG, VF_RAMP_SETTINGS_DIALOG)

	def setVFRampSettings (
		self, initialFrequency, finalFrequency,
		linearFreqStep, logFreqStep, frequencySteppingMode):

		(w, row, col) = self.wVFRampSettingsDisplay
		w.set (initialFrequency, finalFrequency,
				linearFreqStep, logFreqStep, frequencySteppingMode)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def blank_parameters (self):
		(w, r, c) = self.wReferenceSettingsDisplay
		w.blank_parameters()

		(w, r, c) = self.wMeasurementSettingsDisplay
		w.blank_parameters()

		self.wReadoutDisplay.blank_parameters()

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def putBanner (self):
		w = GUI_Banner (self.wPlots.add ('Welcome'))
		w.grid (row = 0, column = 0, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

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

class GUI_ReferenceSettings:

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		master.title ('Reference settings')

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		self.populateMenu (master)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Reference generator')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateReferenceFrame (w)

	def populateMenu (self, master):

		### Main Menu
		self.mainmenu = Menu (master)
		self.mainmenu.config (borderwidth = 1)
		master.config (menu = self.mainmenu)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (
			label = 'Apply', command = self.wApplyCB)

		self.filemenu.add_command (
			label = 'Cancel', command = self.wCancelCB)

	def populateReferenceFrame (self, master):

		master.grid_columnconfigure (0, weight = 0)
		master.grid_columnconfigure (1, weight = 1)
		master.grid_columnconfigure (2, weight = 0)

		col_widths = [10, 10, 3]

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Amplitude',
			anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wRefAmpl = \
			XFloatEntry (master, justify = RIGHT, width = col_widths[col])

		w.fmt ('%.1f')
		w.enable_color (enable = False)
		w.callback (self.wRefParamCB)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = 'mV', anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Frequency',
			anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wRefFreq = \
			XFloatEntry (master, justify = RIGHT, width = col_widths[col])

		w.fmt ('%.2f')
		w.enable_color (enable = False)
		w.callback (self.wRefParamCB)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = 'Hz', anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Phase', anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wRefPhase = \
			XFloatEntry (master, justify = RIGHT, width = col_widths[col])

		w.fmt ('%+06.1f')
		w.enable_color (enable = False)
		w.callback (self.wRefParamCB)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = '°', anchor = W, width = col_widths[col])
		w.grid (row = row, column = col, sticky = NSEW)

	def wRefParamCB (self, *args):
		ampl  = self.wRefAmpl.get() * mV_to_V
		freq  = self.wRefFreq.get()
		phase = self.wRefPhase.get() * deg_to_rad
		self.do_callback (REFERENCE_PARAMETER, ampl, freq, phase)

	def wApplyCB (self, *args):
		self.do_callback (APPLY)

	def wCancelCB (self, *args):
		self.do_callback (CANCEL, self._ampl, self._freq, self._phase)

	def set (self, ampl, freq, phase):

		# ++++ Saves the supplied values in case the dialog is cancelled ++++
		self._ampl  = ampl
		self._freq  = freq
		self._phase = phase

		self.wRefAmpl.set (ampl * V_to_mV)
		self.wRefFreq.set (freq)
		self.wRefPhase.set (rad_to_deg * phase)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_ReferenceSettingsDisplay:

	instances = []

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		self.synchronize()

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Reference generator')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateReferenceFrame (w)

	def populateReferenceFrame (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 100)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)
		master.grid_columnconfigure (2, weight = 0, minsize =  30)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Amplitude', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wRefAmpl = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = 'mV', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Frequency', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wRefFreq = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = 'Hz', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Phase', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wRefPhase = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = '°', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]
			self.wRefAmpl ['text'] = first.wRefAmpl ['text']
			self.wRefFreq ['text'] = first.wRefFreq ['text']
			self.wRefPhase['text'] = first.wRefPhase['text']

		self.instances.append (self)

	def _set (self, ampl, freq, phase):
		self.wRefAmpl.config  (text = str ('%.1f' % (ampl * V_to_mV)))
		self.wRefFreq.config  (text = str ('%.2f' % freq))
		self.wRefPhase.config (text = str ('%+06.1f' % (phase * rad_to_deg)))

	def set (self, ampl, freq, phase):
		for instance in self.instances:
			instance._set (ampl, freq, phase)

	def _blank_parameters (self):
		self.wRefAmpl.config  (text = '...')
		self.wRefFreq.config  (text = '...')
		self.wRefPhase.config (text = '...')

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_MeasurementSettings:

	preAmpCouplingMenuItems = {
		PREAMP_COUPLING_DC : 'DC',
		PREAMP_COUPLING_AC : 'AC'
	}

	preAmpGainMenuItems = {
		PREAMP_GAIN_1   : '1',
		PREAMP_GAIN_10  : '10',
		PREAMP_GAIN_100 : '100'
	}

	postAmpGainMenuItems = {
		POSTAMP_GAIN_1   : '1',
		POSTAMP_GAIN_10  : '10',
		POSTAMP_GAIN_100 : '100'
	}

	intgtrTimeConstMenuItems = {
		INTGTR_TC_2ms  : '2 ms',
		INTGTR_TC_5ms  : '5 ms',
		INTGTR_TC_1sec : '1 sec'
	}

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		master.title ('Measurement settings')

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		self.populateMenu (master)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Measurement')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateMeasurementFrame (w)

	def populateMenu (self, master):

		### Main Menu
		self.mainmenu = Menu (master)
		self.mainmenu.config (borderwidth = 1)
		master.config (menu = self.mainmenu)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (
			label = 'Apply', command = self.wApplyCB)

		self.filemenu.add_command (
			label = 'Cancel', command = self.wCancelCB)

	def populateMeasurementFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 120)
		master.grid_columnconfigure (1, weight = 1, minsize =  50)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Input coupling', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		var = self.preAmpCoupling = StringVar()
		options = self.preAmpCouplingMenuItems.values()
		w = self.wPreAmpCoupling = OptionMenu (
			master, var, *options, command = self.wCB)

		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Pre-amp gain', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		var = self.preAmpGain = StringVar()
		options = self.preAmpGainMenuItems.values()
		w = self.wPreAmpGain = OptionMenu (
			master, var, *options, command = self.wCB)

		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Post-amp gain', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		var = self.postAmpGain = StringVar()
		options = self.postAmpGainMenuItems.values()
		w = self.wPostAmpGain = OptionMenu (
			master, var, *options, command = self.wCB)

		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Time Constant', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		var = self.intgtrTC = StringVar()
		options = self.intgtrTimeConstMenuItems.values()
		w = self.wIntgtrTimeConst = OptionMenu (
			master, var, *options, command = self.wCB)

		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def get (self):

		inputChannel = self._inputChannel

		menu = {v : k for (k, v) in self.preAmpCouplingMenuItems.items()}
		preAmpCoupling = menu.get (self.preAmpCoupling.get())

		menu = {v : k for (k, v) in self.preAmpGainMenuItems.items()}
		preAmpGain = menu.get (self.preAmpGain.get())

		menu = {v : k for (k, v) in self.postAmpGainMenuItems.items()}
		postAmpGain = menu.get (self.postAmpGain.get())

		menu = {v : k for (k, v) in self.intgtrTimeConstMenuItems.items()}
		intgtrTC = menu.get (self.intgtrTC.get())

		return (
			inputChannel, preAmpCoupling,
			preAmpGain, postAmpGain, intgtrTC)

	def original (self):
		return (
			self._inputChannel, self._preAmpCoupling,
			self._preAmpGain, self._postAmpGain, self._intgtrTC)

	def wCB (self, *args):
		self.do_callback (MEASUREMENT_SETTINGS, *self.get())

	def wApplyCB (self, *args):
		self.do_callback (APPLY)

	def wCancelCB (self, *args):
		self.do_callback (CANCEL, *self.original())

	def set (
		self, inputChannel, preAmpCoupling,
		preAmpGain, postAmpGain, intgtrTC):

		'''
			Saves the supplied values
			in case the dialog is cancelled
		'''
		self._inputChannel   = inputChannel
		self._preAmpCoupling = preAmpCoupling
		self._preAmpGain     = preAmpGain
		self._postAmpGain    = postAmpGain
		self._intgtrTC       = intgtrTC

		menu = self.preAmpCouplingMenuItems
		self.preAmpCoupling.set (menu.get (preAmpCoupling))

		menu = self.preAmpGainMenuItems
		self.preAmpGain.set (menu.get (preAmpGain))

		menu = self.postAmpGainMenuItems
		self.postAmpGain.set (menu.get (postAmpGain))

		menu = self.intgtrTimeConstMenuItems
		self.intgtrTC.set (menu.get (intgtrTC))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_MeasurementSettingsDisplay:

	instances = []

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		self.synchronize()

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Measurement')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateMeasurementFrame (w)

	def populateMeasurementFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 120)
		master.grid_columnconfigure (1, weight = 1, minsize =  50)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Input coupling', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wPreAmpCoupling = Label (master, anchor = E,)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Pre-amp gain', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wPreAmpGain = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Post-amp gain', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wPostAmpGain = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Time Constant', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wIntgtrTimeConst = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]
			self.wPreAmpCoupling  ['text'] = first.wPreAmpCoupling  ['text']
			self.wPreAmpGain      ['text'] = first.wPreAmpGain      ['text']
			self.wPostAmpGain     ['text'] = first.wPostAmpGain     ['text']
			self.wIntgtrTimeConst ['text'] = first.wIntgtrTimeConst ['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setInputChannel (self, chn) : pass

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setPreAmpCoupling (self, coupling):

		options = {
			PREAMP_COUPLING_DC : 'DC',
			PREAMP_COUPLING_AC : 'AC'
		}

		self.wPreAmpCoupling.config (text = options.get (coupling))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setPreAmpGain (self, gain):

		options = {
			PREAMP_GAIN_1   : '1',
			PREAMP_GAIN_10  : '10',
			PREAMP_GAIN_100 : '100'
		}

		self.wPreAmpGain.config (text = options.get (gain))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setPostAmpGain (self, gain):

		options = {
			POSTAMP_GAIN_1   : '1',
			POSTAMP_GAIN_10  : '10',
			POSTAMP_GAIN_100 : '100'
		}

		self.wPostAmpGain.config (text = options.get (gain))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setIntgtrTC (self, tc):

		options = {
			INTGTR_TC_2ms  : '2 ms',
			INTGTR_TC_5ms  : '5 ms',
			INTGTR_TC_1sec : '1 sec'
		}

		self.wIntgtrTimeConst.config (text = options.get (tc))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def _set (
		self, inputChannel, preAmpCoupling,
		preAmpGain, postAmpGain, intgtrTC):

		functions = [
			(self._setInputChannel   , inputChannel   ),
			(self._setPreAmpCoupling , preAmpCoupling ),
			(self._setPreAmpGain     , preAmpGain     ),
			(self._setPostAmpGain    , postAmpGain    ),
			(self._setIntgtrTC       , intgtrTC       )
		]

		for (fn, arg) in functions:
			if arg != None : fn (arg)

	def set (
		self, inputChannel, preAmpCoupling,
		preAmpGain, postAmpGain, intgtrTC):

		for instance in self.instances:
			instance._set (
				inputChannel, preAmpCoupling,
				preAmpGain, postAmpGain, intgtrTC)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):
		self.wPreAmpCoupling.config  (text = '...')
		self.wPreAmpGain.config      (text = '...')
		self.wPostAmpGain.config     (text = '...')
		self.wIntgtrTimeConst.config (text = '...')

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_OutputDisplay:

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)

	def updateParamFont (self, widget, mul = 2, weight = 'bold'):
		font = Font (widget, widget['font'])
		font.config (size = mul * font['size'], weight = weight)
		widget.config (font = font)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Output')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

		self.populateOutputFrame (w)

	def populateOutputFrame (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 30)
		master.grid_columnconfigure (1, weight = 1, minsize = 130)
		master.grid_columnconfigure (2, weight = 0, minsize = 40)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'A', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		col += 1
		w = self.wAmplValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		col += 1
		w = self.wAmplUnit = Label (master, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'φ', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		col += 1
		w = self.wPhaseValue = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		col += 1
		w = Label (master, text = '°', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = '0°', anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		col += 1
		w = self.wInPhaseValue = Label (master, anchor = E)
		#w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		col += 1
		w = self.wInPhaseUnit = Label (master, anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = '90°', anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		col += 1
		w = self.wQuadratureValue = Label (master, anchor = E)
		#w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

		col += 1
		w = self.wQuadratureUnit = Label (master, anchor = W)
		#w.grid (row = row, column = col, sticky = NSEW)
		self.updateParamFont (w)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def setAmplitude (self, ampl, preAmpGain, postAmpGain):

		fmts = [
			[
				('%07.4f',  'V',     1.0), #  10V
				('%07.5f',  'V',     1.0), #   1V
				('%07.3f', 'mV', V_to_mV)  # 100mV
			],
			[
				('%07.5f',  'V',     1.0), #   1V
				('%07.3f', 'mV', V_to_mV), # 100mV
				('%07.4f', 'mV', V_to_mV)  #  10mV
			],
			[
				('%07.3f', 'mV', V_to_mV), # 100mV
				('%07.4f', 'mV', V_to_mV), #  10mV
				('%07.5f', 'mV', V_to_mV)  #   1mV
			]
		]

		(fmt, unit, mult) = fmts[preAmpGain][postAmpGain]
		self.wAmplValue.config (text = str (fmt % (ampl * mult)))
		self.wAmplUnit.config (text = unit)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def setPhase (self, phase):
		self.wPhaseValue.config (
			text = str ('%+06.1f' % (phase * rad_to_deg)))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def setInPhaseComponent (self, inphase, preAmpGain, postAmpGain):

		fmts = [
			[
				('%+08.4f',  'V',     1.0), #  10V
				('%+08.5f',  'V',     1.0), #   1V
				('%+08.3f', 'mV', V_to_mV)  # 100mV
			],
			[
				('%+08.5f',  'V',     1.0), #   1V
				('%+08.3f', 'mV', V_to_mV), # 100mV
				('%+08.4f', 'mV', V_to_mV)  #  10mV
			],
			[
				('%+08.3f', 'mV', V_to_mV), # 100mV
				('%+08.4f', 'mV', V_to_mV), #  10mV
				('%+08.5f', 'mV', V_to_mV)  #   1mV
			]
		]

		(fmt, unit, mult) = fmts[preAmpGain][postAmpGain]
		self.wInPhaseValue.config (text = str (fmt % (inphase * mult)))
		self.wInPhaseUnit.config (text = unit)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def setQuadratureComponent (
		self, quadrature, preAmpGain, postAmpGain):

		fmts = [
			[
				('%+08.4f',  'V',     1.0), #  10V
				('%+08.5f',  'V',     1.0), #   1V
				('%+08.3f', 'mV', V_to_mV)  # 100mV
			],
			[
				('%+08.5f',  'V',     1.0), #   1V
				('%+08.3f', 'mV', V_to_mV), # 100mV
				('%+08.4f', 'mV', V_to_mV)  #  10mV
			],
			[
				('%+08.3f', 'mV', V_to_mV), # 100mV
				('%+08.4f', 'mV', V_to_mV), #  10mV
				('%+08.5f', 'mV', V_to_mV)  #   1mV
			]
		]

		(fmt, unit, mult) = fmts[preAmpGain][postAmpGain]
		self.wQuadratureValue.config (text = str (fmt % (quadrature * mult)))
		self.wQuadratureUnit.config (text = unit)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def set (
		self, amplitude, phase,
		inphase, quadrature, preAmpGain, postAmpGain):

		self.setAmplitude           (amplitude, preAmpGain, postAmpGain)
		self.setPhase               (phase)
		self.setInPhaseComponent    (inphase, preAmpGain, postAmpGain)
		self.setQuadratureComponent (quadrature, preAmpGain, postAmpGain)

	def blank_parameters (self):
		self.wAmplValue.config       (text = '...')
		self.wAmplUnit.config        (text = '.'  )
		self.wPhaseValue.config      (text = '...')
		self.wInPhaseValue.config    (text = '...')
		self.wInPhaseUnit.config     (text = '.'  )
		self.wQuadratureValue.config (text = '...')
		self.wQuadratureUnit.config  (text = '.'  )

	# ++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_AcquisitionSettings:

	driveModes = {
		DRIVE_MODE_CS : 'Current',
		DRIVE_MODE_VS : 'Voltage'
	}

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		master.title ('Acquisition settings')

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

		master.grid_columnconfigure (0, weight = 1, minsize = 200)
		master.grid_columnconfigure (1, weight = 1, minsize = 150)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Drive mode', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		var = self.driveMode = StringVar()
		options = self.driveModes.values()
		w = OptionMenu (master, var, *options, command = self.wDriveModeCB)
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Frame (master)
		self.wDriveVoltageFrame = (w, row, col)
		self.populateDriveVoltageFrame (w)

		w = Frame (master)
		self.wDriveCurrentFrame = (w, row, col)
		self.populateDriveCurrentFrame (w)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Delay (sec)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wDelay = XFloatEntry (master)
		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Filter length', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wFilterLength = XIntegerEntry (master)
		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

	def populateDriveCurrentFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 200)
		master.grid_columnconfigure (1, weight = 1, minsize = 150)

		row = 0; col = 0
		w = Label (master, text = 'Drive current (mA)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wDriveCurrent = XFloatEntry (master)
		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

	def populateDriveVoltageFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 200)
		master.grid_columnconfigure (1, weight = 1, minsize = 150)

		row = 0; col = 0
		w = Label (master, text = 'Drive voltage (mV)', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wDriveVoltage = XFloatEntry (master)
		w.enable_color (enable = False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

	def getDriveMode (self):
		driveModes = {v : k for (k, v) in self.driveModes.items()}
		return driveModes.get (self.driveMode.get())

	def wDriveModeCB (self, *args):
		self.setDriveMode (self.getDriveMode())

	def setDriveMode (self, mode):

		self.driveMode.set (self.driveModes.get (mode))

		for (w, row, col) in (
			self.wDriveCurrentFrame, self.wDriveVoltageFrame):
			w.grid_forget()

		(w, row, col) = {
			DRIVE_MODE_CS : self.wDriveCurrentFrame,
			DRIVE_MODE_VS : self.wDriveVoltageFrame}.get (mode)

		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

	def set (
		self, delay, filterLength, driveMode,
		driveCurrentSetPoint, driveVoltageSetPoint):

		self.wDelay.set (delay)
		self.wFilterLength.set (filterLength)
		self.setDriveMode (driveMode)
		self.wDriveCurrent.set (driveCurrentSetPoint * A_to_mA)
		self.wDriveVoltage.set (driveVoltageSetPoint * V_to_mV)

	def wApplyCB (self):
		self.do_callback (APPLY,
			self.wDelay.get(), self.wFilterLength.get(), self.getDriveMode(),
			self.wDriveCurrent.get() * mA_to_A,
			self.wDriveVoltage.get() * mV_to_V)

	def wCancelCB (self):
		self.do_callback (CANCEL)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_AcquisitionSettingsDisplay:

	instances = []

	driveModes = {
		DRIVE_MODE_CS : 'Current',
		DRIVE_MODE_VS : 'Voltage'
	}

	def __init__ (self, master):
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

		master.grid_columnconfigure (0, weight = 1, minsize = 120)
		master.grid_columnconfigure (1, weight = 1, minsize =  80)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Drive mode', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wDriveMode = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Drive amplitude', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wDriveAmplitude = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Delay', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wDelay = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Filter Length', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wFilterLength = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:
			first = self.instances[0]
			self.wDelay          ['text'] = first.wDelay          ['text']
			self.wFilterLength   ['text'] = first.wFilterLength   ['text']
			self.wDriveMode      ['text'] = first.wDriveMode      ['text']
			self.wDriveAmplitude ['text'] = first.wDriveAmplitude ['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++

	def _set (
		self, delay, filterLength, driveMode,
		driveCurrentSetPoint, driveVoltageSetPoint):

		self.wDelay        ['text'] = str (delay) + ' ' + 'sec'
		self.wFilterLength ['text'] = str (filterLength)
		self.wDriveMode    ['text'] = self.driveModes.get (driveMode)

		(driveAmplitude, unit) = {
			DRIVE_MODE_CS : (driveCurrentSetPoint * A_to_mA, 'mA'),
			DRIVE_MODE_VS : (driveVoltageSetPoint * V_to_mV, 'mV')
		}.get (driveMode)

		self.wDriveAmplitude ['text'] = str (driveAmplitude) + ' ' + unit

	def set (
		self, delay, filterLength, driveMode,
		driveCurrentSetPoint, driveVoltageSetPoint):

		for instance in self.instances:
			instance._set (
				delay, filterLength, driveMode,
				driveCurrentSetPoint, driveVoltageSetPoint)

	# ++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):
		self.wDelay          ['text'] = '...'
		self.wFilterLength   ['text'] = '...'
		self.wDriveMode      ['text'] = '...'
		self.wDriveAmplitude ['text'] = '...'

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_VFRampSettings:

	frequencySteppingModes = {
		VF_FREQ_STEP_MODE_LINEAR : 'Linear',
		VF_FREQ_STEP_MODE_LOG    : 'Logarithmic'
	}

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		master.title ('V-F ramp settings')

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self, master):

		self.populateMenu (master)

		master.grid_columnconfigure (0, weight = 1)

		w = LabelFrame (master, text = 'Ramp settings')
		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		self.populateRampSettingsFrame (w)

	def populateRampSettingsFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 120)
		master.grid_columnconfigure (1, weight = 1, minsize = 120)
		master.grid_columnconfigure (2, weight = 1, minsize = 130)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Initial frequency', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wInitialFrequency = XFloatEntry (master, justify = LEFT)
		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = Label (master, text = 'Hz', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Final frequency', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalFrequency = XFloatEntry (master, justify = LEFT)
		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = Label (master, text = 'Hz', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Frame (master)
		self.populateLinearFrequencyStepFrame (w)
		self.wLinearFrequencyStepFrame = (w, row, col, 3)

		w = Frame (master)
		self.populateLogFrequencyStepFrame (w)
		self.wLogFrequencyStepFrame = (w, row, col, 3)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Stepping mode', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		var = self.frequencySteppingMode = StringVar()
		options = self.frequencySteppingModes.values()
		w = OptionMenu (master, var, *options,
				command = self.wFrequencySteppingModeCB)
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

	def populateLinearFrequencyStepFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 120)
		master.grid_columnconfigure (1, weight = 1, minsize = 120)
		master.grid_columnconfigure (2, weight = 1, minsize = 130)

		row = 0; col = 0
		w = Label (master, text = 'Frequency step', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wLinearFrequencyStep = XFloatEntry (master, justify = LEFT)
		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = Label (master, text = 'Hz', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

	def populateLogFrequencyStepFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 120)
		master.grid_columnconfigure (1, weight = 1, minsize = 120)
		master.grid_columnconfigure (2, weight = 1, minsize = 130)

		row = 0; col = 0
		w = Label (master, text = 'Frequency step', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wLogFrequencyStep = XIntegerEntry (master, justify = LEFT)
		w.enable_color (False)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = Label (master, text = 'points per decade', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

	def populateMenu (self, master):

		### Main Menu
		self.mainmenu = Menu (master)
		self.mainmenu.config (borderwidth = 1)
		master.config (menu = self.mainmenu)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (
			label = 'Apply', command = self.wApplyCB)

		self.filemenu.add_command (
			label = 'Cancel', command = self.wCancelCB)

	def wFrequencySteppingModeCB (self, *args):
		self.setFrequencySteppingMode (self.getFrequencySteppingMode())

	def getFrequencySteppingMode (self):

		steppingModes = {
			v : k for (k, v) in self.frequencySteppingModes.items()}

		return steppingModes.get (self.frequencySteppingMode.get())

	def setFrequencySteppingMode (self, mode):

		self.frequencySteppingMode.set (self.frequencySteppingModes.get (mode))

		for (w, row, col, columnspan) in (
			self.wLinearFrequencyStepFrame, self.wLogFrequencyStepFrame):
			w.grid_forget()

		if mode == VF_FREQ_STEP_MODE_LINEAR:
			(w, row, col, columnspan) = self.wLinearFrequencyStepFrame
			w.grid (row = row, column = col,
				columnspan = columnspan, sticky = NSEW)

		elif mode == VF_FREQ_STEP_MODE_LOG:
			(w, row, col, columnspan) = self.wLogFrequencyStepFrame
			w.grid (row = row, column = col,
				columnspan = columnspan, sticky = NSEW)

		else: raise ValueError (mode)

	def set (
		self, initialFrequency, finalFrequency,
		linearFreqStep, logFreqStep, steppingMode):

		self.wInitialFrequency.set (initialFrequency)
		self.wFinalFrequency.set (finalFrequency)
		self.wLinearFrequencyStep.set (linearFreqStep)
		self.wLogFrequencyStep.set (int (round (1.0 / log10 (logFreqStep))))
		self.setFrequencySteppingMode (steppingMode)

	def wApplyCB (self, *args):
		self.do_callback (
			APPLY,
			self.wInitialFrequency.get(),
			self.wFinalFrequency.get(),
			self.wLinearFrequencyStep.get(),
			10 ** (1.0 / self.wLogFrequencyStep.get()),
			self.getFrequencySteppingMode())

	def wCancelCB (self, *args):
		self.do_callback (CANCEL)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_VFRampSettingsDisplay:

	instances = []

	def __init__ (self, master):
		self.master = master
		self.createWidgets (master)
		self.synchronize()

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = LabelFrame (master, text = 'V-F ramp settings')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateVFRampSettingsFrame (w)

	def populateVFRampSettingsFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 120)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'Initial frequency', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wInitialFrequency = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Final frequency', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wFinalFrequency = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Frequency step', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wFrequencyStep = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++
		# ++++++++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Stepping mode', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++++++++++++++++++++++++++++++++++

		col += 1
		w = self.wFrequencySteppingMode = Label (master, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

	# ++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++

	def synchronize (self):

		if len (self.instances) == 0:
			self._blank_parameters()

		else:

			first = self.instances[0]

			widgets = [
				(self.wInitialFrequency,      first.wInitialFrequency     ),
				(self.wFinalFrequency,        first.wFinalFrequency       ),
				(self.wFrequencyStep,         first.wFrequencyStep        ),
				(self.wFrequencySteppingMode, first.wFrequencySteppingMode)
			]

			for (dst, src) in widgets : dst['text'] = src['text']

		self.instances.append (self)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _set (self, initialFrequency, finalFrequency,
		linearFreqStep, logFreqStep, frequencySteppingMode):

		text = str ('%.1f' % initialFrequency) + ' Hz'
		self.wInitialFrequency['text'] = text

		text = str ('%.1f' % finalFrequency) + ' Hz'
		self.wFinalFrequency['text'] = text

		if frequencySteppingMode == VF_FREQ_STEP_MODE_LINEAR:

			text = str ('%.1f' % linearFreqStep) + ' Hz'
			self.wFrequencyStep         ['text'] = text
			self.wFrequencySteppingMode ['text'] = 'Linear'

		elif frequencySteppingMode == VF_FREQ_STEP_MODE_LOG:

			points_per_decade = int (round (1.0 / log10 (logFreqStep)))
			text = str (points_per_decade) + ' points per decade'
			self.wFrequencyStep         ['text'] = text
			self.wFrequencySteppingMode ['text'] = 'Logarithmic'

		else: raise ValueError (frequencySteppingMode)

	def set (self, initialFrequency, finalFrequency,
		linearFreqStep, logFreqStep, frequencySteppingMode):

		for instance in self.instances:
			instance._set (initialFrequency, finalFrequency,
				linearFreqStep, logFreqStep, frequencySteppingMode)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _blank_parameters (self):
		self.wInitialFrequency      ['text'] = '...'
		self.wFinalFrequency        ['text'] = '...'
		self.wFrequencyStep         ['text'] = '...'
		self.wFrequencySteppingMode ['text'] = '...'

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

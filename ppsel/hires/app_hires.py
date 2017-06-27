# coding: utf-8
from Tkinter import *
from tkValidatingEntry import *
import tkFont
from tkFileDialog import askopenfile, asksaveasfile
import os

from XWidget import XFloatEntry, XIntegerEntry, XScroll, XTab
from time import time as systime, localtime
import Plot2D

from HIRES_Constants import *
import Preferences

from app_tcon \
	import GUI_IsothermalSettingsDisplay \
	as TCONGui_IsothermalSettingsDisplay

from app_tcon \
	import GUI_RampSettingsDisplay \
	as TCONGui_RampSettingsDisplay

from app_tcon \
	import GUI_SteppedRampDisplay \
	as TCONGui_SteppedRampDisplay

from app_xhires \
	import GUI_AcquisitionSettingsDisplay \
	as XHIRESGui_AcquisitionSettingsDisplay

from app_xhires \
	import GUI_IVRampSettingsDisplay \
	as XHIRESGui_IVRampSettingsDisplay

from app_xhires \
	import GUI_OhmmeterSettingsDisplay \
	as XHIRESGui_OhmmeterSettingsDisplay

from TCON_Banner    import banner as TCON_banner
from XHIRES_Banner    import banner as XHIRES_banner

class GUI:

	runModeMenuItems = {
		RUN_MODE_RT_LINEAR_RAMP : 'R-T (linear ramp)',
		RUN_MODE_RT_STEP_RAMP   : 'R-T (stepped ramp)',
		RUN_MODE_IV_STEP_RAMP   : 'I-V (stepped ramp)',
	}

	methodFileTypes = [
		('XPLORE method files' , '*.xmt'),
		('All files'           , '*.*')
	]

	def __init__ (self, master, sample):
		self.master = master
		self.sample = sample
		self.master.title ('Electrical DC high resistivity (I-V & R-T)')
		self.createWidgets (master)
		self.setRunMode (RUN_MODE_RT_LINEAR_RAMP)
		self.putBanner()

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def close (self):
		for (w, r, c) in (self.wTconIsothermalSettingsDisplay,
						  self.wTconRampSettingsDisplay,
						  self.wTconSteppedRampDisplay,
						  self.wXhiresAcquisitionSettingsDisplay,
						  self.wXhiresIVRampSettingsDisplay,
						  self.wXhiresOhmmeterSettingsDisplay):
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

		self.filemenu.add_command (
			label = 'Open method', command = self.wOpenMethodCB)

		self.filemenu.add_command (
			label = 'Save method', command = self.wSaveMethodCB)

		self.filemenu.add_command (
			label = 'Hide', command = self.wHideCB)

	def populateDisplayPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)

		# ++++ Instrument control ++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Instrument control')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateInstrumentControlFrame (w)

		# ++++ Run control ++++

		row += 1; col = 0
		w = LabelFrame (master, text = 'Run control')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateControlFrame (w)

		## ++++ Acquisition settings display ++++

		row += 1; col = 0
		self.wXhiresAcquisitionSettingsDisplay = (
			XHIRESGui_AcquisitionSettingsDisplay (master = Frame (master)),
			row, col)
		w = self.wXhiresAcquisitionSettingsDisplay[0]
		w.master.grid (row = row, column = col, sticky = NSEW)

		## ++++ TCON run type specific settings display ++++

		row += 1; col = 0
		self.wTconIsothermalSettingsDisplay = (
			TCONGui_IsothermalSettingsDisplay (master = Frame (master)),
			row, col)

		self.wTconRampSettingsDisplay = (
			TCONGui_RampSettingsDisplay (master = Frame (master)),
			row, col)

		self.wTconSteppedRampDisplay = (
			TCONGui_SteppedRampDisplay (master = Frame (master)),
			row, col)

		## ++++ XHIRES run type specific settings display ++++

		row += 1; col = 0
		self.wXhiresIVRampSettingsDisplay = (
			XHIRESGui_IVRampSettingsDisplay (master = Frame (master)),
			row, col)

		self.wXhiresOhmmeterSettingsDisplay = (
			XHIRESGui_OhmmeterSettingsDisplay (master = Frame (master)),
			row, col)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateInstrumentControlFrame (self, master):
		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = self.wTCON = Button (
			master, text = 'Temperature controller', command = self.wTconCB)

		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = self.wXHIRES = Button (
			master, text = 'High resistance meter',
			command = self.wXhiresCB)

		w.grid (row = row, column = col, sticky = NSEW)

	def populateControlFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

		row = 0; col = 0
		wFrame = Frame (master)
		wFrame.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

		wFrame.grid_columnconfigure (0, weight = 1)
		wFrame.grid_columnconfigure (1, weight = 1)

		w = Label (wFrame, text = "Run mode", width = 10, anchor = W)
		w.grid (row = 0, column = 0, sticky = NSEW)

		var = self.runMode = StringVar()
		options = self.runModeMenuItems.values()
		w = self.wRunMode = OptionMenu (
			wFrame, var, *options, command = self.wRunModeCB)

		w.config (width = 20, anchor = W)
		w.grid (row = 0, column = 1, sticky = NSEW)

		row += 1; col = 0
		w = self.wStart = Button (
			master, text = 'Start', command = self.wStartCB)

		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wFinish = Button (
			master, text = 'Finish', state = DISABLED,
			command = self.wFinishCB)

		w.grid (row = row, column = col, sticky = NSEW)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateStatusPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_rowconfigure    (0, weight = 1)

		row = 0; col = 0
		w = self.wStatus = Label (master, text = '...', anchor = W, width = 10)
		w.grid (row = row, column = col, sticky = NSEW)

	def updateParamFont (self, widget, mul = 2, weight = 'bold'):
		font = tkFont.Font (widget, widget['font'])
		font.config (size = mul * font['size'], weight = weight)
		widget.config (font = font)

	def wRunModeCB (self, *args):
		self.do_callback (RUN_MODE, self.getRunMode())

	def set_status (self, text):

		lt = localtime (systime())
		time_stamp = (
			str ('%02d' % lt.tm_hour) + ':' +
			str ('%02d' % lt.tm_min)  + ':' +
			str ('%02d' % lt.tm_sec))

		text = '<' + time_stamp + ':RES> ' + text
		print text

		old_text = self.wStatus['text']
		new_text = text + '    .    ' + old_text
		new_text = new_text[:1024]
		self.wStatus['text'] = new_text

	def getRunMode (self):
		modes = {v : k for (k, v) in self.runModeMenuItems.items()}
		return modes.get (self.runMode.get())

	def setRunMode (self, mode):
		self.runMode.set (self.runModeMenuItems.get (mode))

		widgets = {
			RUN_MODE_RT_LINEAR_RAMP : self.wTconRampSettingsDisplay,
			RUN_MODE_RT_STEP_RAMP   : self.wTconSteppedRampDisplay,
			RUN_MODE_IV_STEP_RAMP   : self.wTconSteppedRampDisplay
		}

		for (w, row, col) in widgets.values():
			w.master.grid_forget()

		(w, row, col) = widgets.get (mode)
		w.master.grid (row = row, column = col, sticky = NSEW)

		widgets = {
			RUN_MODE_RT_LINEAR_RAMP : self.wXhiresOhmmeterSettingsDisplay,
			RUN_MODE_RT_STEP_RAMP   : self.wXhiresOhmmeterSettingsDisplay,
			RUN_MODE_IV_STEP_RAMP   : self.wXhiresIVRampSettingsDisplay
		}

		for (w, row, col) in widgets.values():
			w.master.grid_forget()

		(w, row, col) = widgets.get (mode)
		w.master.grid (row = row, column = col, sticky = NSEW)

	def setRunControlStatus (self, status):

		if status == RUN_STARTING:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config  (text = 'Starting', state = DISABLED)
			self.wFinish.config (text = 'Finish',   state = DISABLED)

		elif status == RUN_STARTED:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config  (text = 'Start',  state = DISABLED)
			self.wFinish.config (text = 'Finish', state = NORMAL)

		elif status == RUN_FINISHING:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config  (text = 'Start',     state = DISABLED)
			self.wFinish.config (text = 'Finishing', state = DISABLED)

		elif status == RUN_FINISHED:
			self.wRunMode.config (state = NORMAL)
			self.wStart.config  (text = 'Start',  state = NORMAL)
			self.wFinish.config (text = 'Finish', state = DISABLED)

		else: raise ValueError (status)

	def wStartCB (self, *args):
		self.do_callback (START_RUN, self.getRunMode())

	def wFinishCB (self, *args):
		self.do_callback (FINISH_RUN)

	def wTconCB (self, *args):
		self.do_callback (OPEN_DEVICE, TCON_DEVICE)

	def wXhiresCB (self, *args):
		self.do_callback (OPEN_DEVICE, XHIRES_DEVICE)

	def wHideCB (self, *args):
		self.master.withdraw()

	def addTconMenu (self, menu):
		self.utilmenu.add_cascade (
			label = 'Temperature controller', menu = menu)

	def addXhiresMenu (self, menu):
		self.utilmenu.add_cascade (
			label = 'High resistance meter', menu = menu)

	def putBanner (self):
		w = GUI_Banner (self.wPlots.add ('Welcome'))
		w.grid (row = 0, column = 0, sticky = NSEW)

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
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GUI_Banner (Frame):

	def __init__ (self, master):
		Frame.__init__ (self, master)
		self.createWidgets (self)

	def createWidgets (self, master):
		master.grid_columnconfigure (0, weight = 1)
		master.grid_rowconfigure (0, weight = 1)
		master.grid_rowconfigure (1, weight = 1)

		photo = self.xlia_photo = PhotoImage (data = XHIRES_banner)
		w = Label (master, image = photo)
		w.grid (row = 0, column = 0, sticky = NSEW)

		photo = self.tcon_photo = PhotoImage (data = TCON_banner)
		w = Label (master, image = photo)
		w.grid (row = 1, column = 0, sticky = NSEW)

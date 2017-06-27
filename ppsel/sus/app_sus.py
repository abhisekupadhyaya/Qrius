# coding: utf-8
from Tkinter import *
from tkValidatingEntry import *
from tkFont import Font
from tkFileDialog import askopenfile, asksaveasfile
import os

from XWidget import XFloatEntry, XIntegerEntry, XScroll, XTab, XFrame
from time import time as systime, localtime
import Plot2D

from SUS_Constants import *
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

from app_xlia \
	import GUI_ReferenceSettingsDisplay \
	as XLIAGui_ReferenceSettingsDisplay

from app_xlia \
	import GUI_MeasurementSettingsDisplay \
	as XLIAGui_MeasurementSettingsDisplay

from app_xlia \
	import GUI_AcquisitionSettingsDisplay \
	as XLIAGui_AcquisitionSettingsDisplay

from app_xlia \
	import GUI_VFRampSettingsDisplay \
	as XLIAGui_VFRampSettingsDisplay

from appXMC \
	import GUI_MCStatusDisplay \
	as XMCGui_StatusDisplay

from TCON_Banner    import banner as TCON_banner
from XLIA_Banner    import banner as XLIA_banner

class GUI:

	runModeMenuItems = {
		RUN_MODE_XT_LINEAR_RAMP : u'χ-T (linear ramp)',
		RUN_MODE_XT_STEP_RAMP   : u'χ-T (stepped ramp)',
		RUN_MODE_XF_STEP_RAMP   : u'χ-F (stepped ramp)',
		RUN_MODE_XL             : u'χ-L'
	}

	methodFileTypes = [
		('XPLORE method files' , '*.xmt'),
		('All files'           , '*.*')
	]

	def __init__ (self, master, sample):
		self.master = master
		self.sample = sample
		self.master.title ('Magnetic AC susceptibility (χ-T & χ-F)')
		self.createWidgets (master)
		self.setRunMode (RUN_MODE_XT_LINEAR_RAMP)
		self.putBanner()

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def update_font (self, widget, mul = 1, style = 'bold'):
		font = widget['font']
		(name, sep, font) = font.strip().partition (' ')
		(size, sep, font) = font.strip().partition (' ')
		widget['font'] = name + ' ' + str (mul * int (size)) + ' ' + style

	def close (self):
		for (w, r, c) in (self.wTconIsothermalSettingsDisplay,
						  self.wTconRampSettingsDisplay,
						  self.wTconSteppedRampDisplay,
						  self.wXliaAcquisitionSettingsDisplay,
						  self.wXliaMeasurementSettingsDisplay,
						  self.wXliaReferenceSettingsDisplay,
						  self.wXliaVFRampSettingsDisplay,
						  self.wXmcStatusDisplay):
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

		self.settingsmenu = Menu (self.mainmenu)
		self.settingsmenu.config (tearoff = 0)
		self.settingsmenu.add_command (
						label = 'χL acquisition setting',
						command = self.wXL_AcqSettingCB)

		self.utilmenu = Menu (self.mainmenu)
		self.utilmenu.config (tearoff = 0)

		self.mainmenu.add_cascade (
			label = 'Settings', menu = self.settingsmenu, underline = 0)

		self.mainmenu.add_cascade (
			label = 'Tools', menu = self.utilmenu, underline = 0)

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

		## ++++ XMC status display ++++

		row += 1; col = 0
		w = self.wXmcFrame = XFrame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populate_XMC_Display (w)

		## ++++ TCON settings display ++++

		row += 1; col = 0
		w = self.wXtconFrame = XFrame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populate_TCON_Display (w)

		## ++++ XLIA settings display ++++

		row += 1; col = 0
		w = self.wXliaFrame = XFrame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populate_XLIA_Display (w)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateProbePositionFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = self.wProbePosition = Label (master, text = '...')
		w.grid (row = row, column = col, sticky = NSEW)
		self.update_font (w, mul = 5, style = 'bold')

		#row += 1
		#w = self.wProceed = Button (
		#	master, text = 'Proceed',
		#	command = self.wProceedCB, state = DISABLED)
		#w.grid (row = row, column = col, sticky = NSEW)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populate_XLIA_Display (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		(w, r, c) = self.wXliaReferenceSettingsDisplay = (
			XLIAGui_ReferenceSettingsDisplay (master = Frame (master)),
			row, col)
		w.master.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		(w, r, c) = self.wXliaMeasurementSettingsDisplay = (
			XLIAGui_MeasurementSettingsDisplay (master = Frame (master)),
			row, col)
		w.master.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		(w, r, c) = self.wXliaAcquisitionSettingsDisplay = (
			XLIAGui_AcquisitionSettingsDisplay (master = Frame (master)),
			row, col)
		w.master.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		(w, r, c) = self.wXliaVFRampSettingsDisplay = (
			XLIAGui_VFRampSettingsDisplay (master = Frame (master)),
			row, col)

	def populate_TCON_Display (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		(w, r, c) = self.wTconIsothermalSettingsDisplay = (
			TCONGui_IsothermalSettingsDisplay (master = Frame (master)),
			row, col)

		(w, r, c) = self.wTconRampSettingsDisplay = (
			TCONGui_RampSettingsDisplay (master = Frame (master)),
			row, col)

		(w, r, c) = self.wTconSteppedRampDisplay = (
			TCONGui_SteppedRampDisplay (master = Frame (master)),
			row, col)

	def populate_XMC_Display (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		(w, r, c) = self.wXmcStatusDisplay = (
			XMCGui_StatusDisplay (master = Frame(master)),
			row, col)

	def populateInstrumentControlFrame (self, master):
		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = self.wTCON = Button (
			master, text = 'Temperature controller', command = self.wTconCB)

		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = self.wXLIA = Button (
			master, text = 'Lock-in amplifier',
			command = self.wXliaCB)

		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = self.wXMC = Button (
			master, text = 'Sample positioner',
			command = self.wXmcCB)

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

	def wRunModeCB (self, *args):
		self.do_callback (RUN_MODE, self.getRunMode())

	def set_status (self, text):

		lt = localtime (systime())
		time_stamp = (
			str ('%02d' % lt.tm_hour) + ':' +
			str ('%02d' % lt.tm_min)  + ':' +
			str ('%02d' % lt.tm_sec))

		text = '<' + time_stamp + ':SUS> ' + text
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
			RUN_MODE_XT_LINEAR_RAMP : self.wTconRampSettingsDisplay,
			RUN_MODE_XT_STEP_RAMP   : self.wTconSteppedRampDisplay,
			RUN_MODE_XF_STEP_RAMP   : self.wTconSteppedRampDisplay
		}

		for (w, row, col) in widgets.values():
			w.master.grid_forget()

		w = widgets.get (mode)

		if w != None:
			(w, row, col) = w
			w.master.grid (row = row, column = col, sticky = NSEW)

		widgets = {
			RUN_MODE_XF_STEP_RAMP   : self.wXliaVFRampSettingsDisplay
		}

		for (w, row, col) in widgets.values():
			w.master.grid_forget()

		w = widgets.get (mode)

		if w != None:
			(w, row, col) = w
			w.master.grid (row = row, column = col, sticky = NSEW)

		widgets = {
			RUN_MODE_XT_LINEAR_RAMP : self.wXmcStatusDisplay,
			RUN_MODE_XT_STEP_RAMP   : self.wXmcStatusDisplay,
			RUN_MODE_XF_STEP_RAMP   : self.wXmcStatusDisplay,
			RUN_MODE_XL             : self.wXmcStatusDisplay
		}

		for (w, row, col) in widgets.values():
			w.master.grid_forget()

		w = widgets.get (mode)

		if w != None:
			(w, row, col) = w
			w.master.grid (row = row, column = col, sticky = NSEW)

		self.wXliaFrame.update_frame ()
		self.wXtconFrame.update_frame ()
		self.wXmcFrame.update_frame ()

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
			self.wStart.config  (text = 'Start',  state = NORMAL,
								command = self.wStartCB)
			self.wFinish.config (text = 'Finish', state = DISABLED)

		elif status == RUN_PREPARING:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config  (text = 'Prepairing', state = DISABLED)
			self.wFinish.config (text = 'Finish'    , state = NORMAL)

		elif status == RUN_PROCEED:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config  (text = 'Proceed', state = NORMAL,
								command = self.wProceedCB)
			self.wFinish.config (text = 'Finish' , state = NORMAL)

		elif status == RUN_PROCEED_STARTED:
			self.wRunMode.config (state = DISABLED)
			self.wStart.config  (text = 'Proceed', state = DISABLED)
			self.wFinish.config (text = 'Finish' , state = NORMAL)

		else: raise ValueError (status)

	def wStartCB (self, *args):
		self.do_callback (START_RUN, self.getRunMode())

	def wFinishCB (self, *args):
		self.do_callback (FINISH_RUN)

	def wProceedCB (self, *args):
		self.do_callback (PROCEED_RUN)

	def wTconCB (self, *args):
		self.do_callback (OPEN_DEVICE, TCON_DEVICE)

	def wXliaCB (self, *args):
		self.do_callback (OPEN_DEVICE, XLIA_DEVICE)

	def wXmcCB (self, *args):
		self.do_callback (OPEN_DEVICE, XMC_DEVICE)

	def wHideCB (self, *args):
		self.master.withdraw()

	def addTconMenu (self, menu):
		self.settingsmenu.add_cascade (
			label = 'Temperature controller', menu = menu)

	def addXliaMenu (self, menu):
		self.settingsmenu.add_cascade (
			label = 'Lock-in amplifier', menu = menu)

	def addXmcMenu (self, menu):
		self.utilmenu.add_cascade (
			label = 'Sample positioner', menu = menu)

	def wXL_AcqSettingCB (self):
		self.do_callback (OPEN_DIALOG, ACQ_SETTING_DIALOG)

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

	def setProbePosition (self, position):

		text = {
			PROBE_UP   : '↑',
			PROBE_DOWN : '↓'
		}.get (position)

		self.wProbePosition['text'] = text

	def activate_proceed (self):
		self.wProceed.config (state = NORMAL)

	def deactivate_proceed (self):
		self.wProceed.config (state = DISABLED)

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

		photo = self.xlia_photo = PhotoImage (data = XLIA_banner)
		w = Label (master, image = photo)
		w.grid (row = 0, column = 0, sticky = NSEW)

		photo = self.tcon_photo = PhotoImage (data = TCON_banner)
		w = Label (master, image = photo)
		w.grid (row = 1, column = 0, sticky = NSEW)

class GUI_AcqSetting:

	def __init__(self, master, stepSize, maxDepth, probeUp, probeDown):
		self.master = master
		self.master.title ('Acquisition setting')
		self.createWidgets()
		self.set (stepSize, maxDepth, probeUp, probeDown)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self):

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
		self.master.grid_rowconfigure (1, weight = 1)
		self.master.grid_columnconfigure (0, weight = 1)

		w = wFrame = LabelFrame (self.master,
									text = 'χ-L acquisition settings')

		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)

		row = 0; col = 0
		w = Label (wFrame, text = 'Step size (mm) :', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wStepSize = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)
		w.enable_color (enable = False)

		row += 1; col = 0
		w = Label (wFrame, text = 'Max depth (mm) :', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wMaxDepth = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)
		w.enable_color (enable = False)

		w = wFrame = LabelFrame (self.master,
									text = 'χ-T acquisition settings')

		w.grid (row = 1, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)

		row = 0; col = 0
		w = Label (wFrame, text = 'Probe up (mm) :', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wProbeUp = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)
		w.enable_color (enable = False)

		row += 1; col = 0
		w = Label (wFrame, text = 'Probe down (mm) :', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wProbeDown = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)
		w.enable_color (enable = False)

	def wApplyCB (self):
		self.do_callback (APPLY, self.wStepSize.get()  * mm_to_m,
								 self.wMaxDepth.get()  * mm_to_m,
								 self.wProbeUp.get()   * mm_to_m,
								 self.wProbeDown.get() * mm_to_m)

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, stepSize, maxDepth, probeUp, probeDown):
		self.wStepSize.set  (round (stepSize  * m_to_mm, 1))
		self.wMaxDepth.set  (round (maxDepth  * m_to_mm, 1))
		self.wProbeUp.set   (round (probeUp   * m_to_mm, 1))
		self.wProbeDown.set (round (probeDown * m_to_mm, 1))

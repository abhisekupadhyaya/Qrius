# coding: utf-8
from ttk     import Progressbar, Style
from time    import time as systime, localtime

from Tkinter import Frame, LabelFrame, PhotoImage
from Tkinter import Label, Menu, OptionMenu, StringVar, Button
from Tkinter import NORMAL, DISABLED, E, W, NSEW, RIGHT, LEFT

from XWidget       import XFloatEntry, XIntegerEntry, XScroll, XTab
from Preferences   import get_XMC_linacStrokeLength, get_XMC_linacPitch
from XMC_Constants import *
from XMC_Banner    import banner

import Plot2D
import Preferences

class GUI:

	runModeMenuItems = {
		RUN_MODE_MONITOR      : 'Monitor',
	}

	def __init__(self, master, sample):
		self.master = master
		self.sample = sample
		self.master.title ('Sample positioner')

		self.createWidgets (self.master)
		self.blank_parameters()
		self.putBanner()

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def close (self):
		for (w, r, c) in (self.wMCStatusDisplay,):
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
		self.populateStatusFrame (w)

	def populateMenu (self, master):

		### Main Menu
		self.mainmenu = Menu (master)
		self.mainmenu.config (borderwidth = 1)
		master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		#self.settingsmenu = Menu (self.mainmenu)
		#self.settingsmenu.config (tearoff = 0)
		#self.mainmenu.add_cascade (
			#label = 'Settings', menu = self.settingsmenu, underline = 0)

		self.toolsmenu = Menu (self.mainmenu)
		self.toolsmenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'Tools', menu = self.toolsmenu, underline = 0)

		# ++++ Populating file menu ++++

		menu_items = [ \
			('Connect'     , self.wConnectDeviceCB),
			('Hide'        ,    	  self.wHideCB) \
		]

		for (l, c) in menu_items:
			self.filemenu.add_command (label = l, command = c)

		# ++++ Populating settings menu ++++

		#menu_items = [ \
			#('Pitch'     , self.wPitchSettingCB) \
		#]

		#for (l, c) in menu_items:
			#self.settingsmenu.add_command (label = l, command = c)

		# ++++ Populating tools menu ++++

		menu_items = [ \
			('Reset'                 , self.wResetDeviceCB ),
			('Move absolute'         , self.wMoveAbsoluteCB),
			('Move relative'         , self.wMoveRelativeCB),
			('Stop'                  , self.wStopDeviceCB  )  \
		]

		for (l, c) in menu_items:
			self.toolsmenu.add_command (label = l, command = c)

	def populateDisplayPanel (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 230)

		row = 0; col = 0
		w = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.wMCStatusDisplay = (GUI_MCStatusDisplay (w), row, col)

		row += 1
		w = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populateControlFrame (w)

	def populateControlFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Control')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateControlFrameWidgets(w)

	def populateControlFrameWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)

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

	def populateStatusFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)
		#master.grid_rowconfigure    (0, weight = 1)

		row = 0; col = 0
		w = self.wStatus = Label (master, text = '...', anchor = W, width = 10)
		w.grid (row = row, column = col, sticky = NSEW)

	def set_status (self, text):

		lt = localtime (systime())
		time_stamp = (
			str ('%02d' % lt.tm_hour) + ':' +
			str ('%02d' % lt.tm_min)  + ':' +
			str ('%02d' % lt.tm_sec))

		text = '<' + time_stamp + ':XMC> ' + text
		print text

		old_text = self.wStatus['text']
		new_text = text + '    .    ' + old_text
		new_text = new_text[:1024]
		self.wStatus['text'] = new_text

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setConnectionStatus (self, status):

		if status == DEVICE_CONNECTING:
			self.filemenu.entryconfig (
				0, label = 'Connecting', state = DISABLED, command = None)

		elif status == DEVICE_CONNECTED:
			self.filemenu.entryconfig (
				0, label = 'Disconnect', state = NORMAL,
				command = self.wDisconnctDeviceCB)

			self.set_status ('Sample positioner connected')

		elif status == DEVICE_DISCONNECTING:
			self.filemenu.entryconfig (
				0, label = 'Disconnecting', state = DISABLED, command = None)

		elif status == DEVICE_DISCONNECTED:

			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.wMCStatusDisplay[0].blank_parameters()
			self.set_status ('Sample positioner disconnected')

		elif status == DEVICE_NOT_FOUND:
			self.filemenu.entryconfig (
				0, label = 'Connect', state = NORMAL,
				command = self.wConnectDeviceCB)

			self.wMCStatusDisplay[0].blank_parameters()
			self.set_status ('Sample positioner not found')

		else: raise ValueError (status)

	def wHideCB (self):
		self.master.withdraw()

	def wConnectDeviceCB (self):
		self.do_callback (CONNECT_DEVICE)

	def wDisconnctDeviceCB (self):
		self.do_callback (DISCONNECT_DEVICE)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

	def wRunModeCB (self, *args):
		self.do_callback (RUN_MODE, self.getRunMode())

	def getRunMode (self):
		runModes = {v : k for (k, v) in self.runModeMenuItems.items()}
		return runModes.get (self.runMode.get())

	def setRunMode (self, mode):

		self.runMode.set (self.runModeMenuItems.get (mode))

		if mode == RUN_MODE_MONITOR : pass
		else                        : raise ValueError (mode)

	def wPitchSettingCB (self):
		self.do_callback (OPEN_DIALOG, PITCH_SETTING_DIALOG)

	def wResetDeviceCB (self):
		self.do_callback (RESET_DEVICE)

	def wMoveAbsoluteCB (self):
		self.do_callback (OPEN_DIALOG, MOVE_ABSOLUTE_DIALOG)

	def wMoveRelativeCB (self):
		self.do_callback (OPEN_DIALOG, MOVE_RELATIVE_DIALOG)

	def wStopDeviceCB (self):
		self.do_callback (STOP_DEVICE)

	def setMCStatusDisplay (self, state, position, remainingDistance):
		(w, row, col) = self.wMCStatusDisplay
		w.setValues (state, position, remainingDistance)

	def setMCProgressBarDisplay (self, position):
		(w, row, col) = self.wMCStatusDisplay
		w.setBar (position)

	def setStatusJammed (self):
		(w, row, col) = self.wMCStatusDisplay
		w.setStatusJammed()

	def setMCProgressBarMin (self, position):
		(w, row, col) = self.wMCStatusDisplay
		w.setBarMin (position)

	def setMCProgressBarMax (self, position):
		(w, row, col) = self.wMCStatusDisplay
		w.setBarMax (position)

	def blank_parameters (self):
		self.wMCStatusDisplay[0].blank_parameters()

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

class GUI_MoveAbsoluteTool:

	def __init__(self, master, position):
		self.master = master
		self.master.title ('Tools')
		self.createWidgets()
		self.set (position)

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
		self.master.grid_columnconfigure (0, weight = 1)

		w = wFrame = LabelFrame (
				self.master, text = 'Move absolute')

		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)

		w = Label (wFrame, text = 'Position (mm) :', anchor = E)
		w.grid (row = 0, column = 0, sticky = NSEW)

		w = self.wPosition = XFloatEntry ( \
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 0, column = 1, sticky = NSEW)
		w.callback (self.wEnterCB)
		w.enable_color (enable = False)

	def wApplyCB (self):
		self.do_callback (APPLY, self.wPosition.get() * mm_to_m)

	def wEnterCB (self, *args):
		self.do_callback (ENTER, self.wPosition.get() * mm_to_m)

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, position):
		self.wPosition.set (round (position * m_to_mm, 1))

class GUI_MoveRelativeTool:

	def __init__(self, master, distance):
		self.master = master
		self.master.title ('Tools')
		self.createWidgets()
		self.set (distance)

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

		self.master.grid_rowconfigure    (0, weight = 1)
		self.master.grid_columnconfigure (0, weight = 1)

		w = wFrame = LabelFrame (
				self.master, text = 'Move relative')

		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)

		w = Label (wFrame, text = 'Distance (mm) :', anchor = E)
		w.grid (row = 0, column = 0, sticky = NSEW)

		w = self.wDistance = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 0, column = 1, sticky = NSEW)
		w.callback (self.wEnterCB)
		w.enable_color (enable = False)

	def wApplyCB (self):
		self.do_callback (APPLY, self.wDistance.get() * mm_to_m)

	def wEnterCB (self, *args):
		self.do_callback (ENTER, self.wDistance.get() * mm_to_m)

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, distance):
		self.wDistance.set (round (distance * m_to_mm, 1))

class GUI_PitchSetting:

	def __init__(self, master, pitch):
		self.master = master
		self.master.title ('Tools')
		self.createWidgets()
		self.set (pitch)

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
		self.master.grid_columnconfigure (0, weight = 1)

		w = wFrame = LabelFrame (self.master, text = 'Set pitch')

		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)

		w = Label (wFrame, text = 'Pitch (mm) :', anchor = E)
		w.grid (row = 0, column = 0, sticky = NSEW)

		w = self.wPitch = XFloatEntry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT)
		w.grid (row = 0, column = 1, sticky = NSEW)
		w.enable_color (enable = False)

	def wApplyCB (self):
		self.do_callback (APPLY, self.wPitch.get() * mm_to_m)

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, pitch):
		self.wPitch.set (round (pitch * m_to_mm, 2))

class GUI_MCStatusDisplay:

	instances = []

	str_states = {
		MC_STATE_IDLE      : 'IDLE',
		MC_STATE_RESET     : 'RESET',
		MC_STATE_MOVE_UP   : 'UP',
		MC_STATE_MOVE_DOWN : 'DOWN'
	}

	def __init__ (self, master):

		self.master = master
		self.relBarMin = 0
		self.relBarMax = 0
		self.instances.append (self)

		self.createWidgets (master)

		self.setValues (
			state = MC_STATE_IDLE,
			position = 0, remainingDistance = 0)

		self.setBarMin (0.0)
		self.setBarMax (0.0)
		self.setBar (0)

	def close (self):
		self.instances.remove (self)

	def createWidgets (self, master):

		#-Set-progress-bar-style-for-custom-thickness--
		s = Style()
		s.theme_use("default")
		s.configure("TProgressbar", thickness=5)
		#----------------------------------------------

		master.grid_rowconfigure    (0, weight = 1)
		master.grid_columnconfigure (0, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = LabelFrame (master, text = 'Sample positioner status')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateDisplayPanel (w)

	def populateDisplayPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populateStatusFrame (w)

		row += 1
		w = Frame (master)
		w.grid(row = row, column = col, sticky = NSEW)
		self.populatePositionBarFrame (w)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def populateStatusFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_columnconfigure (1, weight = 1)
		master.grid_columnconfigure (2, weight = 1)

		# +++++++++++++++++++++++++++++++

		row = 0; col = 0
		w = Label (master, text = 'State', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		col += 1
		w = self.wState = Label (master, width = 7, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Position', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wPosition = Label (master, width = 6, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = ('%-6s' % 'mm'), width = 6, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++

		row += 1; col = 0
		w = Label (master, text = 'Remaining', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = self.wRemainingDistance = Label (master, width = 6, anchor = E)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = ('%-6s' % 'mm'), width = 6, anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

	def populatePositionBarFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = self.wPosBar = Progressbar (
			master, style="TProgressbar", orient = 'horizontal',
			length = 100, mode = 'indeterminate')

		#w = self.wPosBar = Progressbar (
		#	master, orient = 'horizontal',
		#	length = 100, mode = 'indeterminate')

		w.grid(row = row, column = col, sticky = NSEW)
		w['value'  ] = self.relBarMin
		w['maximum'] = self.relBarMax

		row += 1
		w = self.wRelPosBar = Progressbar (
			master, style="TProgressbar", orient = 'horizontal',
			length = 100, mode = 'indeterminate')

		#w = self.wRelPosBar = Progressbar (
		#	master, orient = 'horizontal',
		#	length = 100, mode = 'indeterminate')

		w.grid(row = row, column = col, sticky = NSEW)
		w['value'  ] = self.relBarMin
		w['maximum'] = self.relBarMax

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setValues (self, state, position, remainingDistance):
		self.wState['text'] = ('%-6s' % self.str_states.get (state))

		self.wPosition['text'] = str (
			'%6.1f' % (position * m_to_mm))

		self.wRemainingDistance['text'] = str (
			'%6.1f' % abs (remainingDistance * m_to_mm))

	def _setStatusJammed (self):
		self.wState['text'] = ('%-6s' % 'JAMMED')

	def _setBar (self, position):
		self.wPosBar   ['value'] = position
		self.wRelPosBar['value'] = (position - self.relBarMin)

	def setValues (self, state, position, remainingDistance):
		for o in self.instances:
			o._setValues (state, position, remainingDistance)

	def setStatusJammed (self):
		for o in self.instances:
			o._setStatusJammed()

	def setBar (self, position):
		for o in self.instances:
			o._setBar (position)

	def setBarMin (self, value):
		for o in self.instances:
			o._setBarMin (value)

	def setBarMax (self, value):
		for o in self.instances:
			o._setBarMax (value)

	def _setBarMin (self, value):
		self.relBarMin = value
		self.wRelPosBar['maximum'] = (self.relBarMax - self.relBarMin)

	def _setBarMax (self, value):
		self.relBarMax = value
		self.wRelPosBar['maximum'] = (self.relBarMax - self.relBarMin)
		self.wPosBar['maximum'] = 100e-3

	def _blank_parameters (self):
		self.wState['text']             = '...'
		self.wPosition['text']          = '...'
		self.wRemainingDistance['text'] = '...'

	def blank_parameters (self):
		for instance in self.instances:
			instance._blank_parameters()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

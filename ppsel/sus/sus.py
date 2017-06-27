# coding: utf-8
import Preferences

# ++++ Importing singleton constructors ++++

from tcon           import TCON
from xlia           import XLIA
from XMC            import XMC

# ++++ Importing datatypes ++++

from SUS_DataType   import DataPoint, DataSet
from XMC_DataType   import DataPoint as XMC_DataPoint
from XLIA_DataType  import DataPoint as XLIA_DataPoint
from TCON_DataType  import DataPoint as TCON_DataPoint

# ++++ Importing constants ++++

from SUS_Constants  import *

from TCON_Constants import RUN_MODE_MONITOR       as TCON_RUN_MODE_MONITOR
from TCON_Constants import RUN_MODE_LINEAR_RAMP   as TCON_RUN_MODE_LINEAR_RAMP
from TCON_Constants import RUN_MODE_STEPPED_RAMP  as TCON_RUN_MODE_STEPPED_RAMP

from Cryostat_Constants import *

from XLIA_Constants import RUN_MODE_VF            as XLIA_RUN_MODE_VF
from XLIA_Constants import RUN_MODE_VTime         as XLIA_RUN_MODE_VTime
from XLIA_Constants import MEASUREMENT_MODE_FULL  as XLIA_MEASUREMENT_MODE_FULL
from XLIA_Constants import MEASUREMENT_MODE_QUICK as XLIA_MEASUREMENT_MODE_QUICK
from XLIA_Constants import VF_FREQ_STEP_MODE_LINEAR
from XLIA_Constants import VF_FREQ_STEP_MODE_LOG

from XMC_Constants  import RUN_MODE_MONITOR       as XMC_RUN_MODE_MONITOR

# ++++ Importing exceptions ++++

from  XMC import LinkError      as XMC_LinkError
from  XMC import CommError      as XMC_CommError
from  XMC import StallError     as XMC_StallError
from  XMC import ResourceError  as XMC_ResourceError

from  tcon import LinkError     as TCON_LinkError
from  tcon import CommError     as TCON_CommError
from  tcon import ResourceError as TCON_ResourceError

from  xlia import LinkError     as XLIA_LinkError
from  xlia import CommError     as XLIA_CommError
from  xlia import ResourceError as XLIA_ResourceError

# ++++ Importing other useful classes ++++

from app_sus        import GUI, GUI_AcqSetting
from SUS_Method     import Method, XMethodError
from XDict          import XDict
from XThread        import XTaskQueue, XThread, XThreadModule, XTerminate

# Importing Python provided libraries

import os
from threading      import Thread, RLock
from time           import time as systime, localtime, sleep
from Tkinter        import NORMAL, DISABLED, Toplevel
from math           import sin, cos, hypot, atan2

class ResourceError (Exception) : pass

class _Applet:

	def __init__ (self, oSus):

		self.oSus = oSus
		self._plots = {}
		self._taskq = XTaskQueue()
		self._lastPlotUpdateAt = 0.0
		self._hApplet = self.oSus.oApp.master.after (50, self._applet)

	def _applet (self):

		oApp = self.oSus.oApp
		self._taskq.process()

		t = systime()
		if t >= self._lastPlotUpdateAt + 2:
			self._lastPlotUpdateAt = t

			for (wPlot, trace1, trace2) in self._plots.values():
				if wPlot.damaged() : wPlot.redraw()

		self._hApplet = oApp.master.after (50, self._applet)

	def schedule_task (self, task, *args):
		self._taskq.push (task, *args)

	def refresh (self):
		self.oSus.oApp.master.update()

	def close (self):
		oApp = self.oSus.oApp
		oApp.close()
		oApp.master.after_cancel (self._hApplet)
		oApp.master.destroy()

	# +++++++++++++ Acquisition functions +++++++++++++++

	def setRunMode (self, mode):
		oApp = self.oSus.oApp
		oApp.setRunMode (mode)

		oSus = self.oSus
		oSus.runMode = mode

	def setRunControlStatus (self, status):
		oApp = self.oSus.oApp
		oApp.setRunControlStatus (status)

	def setAcqSetting (self, stepSize, maxDepth, probeUp, probeDown):
		self.oSus.linac.set(stepSize, abs(maxDepth), probeUp, probeDown)
		text = ('XL acquisition settings modified.')
		self.oSus.oApp.set_status (text)

	# +++++++++++++ Update display functions +++++++++++++++

	def set_status (self, text):
		self.oSus.oApp.set_status (text)

	# +++++ Plot functions ++++

	def initPlot (self, thread, title, xlabel, ylabel, key1, key2):
		oApp = self.oSus.oApp
		wPlot = oApp.newPlot (title)
		wPlot.xlabel (xlabel)
		wPlot.ylabel (ylabel)
		trace1 = wPlot.new_dataset ('k-', key1)
		trace2 = wPlot.new_dataset ('b-', key2)
		wPlot.damage()
		self._plots[thread] = (wPlot, trace1, trace2)

	# 'linear' or 'log'
	def setPlotScale (self, thread, xscale, yscale):
		if thread in self._plots:
			(wPlot, trace1, trace2) = self._plots[thread]
			wPlot.xscale (xscale)
			wPlot.yscale (yscale)
			wPlot.damage()

	def updatePlot (self, thread, x, y1, y2):
		if thread in self._plots:
			(wPlot, trace1, trace2) = self._plots[thread]
			wPlot.add_datapoint (trace1, x, y1)
			wPlot.add_datapoint (trace2, x, y2)
			wPlot.damage()

	def clearPlot (self):
		oApp = self.oSus.oApp
		oApp.clearPlot()
		self._plots.clear()

	def setProbePosition (self, position):
		oApp = self.oSus.oApp
		oApp.setProbePosition (position)

	def setProbeMinMax (self, probeMinMax):
		oSus = self.oSus
		oSus.linac.probeDown = max (probeMinMax)
		oSus.linac.probeUp   = min (probeMinMax)

	def activate_proceed (self):
		oApp = self.oSus.oApp
		oApp.activate_proceed()

	def deactivate_proceed (self):
		oApp = self.oSus.oApp
		oApp.deactivate_proceed()

	def acquisition_atexit (self):
		self.oSus.releaseAcquisition()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Linac :

	def __init__ (self):
		self.stepSize = 1e-3
		self.maxDepth = Preferences.get_XMC_linacStrokeLength ()
		self.probeUp = 0.0
		self.probeDown = self.maxDepth

	def set (self, stepSize, maxDepth, probeUp, probeDown):
		self.stepSize  = stepSize
		self.maxDepth  = maxDepth
		self.probeUp   = probeUp
		self.probeDown = probeDown

	def get (self):
		return (self.stepSize, self.maxDepth,
				self.probeUp, self.probeDown)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def SUS (master, oTCON, oXLIA, oXMC, sample, cryostat):

	if SUS.singleton == None:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()

		oApp          = GUI (win, sample)
		SUS.singleton = _SUS (
			oApp, oTCON, oXLIA, oXMC, sample, cryostat)

	if master not in SUS.master:
		SUS.master.append (master)

	return SUS.singleton

def closeSUS (master):

	if master in SUS.master:
		SUS.master.remove (master)

	if len (SUS.master) == 0 and SUS.singleton:
		SUS.singleton.close()
		SUS.singleton = None

SUS.singleton = None
SUS.master    = []

class _SUS:

	def __init__ (self, oApp, oTCON, oXLIA, oXMC, sample, cryostat):

		self.oApp     = oApp
		self.oTCON    = oTCON
		self.oXLIA    = oXLIA
		self.oXMC     = oXMC
		self.sample   = sample
		self.cryostat = cryostat
		self.runMode  = RUN_MODE_XT_LINEAR_RAMP
		self.linac    = _Linac ()

		# ++++ Update to date GUI ++++

		self.configureWidgets()
		oApp.callback (self.oAppCB)

		# ++++ Support for multi-threading ++++

		self.oApplet    = _Applet (self)
		self.oModule    = None
		self.oAcqThread = None

		# Initialize gui

		self.oApplet.setRunMode (self.runMode)


	def	configureWidgets (self):
		self.oApp.addTconMenu (self.oTCON.oApp.utilmenu)
		self.oApp.addXliaMenu (self.oXLIA.oApp.utilmenu)
		self.oApp.addXmcMenu  (self.oXMC.oApp.toolsmenu)

	def show (self):
		win = self.oApp.master
		win.deiconify()
		win.lift()

	def hide (self):
		win = self.oApp.master
		win.withdraw()

	def wTCONCB (self):
		self.oTCON.show()

	def wXLIACB (self):
		self.oXLIA.show()

	def wXMCCB (self):
		self.oXMC.show()

	def close (self):

		oApplet = self.oApplet

		# Terminating acquisition thread
		if self.oAcqThread:
			self.oAcqThread.schedule_termination()
			while self.oAcqThread:
				sleep (0.05)
				self.oApplet.refresh()

		# Closing GUI
		self.oApplet.close()

	# +++++++++++++++ GUI callback ++++++++++++++++++

	def oAppCB (self, context, *args):
		oApplet = self.oApplet
		if   context == RUN_MODE        : oApplet.setRunMode  (*args)
		elif context == START_RUN       : self.startRun       (*args)
		elif context == FINISH_RUN      : self.finishRun      ()
		elif context == OPEN_DEVICE     : self.openDevice     (*args)
		elif context == OPEN_METHOD     : self.openMethod     (*args)
		elif context == SAVE_METHOD     : self.saveMethod     (*args)
		elif context == PROCEED_RUN     : self.proceedRun     ()
		elif context == OPEN_DIALOG     : self.openDialog     (*args)
		elif context == XL_FIND_EXTREMA : self.XL_findExtrema ()
		else                            : raise ValueError    (context)

	# ++++++++ Settings dialog callback functions ++++++++

	def openDialog (self, dialog):
		if dialog == ACQ_SETTING_DIALOG: self.openAcqSettingDialog()
		else                              : raise ValueError (dialog)

	# +++++++++ Device control functions ++++++++++++++++++

	def openDevice (self, device):
		if   device == TCON_DEVICE : self.oTCON.show()
		elif device == XLIA_DEVICE : self.oXLIA.show()
		elif device == XMC_DEVICE  : self.oXMC.show()
		else                       : raise ValueError (device)

	# +++++++++ Acquisition functions ++++++++++++++++++

	def startRun (self, runMode):

		self.oApplet.setRunControlStatus (RUN_STARTING)

		try:
			thread = self.prepareAcquisition (runMode)
			thread.start()

		except (
			TCON_ResourceError, XLIA_ResourceError,
			XMC_ResourceError, ResourceError) as e:
				self.oApplet.set_status (str (e))
				self.oApplet.setRunControlStatus (RUN_FINISHED)

	def finishRun (self):

		if self.oAcqThread:
			self.oApplet.setRunControlStatus (RUN_FINISHING)
			self.oAcqThread.schedule_termination()
		else:
			text = 'Cannot stop! Running in slave mode.'
			self.oApplet.set_status (text)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareModule (self, master, runMode):

		module       = None
		oSus         = self
		tcon_prepmod = self.oTCON.prepareModule
		xlia_prepmod = self.oXLIA.prepareModule
		xmc_prepmod  = self.oXMC.prepareModule

		try:
			if self.oModule == None:

				if runMode == RUN_MODE_XT_LINEAR_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_LINEAR_RAMP)
					modXLIA = xlia_prepmod (master, XLIA_RUN_MODE_VTime)
					modXMC  = xmc_prepmod  (master, XMC_RUN_MODE_MONITOR)

					module  = _XTLinearRampModule (
						master, oSus, modTCON, modXLIA, modXMC)

					module.initLinacStroke (
						self.linac.probeUp, self.linac.probeDown)

				elif runMode == RUN_MODE_XT_STEP_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_STEPPED_RAMP)
					modXLIA = xlia_prepmod (master, XLIA_RUN_MODE_VTime)
					modXMC  = xmc_prepmod  (master, XMC_RUN_MODE_MONITOR)

					module  = _XTStepRampModule (
						master, oSus, modTCON, modXLIA, modXMC)

					module.initLinacStroke (
						self.linac.probeUp, self.linac.probeDown)

				elif runMode == RUN_MODE_XF_STEP_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_STEPPED_RAMP)
					modXLIA = xlia_prepmod (master, XLIA_RUN_MODE_VF)
					modXMC  = xmc_prepmod  (master, XMC_RUN_MODE_MONITOR)

					module  = _XFTStepRampModule (
						master, oSus, modTCON, modXLIA, modXMC)

					module.initLinacStroke (
						self.linac.probeUp, self.linac.probeDown)

				elif runMode == RUN_MODE_XL:
					modTCON = tcon_prepmod (master, TCON_RUN_MODE_MONITOR)
					modXLIA = xlia_prepmod (master, XLIA_RUN_MODE_VTime)
					modXMC  = xmc_prepmod  (master, XMC_RUN_MODE_MONITOR)

					module  = _XL_Module (
						master, oSus, modTCON, modXLIA, modXMC)

					module.initLinacStroke (
						self.linac.maxDepth, 0.0, self.linac.stepSize)

				else:
					raise ResourceError (
						'SUS_ResourceError: Module creation failed')

				self.oModule = module
				self.select_cryostat (runMode)

			else:
				raise ResourceError (
					'SUS_ResourceError: Module unavailable')

		except (TCON_ResourceError, XLIA_ResourceError, XMC_ResourceError):
			self.oTCON.releaseModule (self)
			self.oXLIA.releaseModule (self)
			self.oXMC.releaseModule  (self)
			raise

		return module

	def releaseModule (self, caller):

		if self.oModule and caller == self.oModule.master:
			self.oTCON.releaseModule (caller)
			self.oXLIA.releaseModule (caller)
			self.oXMC.releaseModule  (caller)
			self.oModule = None

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareAcquisition (self, runMode):

		thread = None
		master = self

		try:

			if self.oAcqThread == None:

				module = self.prepareModule (master, runMode)

				if runMode == RUN_MODE_XT_LINEAR_RAMP:
					thread = _XTLinearRampThread (module)

				elif runMode == RUN_MODE_XT_STEP_RAMP:
					thread = _XTStepRampThread (module)

				elif runMode == RUN_MODE_XF_STEP_RAMP:
					thread = _XFTStepRampThread (module)

				elif runMode == RUN_MODE_XL:
					thread = _XL_Thread (module)

				else:
					raise ResourceError (
						'SUS_ResourceError: Thread creation failed')

				thread.atexit (self.acquisition_atexit)
				self.oAcqThread = thread

			else:
				raise ResourceError (
					'SUS_ResourceError: Thread unavailable')

		except ResourceError:
			self.releaseModule (self)
			raise

		return thread

	def acquisition_atexit (self):
		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.acquisition_atexit)

	def releaseAcquisition (self):
		self.releaseModule (self)
		self.oAcqThread = None

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def proceedRun (self):
		oAcqThread = self.oAcqThread
		if oAcqThread != None and oAcqThread.is_alive():
			oAcqThread.schedule_task (oAcqThread.proceed)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openAcqSettingDialog (self):

		w = self.dialog = GUI_AcqSetting (
			Toplevel (takefocus = True),
			self.linac.stepSize, self.linac.maxDepth,
			self.linac.probeUp , self.linac.probeDown)

		w.callback (self.AcqSettingDialogCB)

		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def AcqSettingDialogCB (self, context, *args):

		oApplet = self.oApplet
		oModule = self.oModule

		if context == APPLY:
			oApplet.schedule_task (oApplet.setAcqSetting, *args)

			if oModule:

				(stepSize, maxDepth, probeUp, probeDown) = args

				if isinstance (oModule, _DualPositionModule):
					oModule.setLinacStroke (probeUp, probeDown)

				elif isinstance (oModule, _XL_Module):
					oModule.setLinacStroke (maxDepth, 0.0, stepSize)

				else: pass

			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMethod (self):
		method = Method()
		method.set_TCON_Method   (self.oTCON.getMethod())
		method.set_XLIA_Method   (self.oXLIA.getMethod())
		method.setRunMode        (self.runMode          )
		method.setLinacMaxDepth  (self.linac.maxDepth   )
		method.setLinacStepSize  (self.linac.stepSize   )
		method.setLinacProbeUp   (self.linac.probeUp    )
		method.setLinacProbeDown (self.linac.probeDown  )
		return method

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def applyMethod (self, method):

		oTCON   = self.oTCON
		oXLIA   = self.oXLIA
		oApplet = self.oApplet
		oModule = self.oModule

		oTCON.applyMethod (method.get_TCON_Method (oTCON.getMethod()))
		oXLIA.applyMethod (method.get_XLIA_Method (oXLIA.getMethod()))

		mode = method.getRunMode (self.runMode)
		oApplet.schedule_task (oApplet.setRunMode, mode)

		# +++++++++++++++++++++++++++++++++

		linacStepSize 	= method.getLinacStepSize  (self.linac.stepSize )
		linacMaxDepth 	= method.getLinacMaxDepth  (self.linac.maxDepth )
		linacProbeUp  	= method.getLinacProbeUp   (self.linac.probeUp  )
		linacProbeDown	= method.getLinacProbeDown (self.linac.probeDown)

		oApplet.schedule_task (oApplet.setAcqSetting,
							linacStepSize, linacMaxDepth,
							linacProbeUp , linacProbeDown)

		if oModule and isinstance (oModule, _DualPositionModule):
			oModule.schedule_task (
				oModule.setLinacStroke,
				linacProbeUp, linacProbeDown)

		if oModule and isinstance (oModule, _XL_Module):
			oModule.schedule_task (
				oModule.setLinacStroke,
				linacMaxDepth, 0.0, linacStepSize)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def saveMethod (self, fd):
		self.getMethod().save (fd)

		oApplet = self.oApplet
		text = 'Method saved : ' + fd.name
		oApplet.schedule_task (oApplet.set_status, text)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openMethod (self, fd):

		try:
			self.applyMethod (Method (fd))
			text = 'Method opened : ' + fd.name

		except XMethodError as e:
			text = 'Method failed : ' + str (e) + ' : ' + fd.name

		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.set_status, text)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def select_cryostat (self, run_mode):

		insert_dict = {

			RUN_MODE_XT_LINEAR_RAMP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_XT
			),

			RUN_MODE_XT_STEP_RAMP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_XT
			),

			RUN_MODE_XF_STEP_RAMP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_XT
			),

			RUN_MODE_XL_PREP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_XT
			),

			RUN_MODE_XL : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_XT
			),
		}

		(cryostat_type, insert_type) = insert_dict.get (run_mode)

		self.cryostat.set_cryostat_type (cryostat_type)
		self.cryostat.set_insert_type   (insert_type)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Module (XThreadModule):

	def __init__ (self, master, oSus, modTCON, modXLIA, modXMC):
		XThreadModule.__init__ (self, master)
		self.oSus    = oSus
		self.modTCON = modTCON
		self.modXLIA = modXLIA
		self.modXMC  = modXMC
		self.t0      = None
		self.dataset = None
		self.fd_log  = None

	# ++++ Useful functions used by derived classes ++++

	def run_type (self):
		return ''

	def xlabel (self):
		return ''

	def ylabel (self):
		return ''

	def folder_name (self):
		return 'sus'

	def init (self):

		oSus   = self.oSus
		oApplet = oSus.oApplet

		try:
			self.filename = self.get_timestamp()
			oApplet.schedule_task (oApplet.setRunControlStatus, RUN_STARTING)

			self.t0      = systime()
			self.dataset = DataSet()

			self.open_log()
			text = 'Log file: ' + self.fd_log.name
			oApplet.schedule_task (oApplet.set_status, text)

			oApplet.schedule_task (oApplet.clearPlot)

			oApplet.schedule_task (
				oApplet.initPlot, self,
				self.run_type() + ' (' + self.filename + ')',
				self.xlabel(), self.ylabel(), 'Chi\'', 'Chi"')

			text = self.run_type() + ' started'
			oApplet.schedule_task (oApplet.set_status, text)
			oApplet.schedule_task (oApplet.setRunControlStatus, RUN_STARTED)

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

	def atexit (self):

		oSus   = self.oSus
		oApplet = oSus.oApplet

		oApplet.schedule_task (oApplet.setRunControlStatus, RUN_FINISHING)

		# Save data
		try:

			if not self.dataset.empty():

				save_path = self.save (self.dataset)

				text = 'Data saved at ' + save_path
				oApplet.schedule_task (oApplet.set_status, text)

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)

		self.close_log()

		text = self.run_type() + ' finished'
		oApplet.schedule_task (oApplet.set_status, text)
		oApplet.schedule_task (oApplet.setRunControlStatus, RUN_FINISHED)

	# ++++ Acquisition functions ++++

	def chi (
		self, frequency,
		signalAmplitude, signalPhase,
		currentAmplitude, currentPhase) :

		chi   = signalAmplitude / (currentAmplitude * frequency)
		phase = signalPhase - currentPhase

		chiP  = chi * sin (phase)
		chiDP = chi * cos (phase)

		return (chiP, chiDP)

	def goto_n_acquire (self, pos, xlia_mode, bg_task = None, *bg_tasks):

		self.do_tasks (bg_task, *bg_tasks)

		linac_datapoint = self.modXMC.goto (
			pos, self.do_tasks, bg_task, *bg_tasks)

		tcon_datapoint  = self.modTCON.acquire_n_plot (
			self.do_tasks, bg_task, *bg_tasks)

		xlia_datapoint  = self.modXLIA.acquire_n_plot (
			xlia_mode, self.do_tasks, bg_task, *bg_tasks)

		(chiP, chiDP) = self.chi (
			xlia_datapoint.refFrequency,
			xlia_datapoint.signalAmplitude, xlia_datapoint.signalPhase,
			xlia_datapoint.currentAmplitude, xlia_datapoint.currentPhase)

		return DataPoint (
			systime() - self.t0,
			xlia_datapoint.refFrequency,
			xlia_datapoint.currentAmplitude,
			xlia_datapoint.currentPhase,
			xlia_datapoint.signalAmplitude,
			xlia_datapoint.signalPhase,
			chiP, chiDP,
			tcon_datapoint.sampleTemperature,
			tcon_datapoint.heaterTemperature,
			linac_datapoint.position)

	# ++++ Logging functions ++++

	def open_log (self, label = None):

		(self.fd_log, full_path) = self.open_file (
			self.filename + '_' + self.run_type()
			+ [('_'+str(label)),''][label == None], 'csv', 'w')

		fields = [
			('Time',                 'sec'),
			('Reference frequency',   'Hz'),
			('Current amplitude',      'A'),
			('Current phase',        'Rad'),
			('Signal amplitude',       'V'),
			('Signal phase',         'Rad'),
			('chiP',                'a.u.'),
			('chiDP',               'a.u.'),
			('Sample temperature',     'K'),
			('Heater temperature',     'K'),
			('Probe position',        'mm')
		]

		(sampleName, sampleID, sampleDescription) = self.oSus.sample.get()
		self.fd_log.write ('#Sample name        : ' + sampleName        + '\n')
		self.fd_log.write ('#Sample ID          : ' + sampleID          + '\n')

		label =            '#Sample description : '
		sampleDescription = sampleDescription.replace ('\n', '\n' + label)
		self.fd_log.write (label + sampleDescription + '\n')

		text = ''
		for (name, unit) in fields : text += name + ','
		self.fd_log.write ('#' + text + '\n')

		text = ''
		for (name, unit) in fields : text += unit + ','
		self.fd_log.write ('#' + text + '\n')

		self.fd_log.flush()
		return full_path

	def update_log (self, datapoint):

		'''
			Prints on screen
		'''

		fields = [
			('Time',
				'%-.1f', datapoint.time,
				1.0, 'sec'),

			('Reference frequency',
				'%-.2f', datapoint.refFrequency,
				1.0, 'Hz'),

			('Current amplitude',
				'%-.5e', datapoint.currentAmplitude,
				A_to_mA, 'mA'),

			('Current phase',
				'%-.1f', datapoint.currentPhase,
				rad_to_deg, 'Deg'),

			('Signal amplitude',
				'%-.5e', datapoint.signalAmplitude,
				V_to_mV, 'mV'),

			('Signal phase',
				'%-.1f', datapoint.signalPhase,
				rad_to_deg, 'Deg'),

			('ChiP',
				'%-.1f', datapoint.chiP,
				1.0, 'a.u.'),

			('ChiDP',
				'%-.1f', datapoint.chiDP,
				1.0, 'a.u.'),

			('Sample temperature',
				'%-.2f', datapoint.sampleTemperature,
				1.0, 'K'),

			('Heater temperature',
				'%-.1f', datapoint.heaterTemperature,
				1.0, 'K'),

			('Probe position',
				'%-.2f', datapoint.probePosition,
				1e3, 'mm'),
		]

		text = ''
		for (name, fmt, value, mult, unit) in fields :
			text += (
				str ('%-25s' % name) + ' : ' +
				str (fmt % (value * mult)) +
				' ' + unit + '\n')

		print text

		'''
			Writes to file
		'''
		text = ''
		for (name, fmt, value, mult, unit) in fields:
			text += str ('%e' % value) + ','

		self.fd_log.write (text + '\n')
		self.fd_log.flush()


	def close_log (self):

		if self.fd_log != None:
			self.fd_log.close()

		self.fd_log = None

	def save (self, dataset, label = None):

		dict = XDict()
		dict.set_sample (self.oSus.sample.get())
		#dict.set_events ({})

		fields = [
			('01 Time',                DATASET_COL_TIME,          'Second'),
			('02 Reference frequency', DATASET_COL_REF_FREQ,          'Hz'),
			('03 Current amplitude',   DATASET_COL_CURRENT_AMPL,       'A'),
			('04 Current phase',       DATASET_COL_CURRENT_PHASE,    'Rad'),
			('05 Signal amplitude',    DATASET_COL_SIGNAL_AMPL,        'V'),
			('06 Signal phase',        DATASET_COL_SIGNAL_PHASE,     'Rad'),
			('07 ChiP',                DATASET_COL_CHIP,            'a.u.'),
			('08 ChiDP',               DATASET_COL_CHIDP,           'a.u.'),
			('09 Sample temperature',  DATASET_COL_SAMPLE_TEMPERATURE, 'K'),
			('10 Heater temperature',  DATASET_COL_HEATER_TEMPERATURE, 'K'),
			('11 Probe position',      DATASET_COL_PROBE_POSITION,     'm')
		]

		for (key, col, unit) in fields:
			dict.set_data (key, dataset.getColumn (col), unit)

		(fd, full_path) = self.open_file (
			self.filename + '_' + self.run_type()
			 + [('_' + str (label)), ''][label == None], 'xpl', 'w')

		dict.save (fd)
		fd.close()

		return full_path

	def open_file (self, file_name, file_ext, open_mode):

		(sampleName, sampleID, _) = self.oSus.sample.get()

		folder = os.path.join (Preferences.getDataFolder(),
							   sampleName + sampleID,
							   self.folder_name())

		full_path = os.path.join (
			folder, file_name + os.extsep + file_ext)

		if ((open_mode == 'w') and (not os.path.exists (folder))):
			os.makedirs (folder)

		fd = open (full_path, open_mode)

		return (fd, full_path)

	def get_timestamp (self):
		lt = localtime (systime())
		file_name = (
			str ('%04d' % lt.tm_year) +
			str ('%02d' % lt.tm_mon)  +
			str ('%02d' % lt.tm_mday) + '_' +
			str ('%02d' % lt.tm_hour) +
			str ('%02d' % lt.tm_min)  +
			str ('%02d' % lt.tm_sec))
		return file_name

	def do_tasks (self, bg_task = None, *bg_tasks):
		XThreadModule.do_tasks (
			self, self.modTCON.do_tasks, self.modXLIA.do_tasks,
			self.modXMC.do_tasks, bg_task, *bg_tasks)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _AcquisitionThread (XThread):

	def __init__ (self, module):
		XThread.__init__ (self, daemon = True)
		self.module = module

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _DualPositionModule (_Module):

	def __init__ (self, master, oSus, modTCON, modXLIA, modXMC):
		_Module.__init__ (self, master, oSus, modTCON, modXLIA, modXMC)
		self.datasetProbeUp   = DataSet()
		self.datasetProbeDown = DataSet()
		self.linacProbeUp     = None
		self.linacProbeDown   = None

	def initLinacStroke (self, up, down):
		self.linacProbeUp = up
		self.linacProbeDown = down

	def setLinacStroke (self, up, down):
		self.initLinacStroke (up, down)
		oApplet = self.oSus.oApplet
		text    = 'Probe stroke updated'
		oApplet.schedule_task (oApplet.set_status, text)

	def init (self):
		_Module.init (self)
		self.datasetProbeUp   = DataSet()
		self.datasetProbeDown = DataSet()

	def atexit (self):

		oApplet = self.oSus.oApplet

		try:
			if not self.datasetProbeUp.empty():

				save_path = self.save (self.datasetProbeUp, 'PU')
				text = 'Probe-up data saved at ' + save_path
				print text

			if not self.datasetProbeDown.empty():

				save_path = self.save (self.datasetProbeDown, 'PD')
				text = 'Probe-down data saved at ' + save_path
				print text

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)

		_Module.atexit (self)

	def getAverageCurrent (self, upAmpl, upPhase, downAmpl, downPhase):

		upInph = upAmpl * cos (upPhase)
		upQuad = upAmpl * sin (upPhase)

		downInph = downAmpl * cos (downPhase)
		downQuad = downAmpl * sin (downPhase)

		quad  = (upQuad + downQuad) / 2
		inph  = (upInph + downInph) / 2
		ampl  = hypot (quad, inph)
		phase = atan2 (quad, inph)

		return (quad, inph, ampl, phase)

	def getAverageSignal (self, upAmpl, upPhase, downAmpl, downPhase):

		upInph = upAmpl * cos (upPhase)
		upQuad = upAmpl * sin (upPhase)

		downInph = downAmpl * cos (downPhase)
		downQuad = downAmpl * sin (downPhase)

		quad  = upQuad - downQuad
		inph  = upInph - downInph
		ampl  = hypot (quad, inph)
		phase = atan2 (quad, inph)

		return (quad, inph, ampl, phase)

	def acquire (self, bg_task = None, *bg_tasks):

		self.do_tasks (bg_task, *bg_tasks)

		# ++++ Do acquisition ++++

		downDataPoint = self.goto_n_acquire (
			self.linacProbeDown, XLIA_MEASUREMENT_MODE_QUICK,
			self.do_tasks, bg_task, *bg_tasks)

		upDataPoint = self.goto_n_acquire (
			self.linacProbeUp, XLIA_MEASUREMENT_MODE_QUICK,
			self.do_tasks, bg_task, *bg_tasks)

		refFrequency = (
			upDataPoint.refFrequency +
			downDataPoint.refFrequency) / 2

		# ++++ Calculate average current and signal ++++

		(currentQuad, currentInph, currentAmplitude, currentPhase) = \
			self.getAverageCurrent (
				upDataPoint.currentAmplitude,
				upDataPoint.currentPhase,
				downDataPoint.currentAmplitude,
				downDataPoint.currentPhase)

		(signalQuad, signalInph, signalAmplitude, signalPhase) = \
			self.getAverageSignal (
				upDataPoint.signalAmplitude,
				upDataPoint.signalPhase,
				downDataPoint.signalAmplitude,
				downDataPoint.signalPhase)

		# ++++ Calculate X' and X" ++++

		(chiP, chiDP) = self.chi (
			refFrequency,
			signalAmplitude, signalPhase,
			currentAmplitude, currentPhase)

		# ++++ Calculate temperature ++++

		sampleTemperature = (
			upDataPoint.sampleTemperature +
			downDataPoint.sampleTemperature) / 2

		heaterTemperature = (
			upDataPoint.heaterTemperature +
			downDataPoint.heaterTemperature) / 2

		# ++++ Generate up, down, and average datapoint ++++

		datapoint = DataPoint (
			systime() - self.t0,
			refFrequency,
			currentAmplitude,
			currentPhase,
			signalAmplitude,
			signalPhase,
			chiP, chiDP,
			sampleTemperature,
			heaterTemperature)

		return (upDataPoint, downDataPoint, datapoint)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XTLinearRampModule (_DualPositionModule):

	def __init__ (self, master, oSus, modTCON, modXLIA, modXMC):
		_DualPositionModule.__init__ (
			self, master, oSus, modTCON, modXLIA, modXMC)

	def run_type (self):
		return 'Chi_T'

	def xlabel (self):
		return 'Sample temperature (K)'

	def ylabel (self):
		return 'Chi (a.u.)'

	def init (self):

		_DualPositionModule.init (self)

		oApplet = self.oSus.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_XT_LINEAR_RAMP)

		self.modTCON.init()
		self.modXLIA.init()
		self.modXMC.init()

	def atexit (self):

		self.modTCON.atexit()
		self.modXLIA.atexit()
		self.modXMC.atexit()

		_DualPositionModule.atexit (self)

	def complete (self):
		return True if self.modTCON.complete() else False

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oSus.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:
			self.modTCON.acquire_n_plot()

			if not self.modTCON.complete():

				(upDataPoint, downDataPoint, datapoint) = \
					self.acquire (self.do_tasks, bg_task, *bg_tasks)

				self.datasetProbeUp.append (upDataPoint)
				self.datasetProbeDown.append (downDataPoint)
				self.dataset.append (datapoint)
				self.update_log (datapoint)

				oApplet.schedule_task (
					oApplet.updatePlot, self,
					datapoint.sampleTemperature,
					datapoint.chiP, datapoint.chiDP)

			else:
				upDataPoint = downDataPoint = datapoint = None

		except (TCON_LinkError, TCON_CommError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (XLIA_LinkError, XLIA_CommError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (XMC_LinkError, XMC_CommError, XMC_StallError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return (upDataPoint, downDataPoint, datapoint)

class _XTLinearRampThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()

			while True :
				self.do_tasks()
				self.module.acquire_n_plot (self.do_tasks)
				if self.module.complete(): break

		except (TCON_LinkError, TCON_CommError)               : pass
		except (XLIA_LinkError, XLIA_CommError)               : pass
		except (XMC_LinkError, XMC_CommError, XMC_StallError) : pass
		except (IOError, OSError)                             : pass
		except XTerminate                                     : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XTStepRampModule (_DualPositionModule):

	def __init__ (self, master, oSus, modTCON, modXLIA, modXMC):
		_DualPositionModule.__init__ (
			self, master, oSus, modTCON, modXLIA, modXMC)

	def run_type (self):
		return 'Chi_T'

	def xlabel (self):
		return 'Sample temperature (K)'

	def ylabel (self):
		return 'Chi (a.u.)'

	def init (self):

		_DualPositionModule.init (self)

		oApplet = self.oSus.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_XT_STEP_RAMP)

		self.modTCON.init()
		self.modXLIA.init()
		self.modXMC.init()

	def atexit (self):

		self.modTCON.atexit()
		self.modXLIA.atexit()
		self.modXMC.atexit()

		_DualPositionModule.atexit (self)

	def complete (self):
		return True if self.modTCON.complete() else False

	def stabilize_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oSus.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			self.modTCON.set_n_stabilize (self.do_tasks, bg_task, *bg_tasks)

			if not self.modTCON.complete():

				(upDataPoint, downDataPoint, datapoint) = \
					self.acquire (self.do_tasks, bg_task, *bg_tasks)

				self.datasetProbeUp.append (upDataPoint)
				self.datasetProbeDown.append (downDataPoint)
				self.dataset.append (datapoint)
				self.update_log (datapoint)

				oApplet.schedule_task (
					oApplet.updatePlot, self,
					datapoint.sampleTemperature,
					datapoint.chiP, datapoint.chiDP)

			else:
				upDataPoint = downDataPoint = datapoint = None

		except (TCON_LinkError, TCON_CommError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (XLIA_LinkError, XLIA_CommError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (XMC_LinkError, XMC_CommError, XMC_StallError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return (upDataPoint, downDataPoint, datapoint)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XTStepRampThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()
			while True :
				self.do_tasks()
				self.module.stabilize_n_plot (self.do_tasks)
				if self.module.complete(): break

		except (TCON_LinkError, TCON_CommError)               : pass
		except (XLIA_LinkError, XLIA_CommError)               : pass
		except (XMC_LinkError, XMC_CommError, XMC_StallError) : pass
		except (IOError, OSError)                             : pass
		except XTerminate                                     : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XFTStepRampModule (_DualPositionModule):

	def __init__ (self, master, oSus, modTCON, modXLIA, modXMC):
		_DualPositionModule.__init__ (
			self, master, oSus, modTCON, modXLIA, modXMC)

	def run_type (self):
		return 'Chi_F'

	def xlabel (self):
		return 'Frequency (Hz)'

	def ylabel (self):
		return 'Chi (a.u.)'

	def init (self):

		_DualPositionModule.init (self)

		oApplet = self.oSus.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_XF_STEP_RAMP)

		self.modTCON.init()
		self.modXMC.init()

		if self.modXLIA.frequencySteppingMode == VF_FREQ_STEP_MODE_LINEAR:
			oApplet.schedule_task (
				oApplet.setPlotScale, self, 'linear', 'linear')

		elif self.modXLIA.frequencySteppingMode == VF_FREQ_STEP_MODE_LOG:
			oApplet.schedule_task (
				oApplet.setPlotScale, self, 'log', 'linear')

		self.modXMC.goto (self.linacProbeUp, self.do_tasks)

	def atexit (self):

		self.modTCON.atexit()
		if self.modXLIA.is_alive() : self.modXLIA.atexit()
		self.modXMC.atexit()

		_DualPositionModule.atexit (self)

	def complete (self):
		return True if self.modTCON.complete() else False

	def breakPlot (self):

		oApplet = self.oSus.oApplet

		blank_datapoint = DataPoint (
			time              = None, refFrequency      = None,
			currentAmplitude  = None, currentPhase      = None,
			signalAmplitude   = None, signalPhase       = None,
			chiP              = None, chiDP             = None,
			sampleTemperature = None, heaterTemperature = None,
			probePosition     = None)

		self.datasetProbeUp.append   (blank_datapoint)
		self.datasetProbeDown.append (blank_datapoint)
		self.dataset.append          (blank_datapoint)

		oApplet.schedule_task (
			oApplet.updatePlot, self,
			blank_datapoint.refFrequency,
			blank_datapoint.chiP, blank_datapoint.chiDP)

		return blank_datapoint

	def stabilize_n_takeXF (self, bg_task = None, *bg_tasks):

		dataset = []
		oSus    = self.oSus
		oApplet = oSus.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			self.modTCON.set_n_stabilize (self.do_tasks, bg_task, *bg_tasks)

			if not self.modTCON.complete():

				self.modXLIA.init()

				while True:

					self.do_tasks (bg_task, *bg_tasks)
					self.modXLIA.applyNextFrequency()

					if not self.modXLIA.complete():

						(upDataPoint, downDataPoint, datapoint) = \
							self.acquire (self.do_tasks, bg_task, *bg_tasks)

						self.datasetProbeUp.append (upDataPoint)
						self.datasetProbeDown.append (downDataPoint)
						self.dataset.append (datapoint)
						self.update_log (datapoint)
						dataset.append (datapoint)

						oApplet.schedule_task (
							oApplet.updatePlot, self,
							datapoint.refFrequency,
							datapoint.chiP, datapoint.chiDP)

					else:
						dataset.append (self.breakPlot())
						break

				self.modXLIA.atexit()

		except (TCON_LinkError, TCON_CommError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (XLIA_LinkError, XLIA_CommError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (XMC_LinkError, XMC_CommError, XMC_StallError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return dataset

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XFTStepRampThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()

			while True:
				self.do_tasks()
				self.module.stabilize_n_takeXF (self.do_tasks)
				if self.module.complete(): break

		except (TCON_LinkError, TCON_CommError)               : pass
		except (XLIA_LinkError, XLIA_CommError)               : pass
		except (XMC_LinkError, XMC_CommError, XMC_StallError) : pass
		except (IOError, OSError)                             : pass
		except XTerminate                                     : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XL_Module (_Module):

	def __init__ (self, master, oSus, modTCON, modXLIA, modXMC):
		_Module.__init__ (self, master, oSus, modTCON, modXLIA, modXMC)
		self.initialPosition = None
		self.finalPosition   = None
		self.probeStep       = None
		self.position        = None
		self._complete       = False

	def initLinacStroke (self, initialPosition, finalPosition, probeStep):
		self.initialPosition = initialPosition
		self.finalPosition   = finalPosition
		self.probeStep       = probeStep

	def setLinacStroke (self, initialPosition, finalPosition, probeStep):
		self.initLinacStroke (initialPosition, finalPosition, probeStep)
		oApplet = self.oSus.oApplet
		text    = 'Probe stroke updated'
		oApplet.schedule_task (oApplet.set_status, text)

	def run_type (self):
		return 'XL'

	def xlabel (self):
		return 'Position (mm)'

	def ylabel (self):
		return 'Chi (a.u.)'

	def init (self):
		_Module.init (self)

		self.position = None
		self._complete = False
		oApplet = self.oSus.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_XL)

		self.modTCON.init()
		self.modXLIA.init()
		self.modXMC.init()

	def atexit (self):

		self.findProbeMinMax()
		self.modTCON.atexit()
		self.modXLIA.atexit()
		self.modXMC.atexit()

		_Module.atexit (self)

	def getNextPosition (self):

		probeStep = abs (self.probeStep)

		# ++++ Calculate next position ++++

		if self.position == None:
			self.position = self.initialPosition

		elif self.finalPosition > self.initialPosition:
			self.position += probeStep
			self.position = probeStep * round (self.position / probeStep)

		elif self.finalPosition < self.initialPosition:
			self.position -= probeStep
			self.position = probeStep * round (self.position / probeStep)

		else: pass

		# ++++ Check for termination ++++

		if (self.finalPosition > self.initialPosition
		and self.position > self.finalPosition):
			self.position  = None
			self._complete = True

		elif (self.finalPosition < self.initialPosition
		and self.position < self.finalPosition):
			self.position  = None
			self._complete = True

		else: pass

		return self.position

	def complete (self):
		return True if self._complete else False

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oSus   = self.oSus
		oApplet = oSus.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:
			position = self.getNextPosition()

			if not self.complete():

				datapoint = self.goto_n_acquire (
					position, XLIA_MEASUREMENT_MODE_QUICK,
					self.do_tasks, bg_task, *bg_tasks)

				self.dataset.append (datapoint)
				self.update_log (datapoint)

				oApplet.schedule_task (
					oApplet.updatePlot, self,
					datapoint.probePosition * m_to_mm,
					datapoint.chiP, datapoint.chiDP)

			else:
				datapoint = None

		except (TCON_LinkError, TCON_CommError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (XLIA_LinkError, XLIA_CommError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (XMC_LinkError, XMC_CommError, XMC_StallError) as e:
			oApplet.schedule_task (oApplet.set_status, str(e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

	def findProbeMinMax (self):

		oApplet = self.oSus.oApplet

		if not self.dataset.empty():

			chiPData = self.dataset.getColumn (DATASET_COL_CHIP)
			positionData = self.dataset.getColumn (DATASET_COL_PROBE_POSITION)

			minIndex = chiPData.index (min (chiPData))
			maxIndex = chiPData.index (max (chiPData))

			probeMinMax = (
				round (positionData[minIndex], 4),
				round (positionData[maxIndex], 4))

			(probeMin, probeMax) = probeMinMax = (
				min (probeMinMax), max (probeMinMax))

			text = (
				'Probe stroke set to ' +
				str ('%.1f' % (probeMin * m_to_mm)) + ' mm and ' +
				str ('%.1f' % (probeMax * m_to_mm)) + ' mm')

			oApplet.schedule_task (oApplet.setProbeMinMax, probeMinMax)
			oApplet.schedule_task (oApplet.set_status, text)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XL_Thread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()

			while True :
				self.do_tasks()
				self.module.acquire_n_plot (self.do_tasks)
				if self.module.complete() : break

		except (TCON_LinkError, TCON_CommError)               : pass
		except (XLIA_LinkError, XLIA_CommError)               : pass
		except (XMC_LinkError, XMC_CommError, XMC_StallError) : pass
		except (IOError, OSError)                             : pass
		except XTerminate                                     : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

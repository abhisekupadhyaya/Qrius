# coding: utf-8

import Preferences
from RES_DataType import DataPoint, DataSet

from app_res     import GUI, GUI_RH_SettingsDialog

from tcon        import TCON
from tcon        import LinkError as TCON_LinkError
from tcon        import CommError as TCON_CommError
from tcon        import ResourceError as TCON_ResourceError

from xsmu        import XSMU
from xsmu        import LinkError as XSMU_LinkError
from xsmu        import CommError as XSMU_CommError
from xsmu        import ResourceError as XSMU_ResourceError

from mgps        import MGPS
from mgps        import LinkError as MGPS_LinkError
from mgps        import CommError as MGPS_CommError
from mgps        import ResourceError as MGPS_ResourceError

from Cryostat_Constants import *

from XDict       import XDict
from XThread     import XTaskQueue, XThread, XThreadModule, XTerminate

# Importing Python provided libraries
import os
from threading   import Thread, RLock, Lock
from time        import time as systime, localtime, sleep
from Tkinter     import NORMAL, DISABLED, Toplevel

from RES_Constants import *
from RES_Method    import Method, XMethodError

from TCON_Constants import RUN_MODE_ISOTHERMAL   as TCON_RUN_MODE_ISOTHERMAL
from TCON_Constants import RUN_MODE_LINEAR_RAMP  as TCON_RUN_MODE_LINEAR_RAMP
from TCON_Constants import RUN_MODE_STEPPED_RAMP as TCON_RUN_MODE_STEPPED_RAMP

from XSMU_Constants import RUN_MODE_IV    as XSMU_RUN_MODE_IV
from XSMU_Constants import RUN_MODE_RTime as XSMU_RUN_MODE_RTime

from MGPS_Constants import RUN_MODE_HTime as MGPS_RUN_MODE_HTime

from math import copysign

class ResourceError (Exception) : pass

class _Applet:

	def __init__ (self, oRes2):

		self.oRes2 = oRes2
		self._plots = {}
		self._taskq = XTaskQueue()
		self._lastPlotUpdateAt = 0.0
		self._hApplet = self.oRes2.oApp.master.after (50, self.applet)

	def applet (self):

		oApp = self.oRes2.oApp
		self._taskq.process()

		t = systime()
		if t >= self._lastPlotUpdateAt + 2:
			self._lastPlotUpdateAt = t

			for (wPlot, traceID) in self._plots.values():
				if wPlot.damaged() : wPlot.redraw()

		self._hApplet = oApp.master.after (50, self.applet)

	def schedule_task (self, task, *args):
		self._taskq.push (task, *args)

	def refresh (self):
		self.oRes2.oApp.master.update()

	def close (self):
		oApp = self.oRes2.oApp
		oApp.close()
		oApp.master.after_cancel (self._hApplet)
		oApp.master.destroy()

	# +++++++++++++ Acquisition functions +++++++++++++++

	def setRunMode (self, mode):
		oApp = self.oRes2.oApp
		oApp.setRunMode (mode)

		oRes2 = self.oRes2
		oRes2.runMode = mode

	def setRunControlStatus (self, status):
		oApp = self.oRes2.oApp
		oApp.setRunControlStatus (status)

	# +++++++++++++ Update display functions +++++++++++++++

	def set_status (self, text):
		self.oRes2.oApp.set_status (text)

	# +++++ Plot functions ++++

	def initPlot (self, thread, title, xlabel, ylabel):
		oApp = self.oRes2.oApp
		wPlot = oApp.newPlot (title)
		wPlot.xlabel (xlabel)
		wPlot.ylabel (ylabel)
		traceID = wPlot.new_dataset ('k-')
		wPlot.damage()
		self._plots[thread] = (wPlot, traceID)

	def updatePlot (self, thread, x, y):
		(wPlot, traceID) = self._plots[thread]
		wPlot.add_datapoint (traceID, x, y)
		wPlot.damage()

	def clearPlot (self):
		oApp = self.oRes2.oApp
		oApp.clearPlot()
		self._plots.clear()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquisition_atexit (self):
		self.oRes2.releaseAcquisition()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def set_rh_settings (self, total_cycle, H_max, H_step):
		self.oRes2.oApp.set_rh_settings (total_cycle, H_max, H_step)
		self.oRes2.rh_settings.set (total_cycle, H_max, H_step)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def RES (master, oTCON, oXSMU, oMGPS, sample, cryostat):

	if RES.singleton == None:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()

		oApp          = GUI (win, sample)
		RES.singleton = _RES (
			oApp, oTCON, oXSMU, oMGPS, sample, cryostat)

	if master not in RES.master:
		RES.master.append (master)

	return RES.singleton

def closeRES (master):

	if master in RES.master:
		RES.master.remove (master)

	if len (RES.master) == 0 and RES.singleton:
		RES.singleton.close()
		RES.singleton = None

RES.singleton = None
RES.master    = []

class RH_Settings:

	def __init__ (self):
		self.total_cycle = 1
		self.H_max       = 0.1
		self.H_step      = 0.01

	def set (self, total_cycle, H_max, H_step):
		self.total_cycle = total_cycle
		self.H_max       = H_max
		self.H_step       = H_step

	def get (self):
		return (self.total_cycle, self.H_max, self.H_step)

class _RES:

	def __init__(self, oApp, oTCON, oXSMU, oMGPS, sample, cryostat):

		self.oApp     = oApp
		self.oTCON    = oTCON
		self.oXSMU    = oXSMU
		self.oMGPS    = oMGPS
		self.sample   = sample
		self.cryostat = cryostat
		self.runMode  = RUN_MODE_RT_LINEAR_RAMP

		self.rh_settings = RH_Settings()
		self.oApp.set_rh_settings (*self.rh_settings.get())

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
		self.oApp.addXsmuMenu (self.oXSMU.oApp.utilmenu)
		self.oApp.add_mgps_menu (self.oMGPS.oApp.utilmenu)

	def show (self):
		win = self.oApp.master
		win.deiconify()
		win.lift()

	def hide (self):
		win = self.oApp.master
		win.withdraw()

	def wTCONCB (self):
		self.oTCON.show()

	def wXSMUCB (self):
		self.oXSMU.show()

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
		if   context == RUN_MODE    : oApplet.setRunMode (*args)
		elif context == START_RUN   : self.startRun      (*args)
		elif context == FINISH_RUN  : self.finishRun     ()
		elif context == OPEN_DEVICE : self.openDevice    (*args)
		elif context == OPEN_METHOD : self.openMethod    (*args)
		elif context == SAVE_METHOD : self.saveMethod    (*args)
		elif context == OPEN_DIALOG : self.open_dialog   (*args)
		else                        : raise ValueError   (context)

	# +++++++++ Device control functions ++++++++++++++++++

	def openDevice (self, device):
		if   device == TCON_DEVICE : self.oTCON.show()
		elif device == XSMU_DEVICE : self.oXSMU.show()
		elif device == MGPS_DEVICE : self.oMGPS.show()
		else                       : raise ValueError (device)

	# +++++++++ Dialog functions ++++++++++++++++++

	def open_dialog (self, dialog):

		if dialog == RH_SETTINGS_DIALOG:
			self.open_rh_settings_dialog()

		else: raise ValueError (dialog)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def open_rh_settings_dialog (self):

		w = self.dialog = GUI_RH_SettingsDialog (
			Toplevel (takefocus = True), *self.rh_settings.get())

		w.callback (self.rh_settings_dialog_cb)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def rh_settings_dialog_cb (self, context, *args):

		oApplet = self.oApplet
		oModule = self.oModule

		if context == APPLY:

			oApplet.schedule_task (oApplet.set_rh_settings, *args)

			if oModule:
				oModule.schedule_task (oModule.set_rh_settings, *args)

			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# +++++++++ Acquisition functions ++++++++++++++++++

	def startRun (self, runMode):

		self.oApplet.setRunControlStatus (RUN_STARTING)

		try:
			thread = self.prepareAcquisition (runMode)
			thread.start()

		except (TCON_ResourceError,
			    XSMU_ResourceError,
			    MGPS_ResourceError,
			    ResourceError) as e:

			self.oApplet.set_status (str(e))
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

		module = None
		tcon_prepmod = self.oTCON.prepareModule
		xsmu_prepmod = self.oXSMU.prepareModule
		mgps_prepmod = self.oMGPS.prepareModule

		try:
			if self.oModule == None:

				if runMode == RUN_MODE_RT_LINEAR_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_LINEAR_RAMP)
					modXSMU = xsmu_prepmod (master, XSMU_RUN_MODE_RTime)
					module = _RTLinearRampModule (
						master, self, modTCON, modXSMU)

				elif runMode == RUN_MODE_RT_STEP_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_STEPPED_RAMP)
					modXSMU = xsmu_prepmod (master, XSMU_RUN_MODE_RTime)
					module = _RTStepRampModule (
						master, self, modTCON, modXSMU)

				elif runMode == RUN_MODE_IV_STEP_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_STEPPED_RAMP)
					modXSMU = xsmu_prepmod (master, XSMU_RUN_MODE_IV)
					module = _IVTStepRampModule (
						master, self, modTCON, modXSMU)

				elif runMode == RUN_MODE_RTH_LINEAR_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_LINEAR_RAMP)
					modXSMU = xsmu_prepmod (master, XSMU_RUN_MODE_RTime)
					modMGPS = mgps_prepmod (master, MGPS_RUN_MODE_HTime)
					module  = _RTH_LinearRampModule (
						master, self, modTCON, modXSMU, modMGPS)

				elif runMode == RUN_MODE_RHT_STEPPED_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_STEPPED_RAMP)
					modXSMU = xsmu_prepmod (master, XSMU_RUN_MODE_RTime)
					modMGPS = mgps_prepmod (master, MGPS_RUN_MODE_HTime)
					module  = _RHT_SteppedRampModule (
						master, self, modTCON, modXSMU, modMGPS)
					module.set_rh_settings (
						*self.rh_settings.get())

				else:
					raise ResourceError (
						'RES_ResourceError: Module creation failed')

				self.oModule = module
				self.select_cryostat (runMode)

			else:
				raise ResourceError (
					'RES_ResourceError: Module unavailable')

		except (
			TCON_ResourceError,
		    XSMU_ResourceError,
		    MGPS_ResourceError
		):
			self.oTCON.releaseModule (self)
			self.oXSMU.releaseModule (self)
			self.oMGPS.releaseModule (self)
			raise

		return module

	def releaseModule (self, caller):

		if self.oModule and caller == self.oModule.master:
			self.oTCON.releaseModule (caller)
			self.oXSMU.releaseModule (caller)
			self.oMGPS.releaseModule (caller)
			self.oModule = None

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareAcquisition (self, runMode):

		thread  = None

		try:

			if self.oAcqThread == None:

				module = self.prepareModule (self, runMode)

				if runMode == RUN_MODE_RT_LINEAR_RAMP:
					thread = _RTLinearRampThread (module)

				elif runMode == RUN_MODE_RT_STEP_RAMP:
					thread = _RTStepRampThread (module)

				elif runMode == RUN_MODE_IV_STEP_RAMP:
					thread = _IVTStepRampThread (module)

				elif runMode == RUN_MODE_RTH_LINEAR_RAMP:
					thread = _RTH_LinearRampThread (module)

				elif runMode == RUN_MODE_RHT_STEPPED_RAMP:
					thread = _RHT_SteppedRampThread (module)

				else:
					raise ResourceError (
						'RES_ResourceError: Thread creation failed')

				thread.atexit (self.acquisition_atexit)
				self.oAcqThread = thread

			else:
				raise ResourceError (
					'RES_ResourceError: Thread unavailable')

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

	def getMethod (self):
		method = Method()
		method.set_TCON_Method (self.oTCON.getMethod())
		method.set_XSMU_Method (self.oXSMU.getMethod())
		method.setRunMode (self.runMode)
		method.set_mgps_method (self.oMGPS.getMethod())
		method.set_rh_settings (*self.rh_settings.get())
		return method

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def applyMethod (self, method):

		oTCON   = self.oTCON
		oXSMU   = self.oXSMU
		oMGPS   = self.oMGPS
		oApplet = self.oApplet

		oTCON.applyMethod (method.get_TCON_Method (oTCON.getMethod()))
		oXSMU.applyMethod (method.get_XSMU_Method (oXSMU.getMethod()))

		mode = method.getRunMode (self.runMode)
		oApplet.schedule_task (oApplet.setRunMode, mode)

		oMGPS.applyMethod (method.get_mgps_method (oMGPS.getMethod()))

		rh_settings = method.get_rh_settings (*self.rh_settings.get())
		oApplet.schedule_task (oApplet.set_rh_settings, *rh_settings)

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

			RUN_MODE_RT_LINEAR_RAMP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_RT
			),

			RUN_MODE_RT_STEP_RAMP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_RT
			),

			RUN_MODE_IV_STEP_RAMP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_RT
			),

			RUN_MODE_RTH_LINEAR_RAMP : (
				CRYOSTAT_TYPE_QUARTZ, INSERT_TYPE_RT_HEATER_PUCK
			),

			RUN_MODE_RHT_STEPPED_RAMP : (
				CRYOSTAT_TYPE_QUARTZ, INSERT_TYPE_RT_HEATER_PUCK
			)
		}

		(cryostat_type, insert_type) = insert_dict.get (run_mode)

		self.cryostat.set_cryostat_type (cryostat_type)
		self.cryostat.set_insert_type   (insert_type)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Module (XThreadModule):

	def __init__ (self, master, oRes2, modTCON, modXSMU, **kwargs):
		XThreadModule.__init__ (self, master)
		self.oRes2   = oRes2
		self.modTCON = modTCON
		self.modXSMU = modXSMU
		self.t0      = systime()
		self.dataset = DataSet()
		self.fd_log  = None
		self.modMGPS = None

	def mgps (self, modMGPS):
		self.modMGPS = modMGPS

	# ++++ Useful functions used by derived classes ++++

	def run_type (self):
		return ''

	def xlabel (self):
		return ''

	def ylabel (self):
		return ''

	def folder_name (self):
		return 'res'

	def init (self):

		oRes2   = self.oRes2
		oApplet = oRes2.oApplet

		try:
			self.filename = self.get_timestamp()
			oApplet.schedule_task (
				oApplet.setRunControlStatus, RUN_STARTING)

			self.t0      = systime()
			self.dataset = DataSet()

			self.open_log()
			text = 'Log file: ' + self.fd_log.name
			oApplet.schedule_task (oApplet.set_status, text)

			oApplet.schedule_task (oApplet.clearPlot)

			oApplet.schedule_task (
				oApplet.initPlot, self,
				self.run_type() + ' (' + self.filename + ')',
				self.xlabel(), self.ylabel())

			text = self.run_type() + ' started'
			oApplet.schedule_task (oApplet.set_status, text)
			oApplet.schedule_task (
				oApplet.setRunControlStatus, RUN_STARTED)

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

	def atexit (self):

		oRes2   = self.oRes2
		oApplet = oRes2.oApplet

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

	# ++++ Logging functions ++++

	def open_log (self):

		(self.fd_log, full_path) = self.open_file (
			self.filename + '_' + self.run_type(), 'csv', 'w')

		fields = [
			('Time',             'sec'),
			('Resistance',       'Ohm'),
			('Current',            'A'),
			('Voltage',            'V'),
			('Sample temperature', 'K'),
			('Heater temperature', 'K'),
			('Magnetic field',     'T'),
		]

		(sampleName, sampleID, sampleDescription) = self.oRes2.sample.get()
		self.fd_log.write ('#Sample name        : ' + sampleName + '\n')
		self.fd_log.write ('#Sample ID          : ' + sampleID   + '\n')

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

			('Resistance',
				'%-.6f', datapoint.resistance,
				1.0, 'Ohm'),

			('Current',
				'%-.3f', datapoint.current,
				A_to_uA, 'uA'),

			('Voltage',
				'%-.3f', datapoint.voltage,
				V_to_mV, 'mV'),

			('Sample temperature',
				'%-.2f', datapoint.sampleTemperature,
				1.0, 'K'),

			('Heater temperature',
				'%-.1f', datapoint.heaterTemperature,
				1.0, 'K'),

			('Magnetic field',
				'%-.3f', datapoint.magnetic_field,
				1.0, 'T')
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

	def save (self, dataset):

		dict = XDict()
		dict.set_sample (self.oRes2.sample.get())
		#dict.set_events ({})

		fields = [
			('01 Time',               DATASET_COL_TIME,          'second'),
			('02 Resistance',         DATASET_COL_RESISTANCE,       'Ohm'),
			('03 Current',            DATASET_COL_CURRENT,            'A'),
			('04 Voltage',            DATASET_COL_VOLTAGE,            'V'),
			('05 Sample Temperature', DATASET_COL_SAMPLE_TEMPERATURE, 'K'),
			('06 Heater Temperature', DATASET_COL_HEATER_TEMPERATURE, 'K'),
			('07 Magnetic field',     DATASET_COL_MAGNETIC_FIELD,     'T'),
		]

		for (key, col, unit) in fields:
			dict.set_data (key, dataset.getColumn (col), unit)

		(fd, full_path) = self.open_file (
			self.filename + '_' + self.run_type(), 'xpl', 'w')

		dict.save (fd)
		fd.close()

		return full_path

	def open_file (self, file_name, file_ext, open_mode):

		(sampleName, sampleID, _) = self.oRes2.sample.get()

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
			self, self.modTCON.do_tasks,
			self.modXSMU.do_tasks, bg_task, *bg_tasks)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _AcquisitionThread (XThread):

	def __init__ (self, module):
		XThread.__init__ (self, daemon = True)
		self.module = module

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RTLinearRampModule (_Module):

	def __init__ (self, master, oRes2, modTCON, modXSMU):
		_Module.__init__ (self, master, oRes2, modTCON, modXSMU)

	def run_type (self):
		return 'RT'

	def xlabel (self):
		return 'Sample temperature (K)'

	def ylabel (self):
		return 'Resistance (Ohm)'

	def init (self):
		_Module.init (self)

		oApplet = self.oRes2.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_RT_LINEAR_RAMP)

		self.modTCON.init()
		self.modXSMU.init()

	def atexit (self):
		self.modXSMU.atexit()
		self.modTCON.atexit()
		_Module.atexit (self)

	def complete (self):
		return True if self.modTCON.complete() else False

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oRes2.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:
			tcon_datapoint = self.modTCON.acquire_n_plot()
			if not self.modTCON.complete():

				xsmu_datapoint = (
					self.modXSMU.acquire_n_plot (
						self.do_tasks, bg_task, *bg_tasks))

				datapoint = DataPoint (
					time              = systime() - self.t0,
					current           = xsmu_datapoint.current,
					voltage           = xsmu_datapoint.voltage,
					resistance        = xsmu_datapoint.resistance,
					sampleTemperature = tcon_datapoint.sampleTemperature,
					heaterTemperature = tcon_datapoint.heaterTemperature)

				self.update_log (datapoint)
				self.dataset.append (datapoint)

				oApplet.schedule_task (oApplet.updatePlot, self,
					datapoint.sampleTemperature, datapoint.resistance)

			else:
				datapoint = None

		except (TCON_CommError, TCON_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (XSMU_CommError, XSMU_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

class _RTLinearRampThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()

			while True :
				self.do_tasks()
				self.module.acquire_n_plot (self.do_tasks)
				if self.module.complete(): break

		except (TCON_LinkError, TCON_CommError) : pass
		except (XSMU_LinkError, XSMU_CommError) : pass
		except (IOError, OSError)               : pass
		except XTerminate                       : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RTStepRampModule (_Module):

	def __init__ (self, master, oRes2, modTCON, modXSMU):
		_Module.__init__ (self, master, oRes2, modTCON, modXSMU)

	def run_type (self):
		return 'RT'

	def xlabel (self):
		return 'Sample temperature (K)'

	def ylabel (self):
		return 'Resistance (Ohm)'

	def init (self):
		_Module.init (self)

		oApplet = self.oRes2.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_RT_STEP_RAMP)

		self.modTCON.init()
		self.modXSMU.init()

	def atexit (self):
		self.modXSMU.atexit()
		self.modTCON.atexit()
		_Module.atexit (self)

	def complete (self):
		return True if self.modTCON.complete() else False

	def stabilize_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oRes2.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			self.modTCON.set_n_stabilize (
				self.do_tasks, bg_task, *bg_tasks)

			if not self.modTCON.complete():

				tcon_datapoint = self.modTCON.acquire_n_plot()
				xsmu_datapoint = self.modXSMU.acquire_n_plot (
					self.do_tasks, bg_task, *bg_tasks)

				datapoint = DataPoint (
					time              = systime() - self.t0,
					current           = xsmu_datapoint.current,
					voltage           = xsmu_datapoint.voltage,
					resistance        = xsmu_datapoint.resistance,
					sampleTemperature = tcon_datapoint.sampleTemperature,
					heaterTemperature = tcon_datapoint.heaterTemperature)

				self.update_log (datapoint)
				self.dataset.append (datapoint)

				oApplet.schedule_task (oApplet.updatePlot, self,
					datapoint.sampleTemperature, datapoint.resistance)

			else:
				datapoint = None

		except (TCON_CommError, TCON_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (XSMU_CommError, XSMU_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RTStepRampThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()
			while True :
				self.do_tasks()
				self.module.stabilize_n_plot (self.do_tasks)
				if self.module.complete(): break

		except (TCON_LinkError, TCON_CommError) : pass
		except (XSMU_LinkError, XSMU_CommError) : pass
		except (IOError, OSError)               : pass
		except XTerminate                       : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _IVTStepRampModule (_Module):

	def __init__ (self, master, oRes2, modTCON, modXSMU):
		_Module.__init__ (self, master, oRes2, modTCON, modXSMU)

	def run_type (self):
		return 'IV_T'

	def xlabel (self):
		return 'Voltage (Volt)'

	def ylabel (self):
		return 'Current (A)'

	def init (self):
		_Module.init (self)

		oApplet = self.oRes2.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_IV_STEP_RAMP)

		self.modTCON.init()

	def atexit (self):
		self.modTCON.atexit()
		if self.modXSMU.is_alive() : self.modXSMU.atexit()
		_Module.atexit (self)

	def complete (self):
		return True if self.modTCON.complete() else False

	def breakPlot (self):

		oApplet = self.oRes2.oApplet

		blank_datapoint = DataPoint (
			time              = None,
			current           = None,
			voltage           = None,
			resistance        = None,
			sampleTemperature = None,
			heaterTemperature = None)

		self.dataset.append (blank_datapoint)

		oApplet.schedule_task (
			oApplet.updatePlot, self,
			blank_datapoint.voltage, blank_datapoint.current)

		return blank_datapoint

	def stabilize_n_takeIV (self, bg_task = None, *bg_tasks):

		dataset = []
		oRes2   = self.oRes2
		oApplet = oRes2.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			self.modTCON.set_n_stabilize (
				self.do_tasks, bg_task, *bg_tasks)

			if not self.modTCON.complete():

				self.modXSMU.init()

				while True:

					self.do_tasks (bg_task, *bg_tasks)
					tcon_datapoint = self.modTCON.acquire_n_plot()
					xsmu_datapoint, breakPlot = (
						self.modXSMU.excite_n_plot (
							self.do_tasks, bg_task, *bg_tasks))

					if breakPlot:
						dataset.append (self.breakPlot())

					if not self.modXSMU.complete():
						datapoint = DataPoint (
					time              = systime() - self.t0,
					current           = xsmu_datapoint.current,
					voltage           = xsmu_datapoint.voltage,
					resistance        = xsmu_datapoint.resistance,
					sampleTemperature = tcon_datapoint.sampleTemperature,
					heaterTemperature = tcon_datapoint.heaterTemperature)

						self.update_log     (datapoint)
						self.dataset.append (datapoint)
						dataset.append      (datapoint)

						oApplet.schedule_task (
							oApplet.updatePlot, self,
							datapoint.voltage, datapoint.current)

					else:
						dataset.append (self.breakPlot())
						break

				self.modXSMU.atexit()

		except (TCON_CommError, TCON_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (XSMU_CommError, XSMU_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return dataset

class _IVTStepRampThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()

			while True:
				self.do_tasks()
				self.module.stabilize_n_takeIV (self.do_tasks)
				if self.module.complete(): break

		except (TCON_LinkError, TCON_CommError) : pass
		except (XSMU_LinkError, XSMU_CommError) : pass
		except (IOError, OSError)               : pass
		except XTerminate                       : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RTH_LinearRampModule (_Module):

	def __init__ (self, master, oRes2, modTCON, modXSMU, modMGPS):
		_Module.__init__ (self, master, oRes2, modTCON, modXSMU)
		_Module.mgps     (self, modMGPS)

	def run_type (self):
		return 'RTH_LinearRamp'

	def xlabel (self):
		return 'Sample temperature (K)'

	def ylabel (self):
		return 'Resistance (Ohm)'

	def init (self):
		_Module.init (self)

		oApplet = self.oRes2.oApplet
		oApplet.schedule_task (
			oApplet.setRunMode, RUN_MODE_RTH_LINEAR_RAMP)

		self.modTCON.init()
		self.modXSMU.init()
		self.modMGPS.init()

	def atexit (self):
		self.modXSMU.atexit()
		self.modTCON.atexit()
		self.modMGPS.atexit()
		_Module.atexit (self)

	def complete (self):
		return True if self.modTCON.complete() else False

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oRes2.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:
			tcon_datapoint = self.modTCON.acquire_n_plot()

			if not self.modTCON.complete():

				xsmu_datapoint = (
					self.modXSMU.acquire_n_plot (
						self.do_tasks, bg_task, *bg_tasks))

				mgps_datapoint = self.modMGPS.acquire_n_plot()

				datapoint = DataPoint (
					time              = systime() - self.t0,
					current           = xsmu_datapoint.current,
					voltage           = xsmu_datapoint.voltage,
					resistance        = xsmu_datapoint.resistance,
					sampleTemperature = tcon_datapoint.sampleTemperature,
					heaterTemperature = tcon_datapoint.heaterTemperature,
					magnetic_field    = mgps_datapoint.magnetic_field)

				self.update_log (datapoint)
				self.dataset.append (datapoint)

				oApplet.schedule_task (oApplet.updatePlot, self,
					datapoint.sampleTemperature, datapoint.resistance)

			else:
				datapoint = None

		except (TCON_CommError, TCON_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (XSMU_CommError, XSMU_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (MGPS_CommError, MGPS_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

class _RTH_LinearRampThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()

			while True :
				self.do_tasks()
				self.module.acquire_n_plot (self.do_tasks)
				if self.module.complete(): break

		except (TCON_LinkError, TCON_CommError) : pass
		except (XSMU_LinkError, XSMU_CommError) : pass
		except (IOError, OSError)               : pass
		except XTerminate                       : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RHT_SteppedRampModule (_Module):

	def __init__ (self, master, oRes2, modTCON, modXSMU, modMGPS):
		_Module.__init__ (self, master, oRes2, modTCON, modXSMU)
		_Module.mgps     (self, modMGPS)

	def run_type (self):
		return 'RHT_SteppedRamp'

	def xlabel (self):
		return 'Magnetic field (T)'

	def ylabel (self):
		return 'Resistance (Ohm)'

	def init (self):
		_Module.init (self)

		oApplet = self.oRes2.oApplet
		oApplet.schedule_task (
			oApplet.setRunMode, RUN_MODE_RHT_STEPPED_RAMP)

		self.modTCON.init()
		self.modXSMU.init()
		self.modMGPS.init()

	def atexit (self):
		self.modXSMU.atexit()
		self.modTCON.atexit()
		self.modMGPS.atexit()
		_Module.atexit (self)

	def set_rh_settings (self, total_cycle, H_max, H_step):
		self.total_cycle = total_cycle
		self.H_max       = H_max
		self.H_step      = H_step

	def complete (self):
		return True if self.modTCON.complete() else False

	def acquire_n_plot (self, H, bg_task = None, *bg_tasks):

		self.modMGPS.setMagneticField (H)

		tcon_datapoint = self.modTCON.acquire_n_plot (
			self.do_tasks, bg_task, *bg_tasks)

		mgps_datapoint = self.modMGPS.acquire_n_plot (
			self.do_tasks, bg_task, *bg_tasks)

		xsmu_datapoint = self.modXSMU.acquire_n_plot (
			self.do_tasks, bg_task, *bg_tasks)

		datapoint = DataPoint (
			time              = systime() - self.t0,
			current           = xsmu_datapoint.current,
			voltage           = xsmu_datapoint.voltage,
			resistance        = xsmu_datapoint.resistance,
			sampleTemperature = tcon_datapoint.sampleTemperature,
			heaterTemperature = tcon_datapoint.heaterTemperature,
			magnetic_field    = mgps_datapoint.magnetic_field)

		self.update_log (datapoint)
		self.dataset.append (datapoint)

		oApplet = self.oRes2.oApplet
		oApplet.schedule_task (oApplet.updatePlot, self,
			datapoint.magnetic_field, datapoint.resistance)

	def acquire_RH (self, bg_task = None, *bg_tasks):

		H = 0
		cycle = 0

		while (cycle < self.total_cycle):

			phase = 0
			# 0: 0      to +H_max
			# 1: +H_max to 0
			# 2: 0      to -H_max
			# 3: -H_max to 0

			while (phase < 4):

				self.do_tasks()
				self.acquire_n_plot (H, bg_task, *bg_tasks)

				bounds = [
					(+self.H_max,  1.0, lambda x, y: x >= y),
					(0.0        , -1.0, lambda x, y: x <= y),
					(-self.H_max, -1.0, lambda x, y: x <= y),
					(0.0        ,  1.0, lambda x, y: x >= y)
				]

				(limit, sign, check) = bounds[phase]

				H = H + copysign (self.H_step, sign)

				if (check (H, limit)):
					H = limit
					phase += 1

			cycle += 1

		self.do_tasks()
		self.acquire_n_plot (H, bg_task, *bg_tasks)

	def stabilize_n_acquire (self, bg_task = None, *bg_tasks):

		oApplet = self.oRes2.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:
			self.modTCON.set_n_stabilize (
				self.do_tasks, bg_task, *bg_tasks)

			if not self.modTCON.complete():
				self.acquire_RH (self.do_tasks, bg_task, *bg_tasks)

		except (TCON_CommError, TCON_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (XSMU_CommError, XSMU_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (MGPS_CommError, MGPS_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

class _RHT_SteppedRampThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()

			while True :
				self.do_tasks()
				self.module.stabilize_n_acquire (self.do_tasks)
				if self.module.complete(): break

		except (TCON_LinkError, TCON_CommError) : pass
		except (XSMU_LinkError, XSMU_CommError) : pass
		except (MGPS_LinkError, MGPS_CommError) : pass
		except (IOError, OSError)               : pass
		except XTerminate                       : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

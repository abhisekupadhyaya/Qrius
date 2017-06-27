# coding: utf-8

import Preferences
from HIRES_DataType import DataPoint, DataSet

from app_hires     import GUI

from tcon        import TCON
from tcon        import LinkError as TCON_LinkError
from tcon        import CommError as TCON_CommError
from tcon        import ResourceError as TCON_ResourceError

from Cryostat_Constants import *

from xhires        import XHIRES
from xhires        import LinkError as XHIRES_LinkError
from xhires        import CommError as XHIRES_CommError
from xhires        import ResourceError as XHIRES_ResourceError

from XDict       import XDict
from XThread     import XTaskQueue, XThread, XThreadModule, XTerminate

# Importing Python provided libraries
import os
from threading   import Thread, RLock, Lock
from time        import time as systime, localtime, sleep
from Tkinter     import NORMAL, DISABLED, Toplevel

from HIRES_Constants import *
from HIRES_Method    import Method, XMethodError

from TCON_Constants import RUN_MODE_ISOTHERMAL   as TCON_RUN_MODE_ISOTHERMAL
from TCON_Constants import RUN_MODE_LINEAR_RAMP  as TCON_RUN_MODE_LINEAR_RAMP
from TCON_Constants import RUN_MODE_STEPPED_RAMP as TCON_RUN_MODE_STEPPED_RAMP

from XHIRES_Constants import RUN_MODE_IV    as XHIRES_RUN_MODE_IV
from XHIRES_Constants import RUN_MODE_RTime as XHIRES_RUN_MODE_RTime

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

	def refhiresh (self):
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

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def HIRES (master, oTCON, oXHIRES, sample, cryostat):

	if HIRES.singleton == None:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()

		oApp          = GUI (win, sample)
		HIRES.singleton = _HIRES (
			oApp, oTCON, oXHIRES, sample, cryostat)

	if master not in HIRES.master:
		HIRES.master.append (master)

	return HIRES.singleton

def closeHIRES (master):

	if master in HIRES.master:
		HIRES.master.remove (master)

	if len (HIRES.master) == 0 and HIRES.singleton:
		HIRES.singleton.close()
		HIRES.singleton = None

HIRES.singleton = None
HIRES.master    = []

class _HIRES:

	def __init__(self, oApp, oTCON, oXHIRES, sample, cryostat):

		self.oApp     = oApp
		self.oTCON    = oTCON
		self.oXHIRES  = oXHIRES
		self.sample   = sample
		self.cryostat = cryostat
		self.runMode  = RUN_MODE_RT_LINEAR_RAMP

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
		self.oApp.addXhiresMenu (self.oXHIRES.oApp.utilmenu)

	def show (self):
		win = self.oApp.master
		win.deiconify()
		win.lift()

	def hide (self):
		win = self.oApp.master
		win.withdraw()

	def wTCONCB (self):
		self.oTCON.show()

	def wXHIRESCB (self):
		self.oXHIRES.show()

	def close (self):

		oApplet = self.oApplet

		# Terminating acquisition thread
		if self.oAcqThread:
			self.oAcqThread.schedule_termination()
			while self.oAcqThread:
				sleep (0.05)
				self.oApplet.refhiresh()

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
		else                        : raise ValueError   (context)

	# +++++++++ Device control functions ++++++++++++++++++

	def openDevice (self, device):
		if   device == TCON_DEVICE : self.oTCON.show()
		elif device == XHIRES_DEVICE : self.oXHIRES.show()
		else                       : raise ValueError (device)

	# +++++++++ Acquisition functions ++++++++++++++++++

	def startRun (self, runMode):

		self.oApplet.setRunControlStatus (RUN_STARTING)

		try:
			thread = self.prepareAcquisition (runMode)
			thread.start()

		except (TCON_ResourceError, XHIRES_ResourceError, ResourceError) as e:
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
		xhires_prepmod = self.oXHIRES.prepareModule

		try:
			if self.oModule == None:

				if runMode == RUN_MODE_RT_LINEAR_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_LINEAR_RAMP)
					modXHIRES = xhires_prepmod (
						master, XHIRES_RUN_MODE_RTime)
					module = _RTLinearRampModule (
						master, self, modTCON, modXHIRES)

				elif runMode == RUN_MODE_RT_STEP_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_STEPPED_RAMP)
					modXHIRES = xhires_prepmod (
						master, XHIRES_RUN_MODE_RTime)
					module = _RTStepRampModule (
						master, self, modTCON, modXHIRES)

				elif runMode == RUN_MODE_IV_STEP_RAMP:
					modTCON = tcon_prepmod (
						master, TCON_RUN_MODE_STEPPED_RAMP)
					modXHIRES = xhires_prepmod (
						master, XHIRES_RUN_MODE_IV)
					module = _IVTStepRampModule (
						master, self, modTCON, modXHIRES)

				else:
					raise ResourceError (
						'HIRES_ResourceError: Module creation failed')

				self.oModule = module
				self.select_cryostat (runMode)

			else:
				raise ResourceError (
					'HIRES_ResourceError: Module unavailable')

		except (TCON_ResourceError, XHIRES_ResourceError):
			self.oTCON.releaseModule (self)
			self.oXHIRES.releaseModule (self)
			raise

		return module

	def releaseModule (self, caller):

		if self.oModule and caller == self.oModule.master:
			self.oTCON.releaseModule (caller)
			self.oXHIRES.releaseModule (caller)
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

				else:
					raise ResourceError (
						'HIRES_ResourceError: Thread creation failed')

				thread.atexit (self.acquisition_atexit)
				self.oAcqThread = thread

			else:
				raise ResourceError (
					'HIRES_ResourceError: Thread unavailable')

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
		method.set_XHIRES_Method (self.oXHIRES.getMethod())
		method.setRunMode (self.runMode)
		return method

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def applyMethod (self, method):

		oTCON   = self.oTCON
		oXHIRES   = self.oXHIRES
		oApplet = self.oApplet

		oTCON.applyMethod (method.get_TCON_Method (oTCON.getMethod()))
		oXHIRES.applyMethod (method.get_XHIRES_Method (oXHIRES.getMethod()))

		mode = method.getRunMode (self.runMode)
		oApplet.schedule_task (oApplet.setRunMode, mode)

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

	def select_cryostat (self, run_mode):

		insert_dict = {

			RUN_MODE_RT_LINEAR_RAMP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_RT_HIRES
			),

			RUN_MODE_RT_STEP_RAMP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_RT_HIRES
			),

			RUN_MODE_IV_STEP_RAMP : (
				CRYOSTAT_TYPE_GENERIC, INSERT_TYPE_RT_HIRES
			),
		}

		(cryostat_type, insert_type) = insert_dict.get (run_mode)

		self.cryostat.set_cryostat_type (cryostat_type)
		self.cryostat.set_insert_type   (insert_type)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Module (XThreadModule):

	def __init__ (self, master, oRes2, modTCON, modXHIRES):
		XThreadModule.__init__ (self, master)
		self.oRes2   = oRes2
		self.modTCON = modTCON
		self.modXHIRES = modXHIRES
		self.t0      = systime()
		self.dataset = DataSet()
		self.fd_log  = None

	# ++++ Useful functions used by derived classes ++++

	def run_type (self):
		return ''

	def xlabel (self):
		return ''

	def ylabel (self):
		return ''

	def folder_name (self):
		return 'hires'

	def init (self):

		oRes2   = self.oRes2
		oApplet = oRes2.oApplet

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
				self.xlabel(), self.ylabel())

			text = self.run_type() + ' started'
			oApplet.schedule_task (oApplet.set_status, text)
			oApplet.schedule_task (oApplet.setRunControlStatus, RUN_STARTED)

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
			('Heater temperature', 'K')
		]

		(sampleName, sampleID, sampleDescription) = self.oRes2.sample.get()
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
				1.0, 'K')
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
			('06 Heater Temperature', DATASET_COL_HEATER_TEMPERATURE, 'K')
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
			self.modXHIRES.do_tasks, bg_task, *bg_tasks)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _AcquisitionThread (XThread):

	def __init__ (self, module):
		XThread.__init__ (self, daemon = True)
		self.module = module

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RTLinearRampModule (_Module):

	def __init__ (self, master, oRes2, modTCON, modXHIRES):
		_Module.__init__ (self, master, oRes2, modTCON, modXHIRES)

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
		self.modXHIRES.init()

	def atexit (self):
		self.modXHIRES.atexit()
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

				xhires_datapoint = (
					self.modXHIRES.acquire_n_plot (
						self.do_tasks, bg_task, *bg_tasks))

				datapoint = DataPoint (
					time              = systime() - self.t0,
					current           = xhires_datapoint.current,
					voltage           = xhires_datapoint.voltage,
					resistance        = xhires_datapoint.resistance,
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

		except (XHIRES_CommError, XHIRES_LinkError) as e:
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
		except (XHIRES_LinkError, XHIRES_CommError) : pass
		except (IOError, OSError)               : pass
		except XTerminate                       : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RTStepRampModule (_Module):

	def __init__ (self, master, oRes2, modTCON, modXHIRES):
		_Module.__init__ (self, master, oRes2, modTCON, modXHIRES)

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
		self.modXHIRES.init()

	def atexit (self):
		self.modXHIRES.atexit()
		self.modTCON.atexit()
		_Module.atexit (self)

	def complete (self):
		return True if self.modTCON.complete() else False

	def stabilize_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oRes2.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			self.modTCON.set_n_stabilize (self.do_tasks, bg_task, *bg_tasks)
			if not self.modTCON.complete():

				tcon_datapoint = self.modTCON.acquire_n_plot()
				xhires_datapoint = self.modXHIRES.acquire_n_plot (
					self.do_tasks, bg_task, *bg_tasks)

				datapoint = DataPoint (
					time              = systime() - self.t0,
					current           = xhires_datapoint.current,
					voltage           = xhires_datapoint.voltage,
					resistance        = xhires_datapoint.resistance,
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

		except (XHIRES_CommError, XHIRES_LinkError) as e:
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
		except (XHIRES_LinkError, XHIRES_CommError) : pass
		except (IOError, OSError)               : pass
		except XTerminate                       : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _IVTStepRampModule (_Module):

	def __init__ (self, master, oRes2, modTCON, modXHIRES):
		_Module.__init__ (self, master, oRes2, modTCON, modXHIRES)

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
		if self.modXHIRES.is_alive() : self.modXHIRES.atexit()
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

			self.modTCON.set_n_stabilize (self.do_tasks, bg_task, *bg_tasks)
			if not self.modTCON.complete():

				self.modXHIRES.init()

				while True:

					self.do_tasks (bg_task, *bg_tasks)
					tcon_datapoint = self.modTCON.acquire_n_plot()
					xhires_datapoint, breakPlot = self.modXHIRES.excite_n_plot (
						self.do_tasks, bg_task, *bg_tasks)

					if breakPlot:
						dataset.append (self.breakPlot())

					if not self.modXHIRES.complete():
						datapoint = DataPoint (
							time              = systime() - self.t0,
							current           = xhires_datapoint.current,
							voltage           = xhires_datapoint.voltage,
							resistance        = xhires_datapoint.resistance,
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

				self.modXHIRES.atexit()

		except (TCON_CommError, TCON_LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (XHIRES_CommError, XHIRES_LinkError) as e:
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
		except (XHIRES_LinkError, XHIRES_CommError) : pass
		except (IOError, OSError)               : pass
		except XTerminate                       : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

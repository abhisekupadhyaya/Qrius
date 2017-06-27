import os

from math import isnan

from threading   import RLock, Lock
from time        import time as systime, localtime, sleep
from Tkinter     import NORMAL, DISABLED, Toplevel

import libxmc

from Preferences import get_XMC_serialNo
from Preferences import getDataFolder

from XMC_Constants import *
from XMC_DataType  import DataPoint, DataSet

from appXMC import GUI
from appXMC import GUI_MoveAbsoluteTool
from appXMC import GUI_MoveRelativeTool
from appXMC import GUI_PitchSetting
from appXMC import GUI_MCStatusDisplay

from Plot2D      import Plot2D
from XDict       import XDict
from XThread     import XTaskQueue, XThread, XTerminate, XThreadModule

class LinkError     (Exception): pass
class CommError     (Exception): pass
class StallError    (Exception): pass
class ResourceError (Exception): pass

# _serialNo = 'QTXU1LO4A'

# ++++ Driver singleton creation

def Driver():

	if Driver.singleton == None:
		Driver.singleton = _Driver()

	return Driver.singleton

Driver.singleton = None

# ++++ Driver wrapper

class _Driver:

	def __init__ (self, orientation = 1):
		self._thlock     = RLock()
		self._deviceID = None
		self._state    = None
		self._position = None
		self._remainingDistance = None
		self._orientation = orientation

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquire_lock (self):
		self._thlock.acquire()

	def release_lock (self):
		self._thlock.release()

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def scan (self):

		serialNos = []
		N = libxmc.scan()
		for i in range (0, N):
			serialNos.append (libxmc.serialNo (i))

		return serialNos

	def open (self, serialNo):

		if serialNo in self.scan():

			self._deviceID, goodID, hardware, timeout = (
				libxmc.open_device (serialNo, COMM_TIMEOUT_INTERVAL))

			if timeout != 0.0 and goodID:
				self.do_callback (DEVICE_CONNECTED)

			else:
				libxmc.close_device (self._deviceID)
				self._deviceID = None
				self.do_callback (DEVICE_NOT_FOUND)

		else:
			self.do_callback (DEVICE_NOT_FOUND)

	def close (self):

		if self._deviceID != None:

			libxmc.close_device (self._deviceID)
			self._deviceID = None
			self._position = None
			self.do_callback (DEVICE_DISCONNECTED)

	def check_connected (self):
		if self._deviceID == None:
			raise LinkError ('XMC_LinkError: Device not connected')

	def check_timeout (self, timeout, context = ''):
		if (timeout == 0.0):
			self.close()
			raise CommError ('XMC_CommError: ' + str (context))

	def check_stall (self, stalled):
		if stalled:
			raise StallError ('XMC_StallError: SAMPLE POSITIONER JAMMED !!!')

	def linacStatus (self):

		self.check_connected()

		(state, position, remainingDistance, stalled, timeout) = (
			libxmc.linacStatus (self._deviceID, COMM_TIMEOUT_INTERVAL))

		self.check_timeout (timeout, "Get linear actuator status")
		self.check_stall (stalled)

		self._state = {
			0 : MC_STATE_IDLE,
			1 : MC_STATE_RESET,
			2 : MC_STATE_MOVE_UP,
			3 : MC_STATE_MOVE_DOWN
		}.get (state)

		self._position = position
		self._remainingDistance = remainingDistance

		self.do_callback (DEVICE_STATUS,
							self._state,
							self._orientation * self._position,
							self._orientation * self._remainingDistance)

		return (self._state,
				self._orientation * self._position,
				self._orientation * self._remainingDistance)

	def linacMove (self, distance):

		self.check_connected()

		(state, position, remainingDistance, stalled, timeout) = (
			libxmc.linacMove (self._deviceID,
				self._orientation * distance, COMM_TIMEOUT_INTERVAL))

		self.check_timeout (timeout, "Move linear actuator")

		self._state = {
			0 : MC_STATE_IDLE,
			1 : MC_STATE_RESET,
			2 : MC_STATE_MOVE_UP,
			3 : MC_STATE_MOVE_DOWN
		}.get (state)

		self._position = position
		self._remainingDistance = remainingDistance

		self.do_callback (DEVICE_MOVING,
							self._state,
							self._orientation * self._position,
							self._orientation * self._remainingDistance)

		return (self._state,
				self._orientation * self._position,
				self._orientation * self._remainingDistance)

	def linacGoto (self, position):

		self.check_connected()

		(state, position, remainingDistance, stalled, timeout) = (
			libxmc.linacGoto (self._deviceID,
				self._orientation * position, COMM_TIMEOUT_INTERVAL))

		self.check_timeout (timeout, "Position linear actuator")

		self._state = {
			0 : MC_STATE_IDLE,
			1 : MC_STATE_RESET,
			2 : MC_STATE_MOVE_UP,
			3 : MC_STATE_MOVE_DOWN
		}.get (state)

		self._position = position
		self._remainingDistance = remainingDistance

		self.do_callback (DEVICE_MOVING,
							self._state,
							self._orientation * self._position,
							self._orientation * self._remainingDistance)

		return (self._state,
				self._orientation * self._position,
				self._orientation * self._remainingDistance)

	def setPitch (self, pitch):
		self.check_connected()
		self.do_callback (DEVICE_PITCH_SET, pitch)

	def reset (self):

		self.check_connected()

		(state, position, remainingDistance, stalled, timeout) = (
			libxmc.linacReset (self._deviceID, COMM_TIMEOUT_INTERVAL))

		self.check_timeout (timeout, "Reset linear actuator")

		self._state = {
			0 : MC_STATE_IDLE,
			1 : MC_STATE_RESET,
			2 : MC_STATE_MOVE_UP,
			3 : MC_STATE_MOVE_DOWN
		}.get (state)

		self._position = position
		self._remainingDistance = remainingDistance

		self.do_callback (DEVICE_RESET,
							self._state,
							self._orientation * self._position,
							self._orientation * self._remainingDistance)

		return (self._state,
				self._orientation * self._position,
				self._orientation * self._remainingDistance)

	def stop (self):

		self.check_connected()

		(state, position, remainingDistance, stalled, timeout) = (
			libxmc.linacStop (self._deviceID, COMM_TIMEOUT_INTERVAL))

		self.check_timeout (timeout, "Stop linear actuator")

		self._state = {
			0 : MC_STATE_IDLE,
			1 : MC_STATE_RESET,
			2 : MC_STATE_MOVE_UP,
			3 : MC_STATE_MOVE_DOWN
		}.get (state)

		self._position = position
		self._remainingDistance = remainingDistance

		self.do_callback (DEVICE_STOPPED,
							self._state,
							self._orientation * self._position,
							self._orientation * self._remainingDistance)

		return (self._state,
				self._orientation * self._position,
				self._orientation * self._remainingDistance)

class _Applet:

	def __init__ (self, oXMC):

		self.oXMC = oXMC
		self._plots = {}
		self._taskq = XTaskQueue()
		self._lastPlotUpdateAt = 0.0
		self._hApplet = self.oXMC.oApp.master.after (50, self._applet)

	def _applet (self):

		self._taskq.process()
		oApp = self.oXMC.oApp

		t = systime()
		if t >= self._lastPlotUpdateAt + 2:
			self._lastPlotUpdateAt = t

			for (wPlot, trace) in self._plots.values():
				if wPlot.damaged() : wPlot.redraw()

		self._hApplet = oApp.master.after (50, self._applet)

	def schedule_task (self, task, *args):
		self._taskq.push (task, *args)

	def setConnectionStatus (self, status):
		self.oXMC.oApp.setConnectionStatus (status)

	def setRunControlStatus (self, status):
		self.oXMC.oApp.setRunControlStatus (status)

	def setRunMode (self, runMode):
		self.oXMC.oApp.setRunMode (runMode)
		self.oXMC.runMode = runMode

	def refresh (self):
		self.oXMC.oApp.master.update()

	def close (self):
		oApp = self.oXMC.oApp
		oApp.close()
		oApp.master.after_cancel (self._hApplet)
		oApp.master.destroy()

	# +++++++++++++ GUI set functions +++++++++++++++

	def setProgressBarLimits (self, position, destination):
		lvalue = [position, destination][position > destination]
		rvalue = [position, destination][position < destination]
		self.oXMC.oApp.setMCProgressBarMin (lvalue)
		self.oXMC.oApp.setMCProgressBarMax (rvalue)

	def setDisplayedParameters (self, state, position, remainingDistance):
		self.oXMC.oApp.setMCStatusDisplay (state, position, remainingDistance)
		self.oXMC.oApp.setMCProgressBarDisplay (position)
		self.oXMC.status.set (state, position, remainingDistance)

	def setStatusJammed (self):
		self.oXMC.oApp.setStatusJammed()

	def setPitchSetting (self, pitch):
		self.oXMC.pitch = pitch

	def initPlot (self, thread, title, xlabel, ylabel):
		oApp = self.oXMC.oApp
		wPlot = oApp.newPlot (title)
		wPlot.xlabel (xlabel)
		wPlot.ylabel (ylabel)
		trace = wPlot.new_dataset ('k-')
		wPlot.damage()
		self._plots[thread] = (wPlot, trace)

	def updatePlot (self, thread, time, position):
		(wPlot, trace) = self._plots[thread]
		wPlot.add_datapoint (trace, time, position)
		wPlot.damage()

	def clearPlot (self):
		oApp = self.oXMC.oApp
		oApp.clearPlot()
		self._plots.clear()

	def set_status (self, text):
		self.oXMC.oApp.set_status (text)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquisition_atexit (self):
		self.oXMC.releaseAcquisition()

	def devicethread_atexit (self):
		self.oXMC.releaseDeviceThread();

class _DeviceThread (XThread):

	def __init__ (self, oXMC):

		XThread.__init__ (self, daemon = True)

		self.t0 = systime()
		self.oXMC = oXMC
		self.oXMC.oDriver.callback (self.driverCB)
		self._stalled = False

	def sleep (self, duration, bg_task = None, *bg_tasks):
		entry = systime()
		self.do_tasks (bg_task, *bg_tasks)
		while systime() < entry + duration:
			sleep (0.05)
			self.do_tasks (bg_task, *bg_tasks)

	def thread (self):

		oXMC    = self.oXMC
		oApplet = oXMC.oApplet

		while True:

			try:

				while True:
					self.do_tasks()
					self.sleep (0.5, self.do_tasks)
					self.check()

			except LinkError       : pass
			except CommError as e  :
				oApplet.schedule_task (oApplet.set_status, str (e))

			except StallError as e : self.report_stall (e)
			except XTerminate      : break

		self.disconnectDevice()

	def check (self):

		oDriver = self.oXMC.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.linacStatus()
			self._stalled = False

		finally:
			oDriver.release_lock()

	def report_stall (self, e):
		if not self._stalled:
			self._stalled = True
			oApplet = self.oXMC.oApplet
			oApplet.schedule_task (oApplet.set_status, str (e))
			oApplet.schedule_task (oApplet.setStatusJammed)

	def driverCB (self, context, *args):

		oApplet = self.oXMC.oApplet

		if context == DEVICE_CONNECTED:
			oApplet.schedule_task (
				oApplet.setConnectionStatus, DEVICE_CONNECTED)

		elif context == DEVICE_NOT_FOUND:
			oApplet.schedule_task (
				oApplet.setConnectionStatus, DEVICE_NOT_FOUND)

		elif context == DEVICE_DISCONNECTED:
			oApplet.schedule_task (
				oApplet.setConnectionStatus, DEVICE_DISCONNECTED)

		elif context == DEVICE_RESET     : self.deviceResetCB   (*args)
		elif context == DEVICE_MOVING    : self.deviceMovingCB  (*args)
		elif context == DEVICE_PITCH_SET : pass
		elif context == DEVICE_STOPPED   : self.deviceStoppedCB (*args)
		elif context == DEVICE_STATUS    : self.deviceStatusCB  (*args)

	def deviceResetCB (self, state, position, remainingDistance):

		oApplet = self.oXMC.oApplet

		text = 'Reseting to top ...'
		oApplet.schedule_task (oApplet.set_status, text)

		if isnan (position):
			position = remainingDistance = 0

		destination = position + remainingDistance

		oApplet.schedule_task (
			oApplet.setProgressBarLimits, position, destination)

		oApplet.schedule_task (
			oApplet.setDisplayedParameters,
			state, position, remainingDistance)

	def deviceMovingCB (self, state, position, remainingDistance):

		oApplet = self.oXMC.oApplet

		if isnan (position):
			position = remainingDistance = 0

		destination = position + remainingDistance

		text = 'Moving to ' + str (
			'%.1f' % (destination * m_to_mm)) + ' mm ...'

		oApplet.schedule_task (oApplet.set_status, text)

		oApplet.schedule_task (
			oApplet.setProgressBarLimits, position, destination)

		oApplet.schedule_task (
			oApplet.setDisplayedParameters,
			state, position, remainingDistance)

	def deviceStoppedCB (self, state, position, remainingDistance):

		oApplet = self.oXMC.oApplet

		text = 'Stopped'
		oApplet.schedule_task (oApplet.set_status, text)

		if isnan (position):
			position = remainingDistance = 0

		oApplet.schedule_task (
			oApplet.setDisplayedParameters,
			state, position, remainingDistance)

	def deviceStatusCB (self, state, position, remainingDistance):

		oApplet = self.oXMC.oApplet

		if isnan (position):
			position = remainingDistance = 0

		oApplet.schedule_task (
			oApplet.setDisplayedParameters,
			state, position, remainingDistance)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def connectDevice (self):

		oApplet = self.oXMC.oApplet
		oDriver = self.oXMC.oDriver
		oApplet.schedule_task (oApplet.setConnectionStatus, DEVICE_CONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.open (get_XMC_serialNo())

			self._stalled = False
			(state, position, remainingDistance) = oDriver.linacStatus()
			if isnan (position) : oDriver.reset()

		except StallError:
			oDriver.reset()

		finally:
			oDriver.release_lock()

	def disconnectDevice (self):

		oApplet = self.oXMC.oApplet
		oDriver = self.oXMC.oDriver
		oApplet.schedule_task (
			oApplet.setConnectionStatus, DEVICE_DISCONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.close()

		finally:
			oDriver.release_lock()

	def resetDevice (self):

		oDriver = self.oXMC.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.reset()

		finally:
			oDriver.release_lock()

	def stopDevice (self):

		oDriver = self.oXMC.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.stop()

		finally:
			oDriver.release_lock()

	def setPitchSetting (self, pitch):

		oDriver = self.oXMC.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.setPitch (pitch)

		finally:
			oDriver.release_lock()

	def setMoveAbsolute (self, position):

		oDriver = self.oXMC.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.linacGoto (position)

		finally:
			oDriver.release_lock()

	def setMoveRelative (self, distance):

		oDriver = self.oXMC.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.linacMove (distance)

		finally:
			oDriver.release_lock()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Module (XThreadModule):

	def __init__ (self, master, oXMC):
		XThreadModule.__init__ (self, master)
		self.oXMC    = oXMC
		self.t0      = systime()
		self.dataset = DataSet()
		self.fd_log  = None

	# ++++ Useful functions used by derived classes ++++

	'''
		Redefine these in the derived class
		to set run-specific folder name and extension.
	'''

	def folder_name (self):
		return 'xmc'

	def run_type (self):
		return ''

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Position (mm)'

	def init (self):

		oXMC   = self.oXMC
		oApplet = oXMC.oApplet

		try:
			self.filename = self.get_timestamp()
			oApplet.schedule_task (oApplet.setRunControlStatus, RUN_STARTING)

			self.t0 = systime()
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

		oXMC    = self.oXMC
		oApplet = oXMC.oApplet
		oApplet.schedule_task (oApplet.setRunControlStatus, RUN_FINISHING)

		# Save acquired run
		try:

			if not self.dataset.empty():

				save_path = self.save (self.dataset)

				text = 'Data saved at ' + save_path
				oApplet.schedule_task (oApplet.set_status, text)

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)

		self.close_log()

		text = 'Run finished'
		oApplet.schedule_task (oApplet.set_status, text)
		oApplet.schedule_task (oApplet.setRunControlStatus, RUN_FINISHED)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquire_datapoint (self, bg_task, *bg_tasks):

		oDriver = self.oXMC.oDriver
		self.do_tasks (bg_task, *bg_tasks)

		try:
			oDriver.acquire_lock()
			(state, position, remainingDistance) = oDriver.linacStatus()

		finally:
			oDriver.release_lock()

		return (state, DataPoint (
			time     = systime() - self.t0,
			position = position))

	def sleep (self, duration, bg_task = None, *bg_tasks):
		entry = systime()
		self.do_tasks (bg_task, *bg_tasks)
		while systime() < entry + duration:
			sleep (0.05)
			self.do_tasks (bg_task, *bg_tasks)

	# ++++ Logging functions ++++

	def open_log (self):

		(self.fd_log, full_path) = self.open_file (
			self.filename + '_' + self.run_type(), 'csv', 'w')

		fields = [
			('01 Time',              'sec'),
			('02 Sample Position',    'mm')
		]

		(sampleName, sampleID, sampleDescription) = self.oXMC.sample.get()
		self.fd_log.write ('#Sample name        : ' + sampleName        + '\n')
		self.fd_log.write ('#Sample ID          : ' + sampleID          + '\n')

		label =            '#Sample description : '
		sampleDescription = sampleDescription.replace ('\n', '\n' + label)
		self.fd_log.write (label + sampleDescription + '\n')

		text = ''
		for field in fields:
			(name, unit) = field
			text += name + ','
		self.fd_log.write ('#' + text + '\n')

		text = ''
		for field in fields:
			(name, unit) = field
			text += unit + ','
		self.fd_log.write ('#' + text + '\n')

		self.fd_log.flush()
		return full_path

	def update_log (self, datapoint):

		fields = [
			('Time',
				'%-.1f', datapoint.time,
				1.0, 'sec'),

			('Sample position',
				'%-.1f', datapoint.position,
				1e3, 'mm')
		]

		text = ''
		for field in fields:
			(name, fmt, value, mult, unit) = field
			text += (
				str ('%-25s' % name) + ' : ' +
				str (fmt % (value * mult)) +
				' ' + unit + '\n')

		print text

		'''
			Writes to file
		'''
		text = ''
		for field in fields:
			(name, fmt, value, mult, unit) = field
			text += str ('%e' % value) + ','

		self.fd_log.write (text + '\n')
		self.fd_log.flush()

	def close_log (self):

		if self.fd_log != None:
			self.fd_log.close()

		self.fd_log = None

	def save (self, dataset):

		dict = XDict()
		dict.set_sample (self.oXMC.sample.get())

		fields = [
			('01 Time',               DATASET_COL_TIME,     1.0, 'sec'),
			('02 Sample Position',    DATASET_COL_POSITION, 1.0, 'm' )
		]

		for (key, col, mult, unit) in fields:
			data = [mult * datum for datum in dataset.getColumn (col)]
			dict.set_data (key, data, unit)

		(fd, full_path) = self.open_file (
			self.filename + '_' + self.run_type(), 'xpl', 'w')

		dict.save (fd)
		fd.close()

		return full_path

	def open_file (self, file_name, file_ext, open_mode):

		(sampleName, sampleID, _) = self.oXMC.sample.get()

		folder = os.path.join (getDataFolder(),
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

class _AcquisitionThread (XThread):

	def __init__ (self, module):
		XThread.__init__ (self, daemon = True)
		self.module = module

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _MonitorModule (_Module):

	def __init__ (self, master, oXMC):
		_Module.__init__(self, master, oXMC)

	def run_type (self):
		return 'Monitor'

	def init (self):
		_Module.init (self)
		oApplet = self.oXMC.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_MONITOR)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oXMC   = self.oXMC
		oApplet = oXMC.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			(state, datapoint) = self.acquire_datapoint (
				self.do_tasks, bg_task, *bg_tasks)

			self.update_log (datapoint)
			self.dataset.append (datapoint)
			oApplet.schedule_task (
				oApplet.updatePlot, self,
				datapoint.time, datapoint.position * m_to_mm)

		except CommError as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

	def reset (self, bg_task = None, *bg_tasks):

		oXMC    = self.oXMC
		oDriver = oXMC.oDriver
		oApplet = oXMC.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			try:
				oDriver.acquire_lock()
				(state, position, remainingDistance) = oDriver.reset()

				time = systime() - self.t0
				oApplet.schedule_task (
					oApplet.updatePlot, self, time, position * m_to_mm)

			finally:
				oDriver.release_lock()

			(state, datapoint) = self.acquire_datapoint (
				self.do_tasks, bg_task, *bg_tasks)

			while state != MC_STATE_IDLE:

				self.sleep (1, self.do_tasks, bg_task, *bg_tasks)

				(state, datapoint) = (
					self.acquire_datapoint (
						self.do_tasks, bg_task, *bg_tasks))

				self.update_log (datapoint)
				self.dataset.append (datapoint)
				oApplet.schedule_task (
					oApplet.updatePlot, self,
					datapoint.time, datapoint.position * m_to_mm)

		except CommError as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		return datapoint

	def goto (self, position, bg_task = None, *bg_tasks):

		oXMC    = self.oXMC
		oDriver = oXMC.oDriver
		oApplet = oXMC.oApplet

		self.do_tasks (bg_task, *bg_tasks)

		try:

			try:
				oDriver.acquire_lock()

				(state, position, remainingDistance) = \
					oDriver.linacGoto (position)

				time = systime() - self.t0
				oApplet.schedule_task (
					oApplet.updatePlot, self, time, position * m_to_mm)

			finally:
				oDriver.release_lock()

			(state, datapoint) = self.acquire_datapoint (
				self.do_tasks, bg_task, *bg_tasks)

			while state != MC_STATE_IDLE:

				self.sleep (1, self.do_tasks, bg_task, *bg_tasks)

				(state, datapoint) = self.acquire_datapoint (
					self.do_tasks, bg_task, *bg_tasks)

				self.update_log (datapoint)
				self.dataset.append (datapoint)
				oApplet.schedule_task (
					oApplet.updatePlot, self,
					datapoint.time, datapoint.position * m_to_mm)

		except CommError as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		return datapoint

	def move (self, distance, bg_task = None, *bg_tasks):

		oXMC    = self.oXMC
		oDriver = oXMC.oDriver
		oApplet = oXMC.oApplet

		self.do_tasks (bg_task, *bg_tasks)

		try:

			try:
				oDriver.acquire_lock()
				(state, position, remainingDistance) = \
					oDriver.linacMove (distance)

				time = systime() - self.t0
				oApplet.schedule_task (
					oApplet.updatePlot, self, time, position * m_to_mm)

			finally:
				oDriver.release_lock()

			(state, datapoint) = self.acquire_datapoint (
				self.do_tasks, bg_task, *bg_tasks)

			while state != MC_STATE_IDLE:

				self.sleep (1, self.do_tasks, bg_task, *bg_tasks)

				(state, datapoint) = self.acquire_datapoint (
					self.do_tasks, bg_task, *bg_tasks)

				self.update_log (datapoint)
				self.dataset.append (datapoint)
				oApplet.schedule_task (
					oApplet.updatePlot, self,
					datapoint.time, datapoint.position * m_to_mm)

		except CommError as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		return datapoint

class _MonitorThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:

			self.module.init()

			while True:

				self.do_tasks()
				self.module.sleep (1, self.do_tasks)
				self.module.acquire_n_plot (self.do_tasks)

		except (CommError, LinkError, StallError): pass
		except (IOError, OSError): pass
		except XTerminate: pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def XMC (master, sample):

	if XMC.singleton == None:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()

		oApp          = GUI (win, sample)
		XMC.singleton = _XMC (oApp, sample)

	if master not in XMC.master:
		XMC.master.append (master)

	return XMC.singleton

def closeXMC (master):

	if master in XMC.master:
		XMC.master.remove (master)

	if len (XMC.master) == 0 and XMC.singleton:
		XMC.singleton.close()
		XMC.singleton = None

XMC.singleton = None
XMC.master    = []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Status:

	def __init__ (self):
		self.state      		= MC_STATE_IDLE
		self.position   		= 0.0
		self.remainingDistance  = 0.0

	def set (self, state, position, remainingDistance):
		self.state		       = state
		self.position          = position
		self.remainingDistance = remainingDistance

	def get (self):
		return (self.state, self.position, self.remainingDistance)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XMC:

	def __init__ (self, oApp, sample):

		self.oApp   = oApp
		self.sample = sample
		self.oApp.callback (self.oAppCB)

		self.oDriver  = Driver()

		# ++++ Private variables ++++
		self.lastMoveRelative = 0.0
		self.pitch            = 1.25e-3

		# ++++ Controller status ++++
		self.status = _Status()

		# ++++ Run control ++++
		self.runMode = RUN_MODE_MONITOR

		# ++++ Support for multi-threading ++++

		self._thlock       = RLock()
		self.oApplet       = _Applet (self)
		self.oDeviceThread = None
		self.oModule       = None
		self.oAcqThread    = None

		try:
			thread = self.prepareDeviceThread()
			thread.start()

		except ResourceError as e:
			self.oApplet.set_status (str (e))

		# ++++ Attempt for auto-connect ++++

		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.setRunMode, self.runMode)
		self.connectDevice()

	def show (self):
		win = self.oApp.master
		win.deiconify()
		win.lift()

	def hide (self):
		win = self.oApp.master
		win.withdraw()

	def acquire_lock (self):
		self._thlock.acquire()

	def release_lock (self):
		self._thlock.release()

	def close (self):

		oApplet = self.oApplet

		# Terminating acquisition thread
		if self.oAcqThread:
			self.oAcqThread.schedule_termination()
			while self.oAcqThread:
				sleep (0.05)
				self.oApplet.refresh()

		# Terminating device thread
		if self.oDeviceThread:
			self.oDeviceThread.schedule_termination()
			while self.oDeviceThread:
				sleep (0.05)
				self.oApplet.refresh()

		# Closing GUI
		self.oApplet.close()

	# ++++ Device thread ctor/dtor ++++

	def devicethread_atexit (self):
		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.devicethread_atexit)

	def prepareDeviceThread (self):

		thread  = None

		if self.oDeviceThread == None:

			thread = _DeviceThread (self)
			thread.atexit (self.devicethread_atexit)
			self.oDeviceThread = thread

		else:
			raise ResourceError (
				'XMC_ResourceError: Device thread unavailable')

		return thread

	def releaseDeviceThread (self):
		self.oDeviceThread = None

	# ++++ GUI callback ++++

	def oAppCB (self, context, *args):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		if   context == CONNECT_DEVICE    : self.connectDevice()
		elif context == DISCONNECT_DEVICE : self.disconnectDevice()
		elif context == RUN_MODE          : self.oApplet.setRunMode (*args)
		elif context == START_RUN         : self.startRun (*args)
		elif context == FINISH_RUN        : self.finishRun()
		elif context == RESET_DEVICE 	  : self.resetDevice()
		elif context == STOP_DEVICE 	  : self.stopDevice()
		elif context == OPEN_DIALOG       : self.openDialog (*args)
		else                              : raise ValueError (context)

	# ---------------- Connection functions ----------------------

	def connectDevice (self):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		oApplet.setConnectionStatus (DEVICE_CONNECTING)
		oDeviceThread.schedule_task (oDeviceThread.connectDevice)

	def disconnectDevice (self):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		oApplet.setConnectionStatus (DEVICE_DISCONNECTING)
		oDeviceThread.schedule_task (oDeviceThread.disconnectDevice)

	def resetDevice (self):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread
		oDeviceThread.schedule_task (oDeviceThread.resetDevice)

	def stopDevice (self):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread
		oDeviceThread.schedule_task (oDeviceThread.stopDevice)

	# +++++++++ Acquisition functions ++++++++++++++++++

	def startRun (self, runMode):

		self.oApplet.setRunControlStatus (RUN_STARTING)

		try:
			thread = self.prepareAcquisition (runMode)
			thread.start()

		except ResourceError as e:
			self.oApplet.set_status (str (e))
			self.oApplet.setRunControlStatus (RUN_FINISHED)

	def finishRun (self):

		if self.oAcqThread:
			self.oApplet.setRunControlStatus (RUN_FINISHING)
			self.oAcqThread.schedule_termination()
		else:
			text = 'Cannot stop! Running in slave mode.'
			self.oApplet.set_status (text)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareModule (self, master, runMode):

		module = None
		oXMC   = self

		if self.oModule == None:

			if runMode == RUN_MODE_MONITOR:
				module = _MonitorModule (master, oXMC)

			else:
				raise ('Module creation failed')

			self.oModule = module

		else:
			raise ResourceError (
				'XMC_ResourceError: Module unavailable')

		return module

	def releaseModule (self, caller):
		if self.oModule and caller == self.oModule.master:
			self.oModule = None

	# +++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareAcquisition (self, runMode):

		thread = None
		master = self

		try:

			if self.oAcqThread == None:

				module = self.prepareModule (master, runMode)

				if runMode == RUN_MODE_MONITOR:
					thread = _MonitorThread (module)

				else:
					raise ResourceError (
						'XMC_ResourceError: Thread creation failed')

				thread.atexit (self.acquisition_atexit)
				self.oAcqThread = thread

			else:
				raise ResourceError (
					'XMC_ResourceError: Thread unavailable')

		except ResourceError:
			self.releaseModule (self)

		return thread

	def acquisition_atexit (self):
		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.acquisition_atexit)

	def releaseAcquisition (self):
		self.releaseModule (self)
		self.oAcqThread = None

	# ++++++++ Settings and Tools dialog callback functions ++++++++

	def openDialog (self, dialog):
		if   dialog == PITCH_SETTING_DIALOG : self.openPitchSettingDialog()
		elif dialog == MOVE_ABSOLUTE_DIALOG : self.openMoveAbsoluteDialog()
		elif dialog == MOVE_RELATIVE_DIALOG : self.openMoveRelativeDialog()
		else                                : raise ValueError (dialog)

	def openPitchSettingDialog (self):

		w = self.dialog = GUI_PitchSetting (
			Toplevel (takefocus = True), self.pitch)

		w.callback (self.pitchSettingDialogCB)

		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def pitchSettingDialogCB (self, context, *args):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		if context == APPLY:
			(pitch,) = args
			oDeviceThread.schedule_task (oDeviceThread.setPitchSetting, pitch)
			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	def openMoveAbsoluteDialog (self):

		(state, position, remainingDistance) = self.status.get()

		w = self.dialog = GUI_MoveAbsoluteTool (
			Toplevel (takefocus = True), position + remainingDistance)

		w.callback (self.moveAbsoluteDialogCB)

		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def moveAbsoluteDialogCB (self, context, *args):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		if context == APPLY:
			oDeviceThread.schedule_task (oDeviceThread.setMoveAbsolute, *args)
			self.dialog.master.destroy()
			self.dialog = None

		elif context == ENTER:
			oDeviceThread.schedule_task (oDeviceThread.setMoveAbsolute, *args)

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	def openMoveRelativeDialog (self):

		w = self.dialog = GUI_MoveRelativeTool (
			Toplevel (takefocus = True), self.lastMoveRelative)

		w.callback (self.moveRelativeDialogCB)

		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def moveRelativeDialogCB (self, context, *args):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		if context == APPLY:
			self.lastMoveRelative = args[0]
			oDeviceThread.schedule_task (oDeviceThread.setMoveRelative, *args)
			self.dialog.master.destroy()
			self.dialog = None

		elif context == ENTER:
			self.lastMoveRelative = args[0]
			oDeviceThread.schedule_task (oDeviceThread.setMoveRelative, *args)

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

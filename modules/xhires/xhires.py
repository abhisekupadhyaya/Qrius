# coding: utf-8
import libxhires

from app_xhires	   import GUI
from app_xhires	   import GUI_SourceParameters
from app_xhires	   import GUI_MeterParameters
from app_xhires	   import GUI_AcquisitionSettings
from app_xhires	   import GUI_IVRampSettings
from app_xhires	   import GUI_OhmmeterSettings

from XHIRES_DataType	import DataPoint, DataSet
from XHIRES_Method		import Method, XMethodError

from XDict			import XDict
from XThread		import XTaskQueue, XThread, XThreadModule, XTerminate
from Preferences	import get_XHIRES_serialNo, getDataFolder

# Importing Python provided libraries
import os
from threading		import Thread, RLock, Lock
from time			import time as systime, localtime, sleep
from Tkinter		import Toplevel
from math			import copysign, sqrt

from XHIRES_Constants import *

def Driver():

	if Driver.singleton == None:
		Driver.singleton = _Driver()

	return Driver.singleton

Driver.singleton = None

class LinkError	 (Exception) : pass
class CommError	 (Exception) : pass
class ResourceError (Exception) : pass

class _Driver:

	def __init__ (self):
		self._thlock = RLock()

		self.deviceID = None
		self.vs_range = None
		self.vm_range = None
		self.cm_range = None
		self.vs_value = None

		self.cm_autorange  = True
		self.vm_autorange  = True
		self.vs_autorange = True

		self._retry = RETRY
		self.vs_active = None

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def callback (self, cb):
		self._callback = cb
		if not self._callback:
			delattr (self, '_callback')

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def scan (self):

		serialNos = []
		number_of_devices = libxhires.scan()
		for i in range (0, number_of_devices):
			serialNos.append (libxhires.serialNo (i))

		return serialNos

	def open (self, serialNo):

		if serialNo in self.scan():

			self.deviceID, goodID, timeout = (
				libxhires.open_device (serialNo, COMM_TIMEOUT_INTERVAL))

			if timeout != 0.0 and goodID:
				self.do_callback (DEVICE_CONNECTED)
				self._VS_activate ()
			else:
				libxhires.close_device (self.deviceID)
				self.deviceID = None
				self.do_callback (DEVICE_NOT_FOUND)

		else:
			self.do_callback (DEVICE_NOT_FOUND)

	def close (self):

		if self.deviceID != None:

			self._VS_deactivate ()
			libxhires.close_device (self.deviceID)

			self.deviceID = None
			self.vs_range = None
			self.vm_range = None
			self.cm_range = None
			self.vs_value = None
			self.vs_active = None

			self.do_callback (DEVICE_DISCONNECTED)

	def check_connected (self):
		if self.deviceID == None:
			raise LinkError ('XHIRES_LinkError: Device not connected')

	def check_timeout (self, timeout, context = ''):
		if (timeout == 0.0):
			self.close()
			raise CommError ('XHIRES_CommError: ' + str (context))

	def _VS_setRange (self, range):

		self.check_connected()

		if self.vs_range == None or self.vs_range != range:

			range, timeout = libxhires.VS_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set voltage source range')

		self.vs_range = range
		return range

	def _VS_activate (self):

		if self.vs_active != True:

			libxhires.VS_enable (self.deviceID, COMM_TIMEOUT_INTERVAL)

			self.vs_active = True


	def _VS_deactivate (self):

		if self.vs_active != False:

			libxhires.VS_disable (self.deviceID, COMM_TIMEOUT_INTERVAL)

			self.vs_active = False


	def _VS_setVoltage (self, value):

		self.check_connected()

		self._VS_activate ()

		set_value, timeout = libxhires.VS_setVoltage (
			self.deviceID, value, COMM_TIMEOUT_INTERVAL)

		self.check_timeout (timeout, 'Set voltage')

		self.vs_value = set_value
		return value

	def _CM_setRange (self, range):

		self.check_connected()

		if self.cm_range == None or self.cm_range != range:

			range, timeout = libxhires.CM_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set ammeter range')

		self.cm_range = range
		return range

	def _VM_setRange (self, range):

		self.check_connected()

		if self.vm_range == None or self.vm_range != range:

			range, timeout = libxhires.VM_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set voltmeter range')

		self.vm_range = range
		return range

	def _VM_doAutoRange (self):

		limits = [(0.99 * 0.1 * rng, 1.01 * rng) for rng in VM_RANGES]
		self.check_connected()

		if self.vm_range == None:
			self._VM_setRange (VM_RANGE_MAX)

		while True:

			filterLength = 1

			voltage, timeout = libxhires.VM_getReading (
				self.deviceID, filterLength, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Get voltmeter reading')

			(low, hi) = limits[self.vm_range]

			if abs (voltage) < low:

				range = self.vm_range - 1
				if range < VM_RANGE_MIN : break
				else					: self._VM_setRange (range)

			elif abs (voltage) > hi:

				range = self.vm_range + 1
				if range > VM_RANGE_MAX : break
				else					: self._VM_setRange (range)

			else: break

		return self.vm_range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM_setRange (self, autorange, range):

		self.check_connected()
		self.vm_autorange = autorange

		if autorange:
			range = self._VM_doAutoRange()

		else:
			range = self._VM_setRange (range)

		self.do_callback (VM_RANGE_CHANGED, autorange, range)
		return (autorange, range)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM_getReading (self, filterLength = 128):

		self.check_connected()

		if self.vm_autorange:
			range = self._VM_doAutoRange()
			self.do_callback (VM_RANGE_CHANGED, self.vm_autorange, range)

		timeout = COMM_TIMEOUT_INTERVAL

		timeout += filterLength * 0.05

		voltage, timeout = libxhires.VM_getReading (
			self.deviceID, filterLength, timeout)

		self.check_timeout (timeout, 'Get voltmeter reading')

		return voltage

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CM_doAutoRange (self):

		limits = [(0.99 * 0.01 * rng, 1.01 * rng) for rng in CM_RANGES]

		self.check_connected()
		if self.cm_range == None: self._CM_setRange (CM_RANGE_MAX)

		while True:

			timeout	  = COMM_TIMEOUT_INTERVAL + 1.0
			cm_delay	 = 1.0
			filterLength = 1

			current, timeout = libxhires.CM_getReading (
				self.deviceID, filterLength, timeout)

			self.check_timeout (timeout, 'Get ammeter reading')

			(low, hi) = limits[self.cm_range]

			if abs (current) < low:

				range = self.cm_range - 1
				if range < CM_RANGE_MIN : break
				else					: self._CM_setRange (range)

			elif abs (current) > hi:

				range = self.cm_range + 1
				if range > CM_RANGE_MAX : break
				else					: self._CM_setRange (range)

			else: break

			sleep (cm_delay)

		return self.cm_range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setRange (self, autorange, range):

		self.check_connected()
		self.cm_autorange = autorange

		if autorange:
			range = self._CM_doAutoRange()

		else:
			range = self._CM_setRange (range)

		self.do_callback (CM_RANGE_CHANGED, autorange, range)
		return (autorange, range)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_getReading (self, filterLength = 128):

		self.check_connected()

		if (self.cm_autorange):
			range = self._CM_doAutoRange()
			self.do_callback (CM_RANGE_CHANGED, self.cm_autorange, range)

		timeout = COMM_TIMEOUT_INTERVAL

		timeout += filterLength * 0.05

		current, timeout = libxhires.CM_getReading (
				self.deviceID, filterLength, timeout)

		self.check_timeout (timeout, 'Get ammeter reading')

		return current

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CM_findRange (self, value):

		range = CM_RANGE_MIN

		while True:

			if abs (value) > CM_RANGES [range]:
				if range + 1 > CM_RANGE_MAX : break
				else						: range += 1

			else : break

		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _VS_findRange (self, value):

		range = VS_RANGE_MIN

		while True:

			if abs (value) > VS_RANGES [range]:
				if range + 1 > VS_RANGE_MAX : break
				else						: range += 1

			else : break

		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VS_setRange (self, autorange, range, value):

		self.check_connected()
		self.vs_autorange = autorange

		# +++++++++++++++++++++++++++++++++++++++++++
		# Finding source range

		if autorange:

			range = self._VS_findRange (value)

		# +++++++++++++++++++++++++++++++++++++++++++
		# Settings source range

		range = self._VS_setRange(range)

		# +++++++++++++++++++++++++++++++++++++++++++
		# Setting source value

		value = self._VS_setVoltage (value)

		self.do_callback (
			VS_RANGE_CHANGED, autorange, range, value)

		return (autorange, range, value)

	def acquire_lock (self):
		self._thlock.acquire()

	def release_lock (self):
		self._thlock.release()

'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''

class _Applet:

	def __init__ (self, oXHIRES):
		self.oXHIRES = oXHIRES
		self._plots = {}
		self._taskq = XTaskQueue()
		self._lastPlotUpdateAt = 0.0
		self._hApplet = self.oXHIRES.oApp.master.after (50, self._applet)

	def _applet (self):

		self._taskq.process()
		oApp = self.oXHIRES.oApp

		t = systime()
		if t >= self._lastPlotUpdateAt + 2:
			self._lastPlotUpdateAt = t

			for (wPlot, traceID) in self._plots.values():
				if wPlot.damaged() : wPlot.redraw()

		self._hApplet = oApp.master.after (50, self._applet)

	def schedule_task (self, task, *args):
		return self._taskq.push (task, *args)

	def refresh (self):
		self.oXHIRES.oApp.master.update()

	def close (self):
		oApp = self.oXHIRES.oApp
		oApp.close()
		oApp.master.after_cancel (self._hApplet)
		oApp.master.destroy()

	# +++++++++++++ Update display functions +++++++++++++++

	def set_status (self, status):
		self.oXHIRES.oApp.set_status (status)

	def setConnection (self, status):
		self.oXHIRES.oApp.setConnection (status)

	def CM_setReading (self, range, reading):
		self.oXHIRES.oApp.CM_setReading (range, reading)

	def VM_setReading (self, range, reading):
		self.oXHIRES.oApp.VM_setReading (range, reading)

	def initPlot (self, thread, title, xlabel, ylabel):
		oApp = self.oXHIRES.oApp
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
		oApp = self.oXHIRES.oApp
		oApp.clearPlot()
		self._plots.clear()

	def CM_setRange (self, autorange, range):
		self.oXHIRES.oApp.CM_setRange (autorange, range)
		self.oXHIRES.meterParameters.CM_setRange (autorange, range)

	def VM_setRange (self, autorange, range):
		self.oXHIRES.oApp.VM_setRange (autorange, range)
		self.oXHIRES.meterParameters.VM_setRange (autorange, range)

	def VS_setRange (self, autorange, range, value):

		oXHIRES   = self.oXHIRES
		oApp	= self.oXHIRES.oApp

		oApp.VS_setRange (autorange, range, value)
		oXHIRES.sourceParameters.VS_setRange (autorange, range, value)

		#oApp.VM_setRange (autorange, range)
		#oXHIRES.meterParameters.VM_setRange (autorange, range)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, mode):
		self.oXHIRES.oApp.setRunMode (mode)

	def setRunControlStatus (self, status):
		self.oXHIRES.oApp.setRunControlStatus (status)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setAcquisitionSettings (self, delay, filterLength):
		self.oXHIRES.oApp.setAcquisitionSettings (delay, filterLength)
		self.oXHIRES.acquisitionSettings.set (delay, filterLength)

	def setIVRampSettings (self, finalVoltage, voltageStep, bipolar):

		self.oXHIRES.oApp.setIVRampSettings (finalVoltage, voltageStep, bipolar)

		self.oXHIRES.ivRampSettings.set (finalVoltage, voltageStep, bipolar)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setOhmmeterSettings (self, maxVoltage, bipolar):

		self.oXHIRES.oApp.setOhmmeterSettings (maxVoltage, bipolar)

		self.oXHIRES.ohmmeterSettings.set (maxVoltage, bipolar)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquisition_atexit (self):
		self.oXHIRES.releaseAcquisition()

	def devicethread_atexit (self):
		self.oXHIRES.releaseDeviceThread();

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _DeviceThread (XThread):

	def __init__ (self, oXHIRES):

		XThread.__init__ (self, daemon = True)

		self.oXHIRES = oXHIRES

		'''
			Register driver callback
		'''
		oDriver = self.oXHIRES.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.callback (self._DriverCB)

		finally:
			oDriver.release_lock()

	def thread (self):

		lastPollAt = 0.0

		while True:

			try:

				while True:

					sleep (0.05)
					self.do_tasks()

					t = systime()
					if t >= lastPollAt + 2:

						lastPollAt = t
						self.acquire_n_display()

			except LinkError: pass

			except CommError as e :
				oApplet = self.oXHIRES.oApplet
				oApplet.schedule_task (oApplet.set_status, str (e))

			except XTerminate: break

		self.disconnectDevice()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _DriverCB (self, context, *args):

		oApplet = self.oXHIRES.oApplet

		if context == DEVICE_CONNECTED:
			oApplet.schedule_task (
				oApplet.setConnection, DEVICE_CONNECTED).wait()

		elif context == DEVICE_DISCONNECTED:
			oApplet.schedule_task (
				oApplet.setConnection, DEVICE_DISCONNECTED).wait()

		elif context == DEVICE_NOT_FOUND:
			oApplet.schedule_task (
				oApplet.setConnection, DEVICE_NOT_FOUND).wait()

		elif context == CM_RANGE_CHANGED:
			oApplet.schedule_task (oApplet.CM_setRange, *args).wait()

		elif context == VM_RANGE_CHANGED:
			oApplet.schedule_task (oApplet.VM_setRange, *args).wait()

		elif context == VS_RANGE_CHANGED:
			oApplet.schedule_task (oApplet.VS_setRange, *args).wait()

		else : raise ValueError (context)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquire_n_display (self):

		(cm_range, vm_range, datapoint) = self.acquire()

		oApplet = self.oXHIRES.oApplet

		oApplet.schedule_task (
			oApplet.CM_setReading, cm_range, datapoint.current)

		oApplet.schedule_task (
			oApplet.VM_setReading, cm_range, datapoint.voltage)

		return datapoint

	def acquire (self):
		oXHIRES   = self.oXHIRES
		oDriver = oXHIRES.oDriver

		try:
			oXHIRES.acquire_lock()
			oXHIRES.adjustMeterRanges()

			(current, voltage) = oXHIRES.measureIV (filterLength = 1)

			cm_range  = oDriver.cm_range
			vm_range  = oDriver.vm_range

		finally:
			oXHIRES.release_lock()

		return (cm_range, vm_range,
		  DataPoint (current = current, voltage = voltage))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	'''
		Connection functions
	'''

	def connectDevice (self):

		oDriver = self.oXHIRES.oDriver
		oApplet = self.oXHIRES.oApplet

		oApplet.schedule_task (oApplet.setConnection, DEVICE_CONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.open (get_XHIRES_serialNo())

		finally:
			oDriver.release_lock()

	def disconnectDevice (self):

		oDriver = self.oXHIRES.oDriver
		oApplet = self.oXHIRES.oApplet

		oApplet.schedule_task (oApplet.setConnection, DEVICE_DISCONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.close()

		finally:
			oDriver.release_lock()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	'''
		Source parameters
	'''
	def VS_setRange (self, autorange, range, value):

		oDriver = self.oXHIRES.oDriver
		oApplet = self.oXHIRES.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.VS_setRange (autorange, range, value)

		finally:
			oDriver.release_lock()

	'''
		Meter parameters
	'''

	def CM_setRange (self, autorange, range):

		oDriver = self.oXHIRES.oDriver
		oApplet = self.oXHIRES.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.CM_setRange (autorange, range)

		finally:
			oDriver.release_lock()

	def VM_setRange (self, autorange, range):

		oDriver = self.oXHIRES.oDriver
		oApplet = self.oXHIRES.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.VM_setRange (autorange, range)

		finally:
			oDriver.release_lock()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def XHIRES (master, sample):

	if not XHIRES.singleton:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()

		oApp		   = GUI (win, sample)
		XHIRES.singleton = _XHIRES (oApp, sample)

	if master not in XHIRES.master:
		XHIRES.master.append (master)

	return XHIRES.singleton

def closeXHIRES (master):

	if master in XHIRES.master:
		XHIRES.master.remove (master)

	if len (XHIRES.master) == 0 and XHIRES.singleton:
		XHIRES.singleton.close()
		XHIRES.singleton = None

XHIRES.singleton = None
XHIRES.master	= []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class SourceParameters:

	def __init__ (self, vs_autorange, vs_range, vs_value):

		self.vs_autorange = vs_autorange
		self.vs_range  = vs_range
		self.vs_value  = vs_value

	def VS_setRange (self, vs_autorange, vs_range, vs_value):

		self.vs_autorange = vs_autorange
		self.vs_range  = vs_range
		self.vs_value  = vs_value

	def get (self):
		return (
			self.vs_autorange,
			self.vs_range,
			self.vs_value)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class MeterParameters:

	def __init__ (self, cm_autorange, cm_range,
			   vm_autorange, vm_range):

		self.CM_setRange (cm_autorange, cm_range)
		self.VM_setRange (vm_autorange, vm_range)

	def CM_setRange (self, cm_autorange, cm_range):
		self.cm_autorange = cm_autorange
		self.cm_range	 = cm_range

	def VM_setRange (self, vm_autorange, vm_range):
		self.vm_autorange = vm_autorange
		self.vm_range	 = vm_range

	def set (self,
			 cm_autorange  = None, cm_range  = None,
			 vm_autorange  = None, vm_range  = None):

		if cm_autorange  != None : self.cm_autorange  = cm_autorange
		if cm_range	  != None : self.cm_range	  = cm_range
		if vm_autorange  != None : self.vm_autorange  = vm_autorange
		if vm_range	  != None : self.vm_range	  = vm_range

	def get (self):
		return (
			self.cm_autorange,
			self.cm_range,
			self.vm_autorange,
			self.vm_range)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class AcquisitionSettings:

	def __init__ (self, delay, filterLength):
		self.set (delay, filterLength)

	def set (self, delay, filterLength):
		self.delay		= delay
		self.filterLength = filterLength

	def get (self):
		return (
			self.delay,
			self.filterLength)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class IVRampSettings:

	def __init__ (self, finalVoltage, voltageStep, bipolar):

		self.set (finalVoltage, voltageStep, bipolar)

	def set (self, finalVoltage, voltageStep, bipolar):

		self.finalVoltage = finalVoltage
		self.voltageStep  = voltageStep
		self.bipolar	  = bipolar

	def get (self):
		return (self.finalVoltage, self.voltageStep, self.bipolar)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class OhmmeterSettings:

	def __init__ (self, maxVoltage, bipolar):

		self.set (maxVoltage, bipolar)

	def set (self, maxVoltage, bipolar):

		self.maxVoltage   = maxVoltage
		self.bipolar	  = bipolar

	def get (self):
		return (self.maxVoltage, self.bipolar)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XHIRES:

	def __init__ (self, oApp, sample):

		self.oApp = oApp
		self.sample = sample
		oDriver = self.oDriver = _Driver()

		# ++++ Device parameters ++++

		self.sourceParameters = SourceParameters (
			vs_autorange = True, vs_range  = VS_RANGE_10V,
			vs_value  = 0.0)

		self.meterParameters = MeterParameters (
			cm_autorange = True, cm_range = CM_RANGE_1uA,
			vm_autorange = True, vm_range = VM_RANGE_100V)

		self.run_mode	  = RUN_MODE_RTime

		# ++++ Settings ++++

		self.acquisitionSettings = \
			AcquisitionSettings (delay = 2.0, filterLength = 16)

		self.ivRampSettings = IVRampSettings (
			finalVoltage = 10.0,
			voltageStep  = 1.0,
			bipolar	  = True)

		self.ohmmeterSettings = OhmmeterSettings (
			maxVoltage   = 10.0,
			bipolar	  = True)

		# ++++ Support for multi-threading ++++

		self._thlock	   = RLock()
		self.oApplet	   = _Applet (self)
		self.oDeviceThread = None
		self.oModule	   = None
		self.oAcqThread	   = None

		try:
			thread = self.prepareDeviceThread()
			thread.start()

		except ResourceError as e:
			self.oApplet.set_status (str (e))

		# ++++ initialize app and try connectig to the device

		self.oApp.callback (self.oAppCB)

		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.setRunMode, self.run_mode)

		oApplet.schedule_task (
			oApplet.setAcquisitionSettings,
			self.acquisitionSettings.delay,
			self.acquisitionSettings.filterLength)

		oApplet.schedule_task (
			oApplet.setIVRampSettings,
			self.ivRampSettings.finalVoltage,
			self.ivRampSettings.voltageStep,
			self.ivRampSettings.bipolar)

		oApplet.schedule_task (
			oApplet.setOhmmeterSettings,
			self.ohmmeterSettings.maxVoltage,
			self.ohmmeterSettings.bipolar)

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

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def connectDevice (self):

		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.setConnection, DEVICE_CONNECTING)

		oDeviceThread = self.oDeviceThread
		oDeviceThread.schedule_task (oDeviceThread.connectDevice)

		oDeviceThread.schedule_task (
			oDeviceThread.VS_setRange,
			self.sourceParameters.vs_autorange,
			self.sourceParameters.vs_range,
			self.sourceParameters.vs_value)

		oDeviceThread.schedule_task (
			oDeviceThread.CM_setRange,
			self.meterParameters.cm_autorange,
			self.meterParameters.cm_range)

		oDeviceThread.schedule_task (
			oDeviceThread.VM_setRange,
			self.meterParameters.vm_autorange,
			self.meterParameters.vm_range)

	def disconnectDevice (self):

		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.setConnection, DEVICE_DISCONNECTING)

		oDeviceThread = self.oDeviceThread
		oDeviceThread.schedule_task (oDeviceThread.disconnectDevice)

	# ++++ Device thread ctor/dtor ++++

	def devicethread_atexit (self):
		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.devicethread_atexit)

	def prepareDeviceThread (self):

		thread = None

		if self.oDeviceThread == None:

			thread = _DeviceThread (self)
			thread.atexit (self.devicethread_atexit)
			self.oDeviceThread = thread

		else:
			raise ResourceError (
				'XHIRES_ResourceError: Device thread unavailable')

		return thread

	def releaseDeviceThread (self):
		self.oDeviceThread = None

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def oAppCB (self, context, *args):

		oApplet = self.oApplet
		oDeviceThread = self.oDeviceThread

		if   context == CONNECT_DEVICE	: self.connectDevice()
		elif context == DISCONNECT_DEVICE : self.disconnectDevice()

		elif context == RUN_MODE		  :
			oApplet.schedule_task (oApplet.setRunMode, *args)

		elif context == START_RUN		 : self.startRun (*args)
		elif context == FINISH_RUN		: self.finishRun()
		elif context == OPEN_DIALOG	   : self.openDialog (*args)
		elif context == OPEN_METHOD	   : self.openMethod (*args)
		elif context == SAVE_METHOD	   : self.saveMethod (*args)

		else: raise ValueError (context)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def startRun (self, mode):

		self.oApplet.setRunControlStatus (RUN_STARTING)

		try:
			thread = self.prepareAcquisition (mode)
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

	def prepareModule (self, master, mode):

		module = None

		if self.oModule == None:

			if mode == RUN_MODE_ITime:
				module = _ITimeModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

			elif mode == RUN_MODE_IV:
				module = _IVModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

				module.initIVRampSettings (
					self.ivRampSettings.finalVoltage,
					self.ivRampSettings.voltageStep,
					self.ivRampSettings.bipolar)

			elif mode == RUN_MODE_RTime:
				module = _RTimeModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

				module.initOhmmeterSettings (
					self.ohmmeterSettings.maxVoltage,
					self.ohmmeterSettings.bipolar)

			else:
				raise ResourceError (
					'XHIRES_ResourceError: Module creation failed')

			self.oModule = module

		else:
			raise ResourceError (
				'XHIRES_ResourceError: Module unavailable')

		return module

	def releaseModule (self, caller):
		if self.oModule and caller == self.oModule.master:
			self.oModule = None

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareAcquisition (self, mode):

		thread = None
		master = self

		try:

			if self.oAcqThread == None:

				module = self.prepareModule (master, mode)

				if mode == RUN_MODE_ITime:
					thread =  _ITimeAcquisitionThread (module)

				elif mode == RUN_MODE_IV:
					thread = _IVAcquisitionThread (module)

				elif mode == RUN_MODE_RTime:
					thread = _RTimeAcquisitionThread (module)

				else:
					raise ResourceError (
						'XHIRES_ResourceError: Thread creation failed')

				thread.atexit (self.acquisition_atexit)
				self.oAcqThread = thread

			else:
				raise ResourceError (
					'XHIRES_ResourceError: Thread unavailable')

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

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openDialog (self, dialog):

		if dialog == SOURCE_PARAMETERS_DIALOG:
			self.openSourceDialog()

		elif dialog == METER_SETTINGS_DIALOG:
			self.openMeterDialog()

		elif dialog == ACQUISITION_SETTINGS_DIALOG:
			self.openAcquisitionSettingsDialog()

		elif dialog == IV_RAMP_SETTINGS_DIALOG:
			self.openIVRampDialog()

		elif dialog == OHMMETER_SETTINGS_DIALOG:
			self.openOhmmeterDialog()

		else: raise ValueError (dialog)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openSourceDialog (self):

		# Creates a GUI_SourceParameters dialog

		w = self.dialog = GUI_SourceParameters (
			Toplevel (takefocus = True),
			self.sourceParameters.vs_autorange,
			self.sourceParameters.vs_range,
			self.sourceParameters.vs_value)

		w.callback (self.sourceDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def sourceDialogCB (self, context, *args):

		oDeviceThread = self.oDeviceThread

		if context == APPLY:
			oDeviceThread.schedule_task (
				oDeviceThread.VS_setRange, *args)

			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openMeterDialog (self):

		# Creates a GUI_MeterParameters dialog

		w = self.dialog = GUI_MeterParameters (
			Toplevel (takefocus = True),
			self.meterParameters.cm_autorange,
			self.meterParameters.cm_range,
			self.meterParameters.vm_autorange,
			self.meterParameters.vm_range)

		w.callback (self.meterDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def meterDialogCB (self, context, *args):

		oDeviceThread = self.oDeviceThread

		if context == CM_RANGE_CHANGED:
			oDeviceThread.schedule_task (oDeviceThread.CM_setRange, *args)

		elif context == VM_RANGE_CHANGED:
			oDeviceThread.schedule_task (oDeviceThread.VM_setRange, *args)

		elif context == APPLY:
			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:

			oDeviceThread.schedule_task (
				oDeviceThread.CM_setRange,
				self.meterParameters.cm_autorange,
				self.meterParameters.cm_range)

			oDeviceThread.schedule_task (
				oDeviceThread.VM_setRange,
				self.meterParameters.vm_autorange,
				self.meterParameters.vm_range)

			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openAcquisitionSettingsDialog (self):

		w = self.dialog = GUI_AcquisitionSettings (
			Toplevel (takefocus = True),
			self.acquisitionSettings.delay,
			self.acquisitionSettings.filterLength)

		w.callback (self.acquisitionSettingsDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def acquisitionSettingsDialogCB (self, context, *args):

		oApplet	= self.oApplet
		oModule	= self.oModule

		if context == APPLY:

			oApplet.schedule_task (oApplet.setAcquisitionSettings, *args)

			if oModule:
				oModule.schedule_task (oModule.setAcquisitionSettings, *args)

			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openIVRampDialog (self):

		w = self.dialog = GUI_IVRampSettings (
			Toplevel (takefocus = True),
			self.ivRampSettings.finalVoltage,
			self.ivRampSettings.voltageStep,
			self.ivRampSettings.bipolar)

		w.callback (self.ivRampDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def ivRampDialogCB (self, context, *args):

		oApplet	= self.oApplet
		oModule	= self.oModule

		if context == APPLY:

			oApplet.schedule_task (oApplet.setIVRampSettings, *args)

			if oModule and isinstance (oModule, _IVModule):
				oModule.schedule_task (oModule.setIVRampSettings, *args)

			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openOhmmeterDialog (self):

		w = self.dialog = GUI_OhmmeterSettings (
			Toplevel (takefocus = True),
			self.ohmmeterSettings.maxVoltage,
			self.ohmmeterSettings.bipolar)

		w.callback (self.ohmmeterDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def ohmmeterDialogCB (self, context, *args):

		oApplet	= self.oApplet
		oModule	= self.oModule

		if context == APPLY:

			oApplet.schedule_task (oApplet.setOhmmeterSettings, *args)

			if oModule and isinstance (oModule, _RTimeModule):
				oModule.schedule_task (oModule.setOhmmeterSettings, *args)

			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def doExcitation (self, excitation_voltage):

		print "Applying excitation ..."

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.VS_setRange (
				self.sourceParameters.vs_autorange,
				self.sourceParameters.vs_range,
				excitation_voltage)

		finally:
			oDriver.release_lock()

		(current, vsrc) = self.measureIV (filterLength = 1)

		(mult, unit, fmt) = (1., "V", "%+.3f")

		print ("Setpoint: " + str (fmt % (mult * vsrc)) + unit + "\n")

		return vsrc

	# Useful functions callable from other modules

	def output_off (self):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			oDriver.VS_setRange (
				self.sourceParameters.vs_autorange,
				self.sourceParameters.vs_range, 0.0)

		finally:
			oDriver.release_lock()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def adjustMeterRanges (self):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			if self.meterParameters.cm_autorange:
				oDriver.CM_getReading (filterLength = 1)

			if self.meterParameters.vm_autorange:
				oDriver.VM_getReading (filterLength = 1)

		finally:
			oDriver.release_lock()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def measureI (self, filterLength):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			current = oDriver.CM_getReading  (filterLength)

		finally:
			oDriver.release_lock()

		return current

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def measureV (self, filterLength):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			voltage = oDriver.VM_getReading  (filterLength)

		finally:
			oDriver.release_lock()

		return voltage

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def measureIV (self, filterLength):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			current = oDriver.CM_getReading  (filterLength)
			voltage = oDriver.VM_getReading  (filterLength)

		finally:
			oDriver.release_lock()

		return (current, voltage)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def sleep (self, duration, bg_task = None, *bg_tasks):

		entry = systime()
		while systime() < entry + duration:
			sleep (0.05)
			if bg_task: bg_task()
			for task in bg_tasks:
				if task: task()

	def measureR (
		self, bipolar, delay, filterLength,
		bg_task = None, *bg_tasks):

		# Measure positive values
		self.doExcitation (self.ohmmeterSettings.maxVoltage)

		self.adjustMeterRanges()
		self.sleep (delay, bg_task, *bg_tasks)

		(posI, posVsrc) = self.measureIV (filterLength)

		# Measure negetive values
		if bipolar:

			self.doExcitation (-self.ohmmeterSettings.maxVoltage)

			self.adjustMeterRanges()
			self.sleep (delay, bg_task, *bg_tasks)

			(negI, negVsrc) = self.measureIV (filterLength)

		# Calculate delta I and delta V
		if bipolar:
			delI = abs (posI - negI) / 2.0
			delVsrc = abs (posVsrc - negVsrc) / 2.0

		else:
			delI = abs (posI)
			delVsrc = abs (posVsrc)

		# Calculate resistance
		try:
			resistance = delVsrc / delI

		except ZeroDivisionError:
			resistance = float ('inf')

		self.doExcitation (0.0)

		return (delI, delVsrc, resistance)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMethod (self):
		method = Method()
		method.setSourceParameters	(*self.sourceParameters.get())
		method.setMeterParameters	 (*self.meterParameters.get())
		method.setAcquisitionSettings (*self.acquisitionSettings.get())
		method.set_IV_RampSettings	(*self.ivRampSettings.get())
		method.setOhmmeterSettings	(*self.ohmmeterSettings.get())
		return method

	def applyMethod (self, method):
		oApplet	   = self.oApplet
		oDeviceThread = self.oDeviceThread
		oModule	   = self.oModule

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		self.sourceParameters.set (
			*method.getSourceParameters (
				*self.sourceParameters.get()))

		oDeviceThread.schedule_task (
			oDeviceThread.VS_setRange,
			self.sourceParameters.vs_autorange,
			self.sourceParameters.vs_range,
			self.sourceParameters.vs_value)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		self.meterParameters.set (
			*method.getMeterParameters (
				*self.meterParameters.get()))

		oDeviceThread.schedule_task (
			oDeviceThread.CM_setRange,
			self.meterParameters.cm_autorange,
			self.meterParameters.cm_range)

		oDeviceThread.schedule_task (
			oDeviceThread.VM_setRange,
			self.meterParameters.vm_autorange,
			self.meterParameters.vm_range)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		settings = method.getAcquisitionSettings (
			*self.acquisitionSettings.get())

		oApplet.schedule_task (oApplet.setAcquisitionSettings, *settings)

		if oModule:
			oModule.schedule_task (
				oModule.setAcquisitionSettings, *settings)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		settings = method.get_IV_RampSettings (*self.ivRampSettings.get())

		oApplet.schedule_task (oApplet.setIVRampSettings, *settings)

		if oModule and isinstance (oModule, _IVModule):
			oModule.schedule_task (
				oModule.setIVRampSettings, *settings)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		settings = method.getOhmmeterSettings (*self.ohmmeterSettings.get())

		oApplet.schedule_task (oApplet.setOhmmeterSettings, *settings)

		if oModule and isinstance (oModule, _RTimeModule):
			oModule.schedule_task (
				oModule.setOhmmeterSettings, *settings)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openMethod (self, fd):

		try:
			self.applyMethod (Method (fd))
			text = 'Method opened : ' + fd.name

		except XMethodError as e:
			text = 'Method failed : ' + str (e) + ' : ' + fd.name

		oApplet = self.oApplet
		oApplet.schedule_task (oApplet.set_status, text)

	def saveMethod (self, fd):
		self.getMethod().save (fd)

		oApplet = self.oApplet
		text = 'Method saved : ' + fd.name
		oApplet.schedule_task (oApplet.set_status, text)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Module (XThreadModule):

	def __init__ (self, master, oXHIRES):
		XThreadModule.__init__ (self, master)
		self.oXHIRES		= oXHIRES
		self.t0		   = systime()
		self.dataset	  = DataSet()
		self.fd_log	   = None
		self._alive	   = False

	# ++++ Useful functions used by derived classes ++++

	'''
		Redefine these in the derived class
		to set run-type specific folder name and extension.
	'''

	def run_type (self):
		return ''

	def xlabel (self):
		return ''

	def ylabel (self):
		return ''

	def folder_name (self):
		return 'xhires'

	def is_alive (self):
		return True if self._alive else False

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def initAcquisitionSettings (self, delay, filterLength):
		self.delay		= delay
		self.filterLength = filterLength

	def setAcquisitionSettings (self, delay, filterLength):
		self.initAcquisitionSettings (delay, filterLength)
		oApplet = self.oXHIRES.oApplet
		text = 'Acquisition settings updated'
		oApplet.schedule_task (oApplet.set_status, text)

	def init (self):

		oXHIRES		 = self.oXHIRES
		oApplet	   = oXHIRES.oApplet
		self._alive   = True

		try:
			self.filename = self.get_timestamp()
			oApplet.schedule_task (oApplet.setRunControlStatus, RUN_STARTING)

			self.t0	  = systime()
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

		oXHIRES   = self.oXHIRES
		oApplet = oXHIRES.oApplet
		oApplet.schedule_task (oApplet.setRunControlStatus, RUN_FINISHING)

		# Resets excitation voltage
		try:
			oXHIRES.output_off()

		except (LinkError, CommError):
			pass

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

		self._alive = False

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
			('Time',	   '%12s', 'sec'),
			('Current',	   '%20s',   'A'),
			('Voltage',	   '%12s',   'V'),
			('Resistance', '%16s', 'ohm')
		]

		(sampleName, sampleID, sampleDescription) = self.oXHIRES.sample.get()
		self.fd_log.write ('#Sample name		: ' + sampleName		+ '\n')
		self.fd_log.write ('#Sample ID		  : ' + sampleID		  + '\n')

		label =			'#Sample description : '
		sampleDescription = sampleDescription.replace ('\n', '\n' + label)
		self.fd_log.write (label + sampleDescription + '\n')

		text = ''
		for field in fields:
			(name, fmt, unit) = field
			text += str (fmt % name) + ','
		self.fd_log.write ('#' + text + '\n')

		text = ''
		for field in fields:
			(name, fmt, unit) = field
			text += str (fmt % unit) + ','
		self.fd_log.write ('#' + text + '\n')

		self.fd_log.flush()
		return full_path

	def update_log (self, datapoint):

		fields = [
			('Time	   : ',   '%12.1f',  datapoint.time,	   'sec'),
			('Current	: ',  '%20.15f', datapoint.current,	   'A'),
			('Voltage	: ',  '%12.5f',  datapoint.voltage,	   'V'),
			('Resistance : ', '%16.0f',  datapoint.resistance, 'ohm')
		]

		'''
			Prints on screen
		'''
		text = ''
		for field in fields:
			(name, fmt, value, unit) = field
			text += name + str (fmt % value) + unit + '\n'

		print text

		'''
			Writes to file
		'''
		text = ''
		for field in fields:
			(name, fmt, value, unit) = field
			text += str (fmt % value) + ','

		self.fd_log.write (text + '\n')
		self.fd_log.flush()


	def close_log (self):

		if self.fd_log != None:
			self.fd_log.close()

		self.fd_log = None

	def save (self, dataset):

		dict = XDict()
		dict.set_sample (self.oXHIRES.sample.get())
		#dict.set_events ({})

		fields = [
			('01 Time',	   DATASET_COL_TIME,	   'second'),
			('02 Current',	DATASET_COL_CURRENT,		 'A'),
			('03 Voltage',	DATASET_COL_VOLTAGE,		 'V'),
			('05 Resistance', DATASET_COL_RESISTANCE,	  'Ω')
		]

		for field in fields:
			(key, col, unit) = field
			dict.set_data (key, dataset.getColumn (col), unit)

		(fd, full_path) = self.open_file (
			self.filename + '_' + self.run_type(), 'xpl', 'w')

		dict.save (fd)
		fd.close()

		return full_path

	def open_file (self, file_name, file_ext, open_mode):

		(sampleName, sampleID, _) = self.oXHIRES.sample.get()

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

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _ITimeModule (_Module):

	def __init__ (self, master, oXHIRES):
		_Module.__init__ (self, master, oXHIRES)

	def run_type (self):
		return 'I_Time'

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Current (A)'

	def init (self):
		_Module.init (self)

		oXHIRES   = self.oXHIRES
		oApplet = oXHIRES.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_ITime)

	def acquire (self, bg_task = None, *bg_tasks):

		oXHIRES = self.oXHIRES
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		# ++++++++++++++++++++++++++++++

		try:
			oXHIRES.acquire_lock()
			current = oXHIRES.measureI (self.filterLength)

		finally:
			oXHIRES.release_lock()

		return DataPoint (time = t, current = current)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oXHIRES   = self.oXHIRES
		oApplet = oXHIRES.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			datapoint = self.acquire (self.do_tasks, bg_task, *bg_tasks)
			self.update_log (datapoint)
			self.dataset.append (datapoint)

			oApplet.schedule_task (
				oApplet.updatePlot, self, datapoint.time, datapoint.current)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _ITimeAcquisitionThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:

			self.module.init()

			while True:
				self.do_tasks()
				self.module.sleep (1, self.do_tasks)
				self.module.acquire_n_plot (self.do_tasks)

		except (CommError, LinkError) : pass
		except (IOError, OSError)	 : pass
		except XTerminate			 : pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _IVModule (_Module):

	def __init__ (self, master, oXHIRES):
		_Module.__init__ (self, master, oXHIRES)
		self.excitationVoltage = None
		self.scan_mode		 = None
		self._complete		 = False

	def run_type (self):
		return 'IV'

	def xlabel (self):
		return 'Voltage (V)'

	def ylabel (self):
		return 'Current (A)'

	def init (self):
		_Module.init (self)

		oXHIRES   = self.oXHIRES
		oApplet = oXHIRES.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_IV)

		self.excitationVoltage = None
		self.scan_mode		 = None
		self._complete		 = False

	def initIVRampSettings (
		self, finalVoltage, voltageStep, bipolar):

		self.finalVoltage = finalVoltage
		self.voltageStep  = voltageStep
		self.bipolar	  = bipolar

	def setIVRampSettings (
		self, finalVoltage, voltageStep, bipolar):

		self.initIVRampSettings (
			finalVoltage, voltageStep, bipolar)

		text = 'IV settings updated'
		oApplet = self.oXHIRES.oApplet
		oApplet.schedule_task (oApplet.set_status, text)

	def acquire (self, bg_task = None, *bg_tasks):

		oXHIRES = self.oXHIRES
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		try:
			oXHIRES.acquire_lock()
			(current, voltage) = oXHIRES.measureIV (self.filterLength)

		finally:
			oXHIRES.release_lock()

		return DataPoint (
			time	= t,
			current = current,
			voltage = voltage)

	def breakPlot (self):

		oApplet = self.oXHIRES.oApplet

		blank_datapoint = DataPoint (
			time	= None,
			current = None,
			voltage = None)

		self.dataset.append (blank_datapoint)

		oApplet.schedule_task (
			oApplet.updatePlot, self,
			blank_datapoint.voltage, blank_datapoint.current)

		return blank_datapoint

	def excite_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oXHIRES.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			breakPlot = self.applyNextExcitation()
			if breakPlot: self.breakPlot()

			if not self.complete():

				self.sleep (self.delay, self.do_tasks, bg_task, *bg_tasks)
				datapoint = self.acquire (self.do_tasks, bg_task, *bg_tasks)

				self.update_log (datapoint)
				self.dataset.append (datapoint)

				oApplet.schedule_task (
					oApplet.updatePlot, self,
					datapoint.voltage, datapoint.current)

			else:
				datapoint = None

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint, breakPlot

	def applyNextExcitation (self):

		oXHIRES = self.oXHIRES

		'''
			Find excitation
		'''

		breakPlot = NO_BREAKPLOT

		if self.scan_mode == None:
			self.scan_mode = SCAN_MODE_POSITIVE

		if self.scan_mode == SCAN_MODE_POSITIVE:
			breakPlot = self.findNextPositiveExcitation (breakPlot)

		if self.scan_mode == SCAN_MODE_NEGATIVE:
			breakPlot = self.findNextNegativeExcitation (breakPlot)

		if not self.complete():

			try:
				oXHIRES.acquire_lock()

				if self.voltageStep != 0.0:
					voltage = self.excitationVoltage
				else:
					voltage = self.finalVoltage

				if voltage == 0.0:
					oXHIRES.output_off ()

				else:
					value = oXHIRES.doExcitation (voltage)

			finally:
				oXHIRES.release_lock()

		return breakPlot

	def findNextPositiveExcitation (self, breakPlot):

		oXHIRES = self.oXHIRES

		if self.excitationVoltage == None:

			self.excitationVoltage = 0.0

		elif (abs (self.excitationVoltage) < abs  (self.finalVoltage)):

				# Estimating next voltage

				nextVoltage = (
					oXHIRES.sourceParameters.vs_value + self.voltageStep)

				try:
					self.excitationVoltage = self.voltageStep * round (
						nextVoltage / self.voltageStep)

				except ZeroDivisionError:
					self.excitationVoltage = nextVoltage

		else:
			self.excitationVoltage = None

			if self.bipolar:
				breakPlot	  = DO_BREAKPLOT
				self.scan_mode = SCAN_MODE_NEGATIVE

			else:
				self.scan_mode = None
				self._complete = True

		return breakPlot

	def findNextNegativeExcitation (self, breakPlot):

		oXHIRES = self.oXHIRES

		if (self.excitationVoltage == None):

			self.excitationVoltage = 0.0

		elif (abs (self.excitationVoltage) < abs (self.finalVoltage)):

				# Estimating next voltage

				nextVoltage = (
					oXHIRES.sourceParameters.vs_value - self.voltageStep)

				try:
					self.excitationVoltage = self.voltageStep * round (
						nextVoltage / self.voltageStep)

				except ZeroDivisionError:
					self.excitationVoltage = nextVoltage

		else:
			self.scan_mode = None
			self.excitationVoltage = None
			self._complete = True

		return breakPlot

	def complete (self):
		return True if self._complete else False

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _IVAcquisitionThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:
			self.module.init()

			while True:
				self.do_tasks()
				self.module.excite_n_plot (self.do_tasks)
				if self.module.complete(): break

		except (CommError, LinkError) : pass
		except (IOError, OSError)	 : pass
		except XTerminate			 : pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RTimeModule (_Module):

	def __init__ (self, master, oXHIRES):
		_Module.__init__ (self, master, oXHIRES)

	def run_type (self):
		return 'R_Time'

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Resistance (Ohm)'

	def init (self):
		_Module.init (self)

		oXHIRES   = self.oXHIRES
		oApplet = oXHIRES.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_RTime)

	def initOhmmeterSettings (self, maxVoltage, bipolar):

		self.maxVoltage   = maxVoltage
		self.bipolar	  = bipolar

	def setOhmmeterSettings (self, maxVoltage, bipolar):

		self.initOhmmeterSettings (maxVoltage, bipolar)

		text = 'Ohmmeter settings updated'
		oApplet = self.oXHIRES.oApplet
		oApplet.schedule_task (oApplet.set_status, text)

	def acquire (self, bg_task = None, *bg_tasks):

		oXHIRES = self.oXHIRES
		t = systime() - self.t0

		self.do_tasks (bg_task, *bg_tasks)

		maxVoltage   = self.maxVoltage
		filterLength = self.filterLength
		delay        = self.delay
		bipolar      = self.bipolar

		# +++++++++++++++++++++++++++++++++++++++++++++++
		# Measure positive values

		try:
			oXHIRES.acquire_lock()
			oXHIRES.doExcitation (maxVoltage)
			oXHIRES.adjustMeterRanges()

		finally:
			oXHIRES.release_lock()

		# Sleep for specified delay time while handling background processes
		self.sleep (delay, self.do_tasks, bg_task, *bg_tasks)

		try:
			oXHIRES.acquire_lock()
			(posI, posVsrc) = oXHIRES.measureIV (filterLength)

		finally:
			oXHIRES.release_lock()

		# +++++++++++++++++++++++++++++++++++++++++++++++
		# Measure negetive values

		if bipolar:

			try:
				oXHIRES.acquire_lock()
				oXHIRES.doExcitation (-maxVoltage)
				oXHIRES.adjustMeterRanges()

			finally:
				oXHIRES.release_lock()

			# Sleep for specified delay time while handling background processes
			self.sleep (delay, self.do_tasks, bg_task, *bg_tasks)

			try:
				oXHIRES.acquire_lock()
				(negI, negVsrc) = oXHIRES.measureIV (filterLength)

			finally:
				oXHIRES.release_lock()

		# +++++++++++++++++++++++++++++++++++++++++++++++
		# Calculate delta I and delta V

		if bipolar:
			delI = abs (posI - negI) / 2.0
			delVsrc = abs (posVsrc - negVsrc) / 2.0

		else:
			delI = abs (posI)
			delVsrc = abs (posVsrc)

		# Calculate resistance
		try:
			resistance = delVsrc / delI

		except ZeroDivisionError:
			resistance = float ('inf')

		# +++++++++++++++++++++++++++++++++++++++++++++++

		return DataPoint (
			time	   = t,
			current	   = delI,
			voltage	   = delVsrc,
			resistance = resistance)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oXHIRES.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:
			datapoint = self.acquire (self.do_tasks, bg_task, *bg_tasks)
			self.update_log (datapoint)
			self.dataset.append (datapoint)

			oApplet.schedule_task (
				oApplet.updatePlot, self,
				datapoint.time, datapoint.resistance)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RTimeAcquisitionThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:

			self.module.init()

			while True:
				self.do_tasks()
				self.module.acquire_n_plot (self.do_tasks)

		except (CommError, LinkError) : pass
		except (IOError, OSError)	 : pass
		except XTerminate			 : pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

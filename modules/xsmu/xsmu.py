# coding: utf-8
import libxsmu
import time

from app_xsmu       import GUI
from app_xsmu       import GUI_SourceParameters
from app_xsmu       import GUI_MeterParameters
from app_xsmu       import GUI_AcquisitionSettings
from app_xsmu       import GUI_IVRampSettings
from app_xsmu       import GUI_IVTimeResolvedRampSettings
from app_xsmu       import GUI_OhmmeterSettings

from XSMU_DataType  import DataPoint, DataSet
from XSMU_Method    import Method, XMethodError

from XDict          import XDict
from XThread        import XTaskQueue, XThread, XThreadModule, XTerminate
from Preferences    import get_XSMU_serialNo, getDataFolder

# Importing Python provided libraries
import os
from threading      import Thread, RLock, Lock
from time           import time as systime, localtime, sleep
from Tkinter        import Toplevel
from math           import copysign, sqrt

from XSMU_Constants import *
INDEX = 0

def Driver():

	if Driver.singleton == None:
		Driver.singleton = _Driver()

	return Driver.singleton

Driver.singleton = None

class LinkError     (Exception) : pass
class CommError     (Exception) : pass
class ResourceError (Exception) : pass

class _Driver:

	def __init__ (self):
		self._thlock = RLock()

		self.deviceID = None
		self.src_mode = None
		self.vs_range = None
		self.vm_range = None
		self.cm_range = None
		self.cs_value = None
		self.vs_value = None
		self.vm2_range = None

		self.cm_autorange  = True
		self.vm_autorange  = True
		self.vm2_autorange = True
		self.src_autorange = True

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
		number_of_devices = libxsmu.scan()
		for i in range (0, number_of_devices):
			serialNos.append (libxsmu.serialNo (i))

		return serialNos

	def open (self, serialNo):

		if serialNo in self.scan():

			self.deviceID, goodID, timeout = (
				libxsmu.open_device (serialNo, COMM_TIMEOUT_INTERVAL))

			if timeout != 0.0 and goodID:
				self.do_callback (DEVICE_CONNECTED)

			else:
				libxsmu.close_device (self.deviceID)
				self.deviceID = None
				self.do_callback (DEVICE_NOT_FOUND)

		else:
			self.do_callback (DEVICE_NOT_FOUND)

	def close (self):

		if self.deviceID != None:

			libxsmu.close_device (self.deviceID)

			self.deviceID = None
			self.src_mode = None
			self.vs_range = None
			self.vm_range = None
			self.cm_range = None
			self.cs_value = None
			self.vs_value = None
			self.vm2_range = None

			self.do_callback (DEVICE_DISCONNECTED)

	def check_connected (self):
		if self.deviceID == None:
			raise LinkError ('XSMU_LinkError: Device not connected')

	def check_timeout (self, timeout, context = ''):
		if (timeout == 0.0):
			self.close()
			raise CommError ('XSMU_CommError: ' + str (context))

	def _setSourceMode (self, mode):

		self.check_connected()

		if self.src_mode == None or self.src_mode != mode:

			mode, timeout = libxsmu.setSourceMode (
				self.deviceID, mode, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set source mode')

			if mode == SOURCE_MODE_CS:
				self.cm_range = None
				self.cs_value = None

			if mode == SOURCE_MODE_VS:
				self.vs_range = None
				self.vs_value = None

		self.src_mode = mode
		return mode

	def _VS_setRange (self, range):

		self.check_connected()

		if self.vs_range == None or self.vs_range != range:

			range, timeout = libxsmu.VS_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set voltage source range')

		self.vs_range = range
		return range

	def _CS_setCurrent (self, value):

		self.check_connected()

		set_value, timeout = libxsmu.CS_setCurrent (
			self.deviceID, value, COMM_TIMEOUT_INTERVAL)

		self.check_timeout (timeout, 'Set current')
		self.cs_value = value
		return set_value

	def _VS_setVoltage (self, value):

		self.check_connected()

		set_value, timeout = libxsmu.VS_setVoltage (
			self.deviceID, value, COMM_TIMEOUT_INTERVAL)

		self.check_timeout (timeout, 'Set voltage')
		self.vs_value = value
		return set_value

	def _CM_setRange (self, range):

		self.check_connected()

		if self.cm_range == None or self.cm_range != range:

			range, timeout = libxsmu.CM_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set ammeter range')

		self.cm_range = range
		return range

	def _VM_setRange (self, range):

		self.check_connected()

		if self.vm_range == None or self.vm_range != range:

			range, timeout = libxsmu.VM_setRange (
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

			timeout      = COMM_TIMEOUT_INTERVAL
			filterLength = 1

			(voltage, timeout) = libxsmu.VM_getReading (
				self.deviceID, filterLength, timeout)

			self.check_timeout (timeout, 'Get voltmeter reading')

			(low, hi) = limits[self.vm_range]

			if abs (voltage) < low:

				range = self.vm_range - 1
				if range < VM_RANGE_MIN : break
				else                    : self._VM_setRange (range)

			elif abs (voltage) > hi:

				range = self.vm_range + 1
				if range > VM_RANGE_MAX : break
				else                    : self._VM_setRange (range)

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

		if (libxsmu.firmware_version (self.deviceID)
				>= libxsmu.make_version (2, 2, 0)):

			timeout += filterLength * 0.022

		else:
			timeout += filterLength * 0.01

		(voltage, timeout) = libxsmu.VM_getReading (
			self.deviceID, filterLength, timeout)

		self.check_timeout (timeout, 'Get voltmeter reading')

		return voltage

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _VM2_setRange (self, range):

		self.check_connected()

		if self.vm2_range == None or self.vm2_range != range:

			range, timeout = libxsmu.VM2_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set drive-sense range')

		self.vm2_range = range
		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _VM2_doAutoRange (self):

		limits = [(0.99 * 0.1 * rng, 1.01 * rng) for rng in VM2_RANGES]

		self.check_connected()

		if self.vm2_range == None:
			self._VM2_setRange (VM2_RANGE_MAX)

		while True:

			timeout      = COMM_TIMEOUT_INTERVAL
			filterLength = 1

			(voltage, timeout) = libxsmu.VM2_getReading (
				self.deviceID, filterLength, timeout)

			self.check_timeout (timeout, 'Get drive reading')

			(low, hi) = limits[self.vm2_range]

			if abs (voltage) < low:

				range = self.vm2_range - 1
				if range < VM2_RANGE_MIN : break
				else                     : self._VM2_setRange (range)

			elif abs (voltage) > hi:

				range = self.vm2_range + 1
				if range > VM2_RANGE_MAX : break
				else                     : self._VM2_setRange (range)

			else: break

		return self.vm2_range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM2_setRange (self, autorange, range):

		self.check_connected()
		self.vm2_autorange = autorange

		if autorange:
			range = self._VM2_doAutoRange()

		else:
			range = self._VM2_setRange (range)

		self.do_callback (VM2_RANGE_CHANGED, autorange, range)
		return (autorange, range)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VM2_getReading (self, filterLength = 128):

		if self.vm2_autorange:
			range = self._VM2_doAutoRange()
			self.do_callback (VM2_RANGE_CHANGED, self.vm2_autorange, range)

		self.check_connected()
		timeout = COMM_TIMEOUT_INTERVAL

		if (libxsmu.firmware_version (self.deviceID)
				>= libxsmu.make_version (2, 2, 0)):

			timeout += filterLength * 0.022

		else:
			timeout += filterLength * 0.01

		(voltage, timeout) = libxsmu.VM2_getReading (
			self.deviceID, filterLength, timeout)

		self.check_timeout (timeout, 'Get drive reading')
		return voltage

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CM_doAutoRange (self):

		limits = [(0.99 * 0.1 * rng, 1.01 * rng) for rng in CM_RANGES]

		self.check_connected()
		if self.cm_range == None: self._CM_setRange (CM_RANGE_MAX)

		while True:

			timeout      = COMM_TIMEOUT_INTERVAL
			filterLength = 1

			(current, timeout) = libxsmu.CM_getReading (
				self.deviceID, filterLength, timeout)

			self.check_timeout (timeout, 'Get ammeter reading')

			(low, hi) = limits[self.cm_range]

			if abs (current) < low:

				range = self.cm_range - 1
				if range < CM_RANGE_MIN : break
				else                    : self._CM_setRange (range)

			elif abs (current) > hi:

				range = self.cm_range + 1
				if range > CM_RANGE_MAX : break
				else                    : self._CM_setRange (range)

			else: break

		return self.cm_range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_setRange (self, autorange, range):

		self.check_connected()
		self.cm_autorange = autorange

		if self.src_mode != SOURCE_MODE_CS:

			if autorange:
				range = self._CM_doAutoRange()

			else:
				range = self._CM_setRange (range)

		else: range = self.cm_range

		self.do_callback (CM_RANGE_CHANGED, autorange, range)
		return (autorange, range)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_getReading (self, filterLength = 128):
	
                
		self.check_connected()
                
                
		if self.src_mode != SOURCE_MODE_CS and self.cm_autorange:
			range = self._CM_doAutoRange()
			self.do_callback (CM_RANGE_CHANGED, self.cm_autorange, range)
		
		
		timeout = COMM_TIMEOUT_INTERVAL

		if (libxsmu.firmware_version (self.deviceID)
				>= libxsmu.make_version (2, 2, 0)):

			timeout += filterLength * 0.022

		else:
			timeout += filterLength * 0.01
			
		
		(current, timeout) = \
			libxsmu.CM_getReading (self.deviceID, filterLength, timeout)
		
		self.check_timeout (timeout, 'Get ammeter reading')
		
		return current

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CM_findRange (self, value):

		range = CM_RANGE_MIN

		while True:

			if abs (value) > CM_RANGES [range]:
				if range + 1 > CM_RANGE_MAX : break
				else                        : range += 1

			else : break

		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _VS_findRange (self, value):

		range = VS_RANGE_MIN

		while True:

			if abs (value) > VS_RANGES [range]:
				if range + 1 > VS_RANGE_MAX : break
				else                        : range += 1

			else : break

		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setSourceParameters (self, mode, autorange, range, value):

		self.check_connected()

		self.src_autorange = autorange
		mode               = self._setSourceMode (mode)

		# +++++++++++++++++++++++++++++++++++++++++++
		# Finding source range

		if autorange:

			find_range = {
				SOURCE_MODE_CS : self._CM_findRange,
				SOURCE_MODE_VS : self._VS_findRange}.get (mode)

			range = find_range (value)

		# +++++++++++++++++++++++++++++++++++++++++++
		# Settings source range

		set_range = {
			SOURCE_MODE_CS : self._CM_setRange,
			SOURCE_MODE_VS : self._VS_setRange}.get (mode)

		range = set_range (range)

		# +++++++++++++++++++++++++++++++++++++++++++
		# Setting source value

		set_output = {
			SOURCE_MODE_CS : self._CS_setCurrent,
			SOURCE_MODE_VS : self._VS_setVoltage}.get (mode)

		value = set_output (value)

		self.do_callback (
			SOURCE_PARAMETERS_CHANGED,
			mode, autorange, range, value)

		return (mode, autorange, range, value)

	def acquire_lock (self):
		self._thlock.acquire()

	def release_lock (self):
		self._thlock.release()

'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''

class _Applet:

	def __init__ (self, oXSMU):
		self.oXSMU = oXSMU
		self._plots = {}
		self._taskq = XTaskQueue()
		self._lastPlotUpdateAt = 0.0
		self._hApplet = self.oXSMU.oApp.master.after (50, self._applet)

	def _applet (self):

		self._taskq.process()
		oApp = self.oXSMU.oApp

		t = systime()
		if t >= self._lastPlotUpdateAt + 2:
			self._lastPlotUpdateAt = t

			for (wPlot, traceID) in self._plots.values():
				if wPlot.damaged() : wPlot.redraw()

		self._hApplet = oApp.master.after (50, self._applet)

	def schedule_task (self, task, *args):
		return self._taskq.push (task, *args)

	def refresh (self):
		self.oXSMU.oApp.master.update()

	def close (self):
		oApp = self.oXSMU.oApp
		oApp.close()
		oApp.master.after_cancel (self._hApplet)
		oApp.master.destroy()

	# +++++++++++++ Update display functions +++++++++++++++

	def set_status (self, status):
		self.oXSMU.oApp.set_status (status)

	def setConnection (self, status):
		self.oXSMU.oApp.setConnection (status)

	def CM_setReading (self, range, reading):
		self.oXSMU.oApp.CM_setReading (range, reading)

	def VM_setReading (self, range, reading):
		self.oXSMU.oApp.VM_setReading (range, reading)

	def VM2_setReading (self, range, reading):
		self.oXSMU.oApp.VM2_setReading (range, reading)

	def initPlot (self, thread, title, xlabel, ylabel):
		oApp = self.oXSMU.oApp
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
		oApp = self.oXSMU.oApp
		oApp.clearPlot()
		self._plots.clear()

	def CM_setRange (self, autorange, range):
		self.oXSMU.oApp.CM_setRange (autorange, range)
		self.oXSMU.meterParameters.CM_setRange (autorange, range)
		self.oXSMU.sourceParameters.CS_setRange (range)

	def VM_setRange (self, autorange, range):
		self.oXSMU.oApp.VM_setRange (autorange, range)
		self.oXSMU.meterParameters.VM_setRange (autorange, range)

	def VM2_setRange (self, autorange, range):
		self.oXSMU.oApp.VM2_setRange (autorange, range)
		self.oXSMU.meterParameters.VM2_setRange (autorange, range)

	def setSourceParameters (self, mode, autorange, range, value):

		oXSMU   = self.oXSMU
		oApp    = self.oXSMU.oApp

		oApp.setSourceParameters (mode, autorange, range, value)
		oXSMU.sourceParameters.set (mode, autorange, range, value)

		if mode == SOURCE_MODE_CS:
			(cm_autorange, cm_range,
			 vm_autorange, vm_range,
			 vm2_autorange, vm2_range) = oXSMU.meterParameters.get()

			oApp.CM_setRange (cm_autorange, range)
			oXSMU.meterParameters.CM_setRange (cm_autorange, range)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, mode):
		self.oXSMU.oApp.setRunMode (mode)

	def setRunControlStatus (self, status):
		self.oXSMU.oApp.setRunControlStatus (status)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setAcquisitionSettings (self, delay, filterLength):
		self.oXSMU.oApp.setAcquisitionSettings (delay, filterLength)
		self.oXSMU.acquisitionSettings.set (delay, filterLength)

	def setIVRampSettings (
		self, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.oXSMU.oApp.setIVRampSettings (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

		self.oXSMU.ivRampSettings.set (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)
	
	def setIVTimeResolvedRampSettings (
		self, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.oXSMU.oApp.setIVTimeResolvedRampSettings (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

		self.oXSMU.ivTimeResolvedRampSettings.set (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setOhmmeterSettings (
		self, maxCurrent, maxVoltage,
		maxPower, bipolar, resTrackMode):

		self.oXSMU.oApp.setOhmmeterSettings (
			maxCurrent, maxVoltage, maxPower, bipolar, resTrackMode)

		self.oXSMU.ohmmeterSettings.set (
			maxCurrent, maxVoltage, maxPower, bipolar, resTrackMode)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquisition_atexit (self):
		self.oXSMU.releaseAcquisition()

	def devicethread_atexit (self):
		self.oXSMU.releaseDeviceThread();

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _DeviceThread (XThread):

	def __init__ (self, oXSMU):

		XThread.__init__ (self, daemon = True)

		self.oXSMU = oXSMU

		'''
			Register driver callback
		'''
		oDriver = self.oXSMU.oDriver

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
				oApplet = self.oXSMU.oApplet
				oApplet.schedule_task (oApplet.set_status, str (e))

			except XTerminate: break

		self.disconnectDevice()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _DriverCB (self, context, *args):

		oApplet = self.oXSMU.oApplet

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

		elif context == VM2_RANGE_CHANGED:
			oApplet.schedule_task (oApplet.VM2_setRange, *args).wait()

		elif context == SOURCE_PARAMETERS_CHANGED:
			oApplet.schedule_task (oApplet.setSourceParameters, *args).wait()

		else : raise ValueError (context)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquire_n_display (self):

		(cm_range, vm_range, vm2_range, datapoint) = self.acquire()

		oApplet = self.oXSMU.oApplet

		oApplet.schedule_task (
			oApplet.CM_setReading, cm_range, datapoint.current)

		oApplet.schedule_task (
			oApplet.VM_setReading, cm_range, datapoint.voltage)

		oApplet.schedule_task (
			oApplet.VM2_setReading, vm2_range, datapoint.vsrc)

		return datapoint

	def acquire (self):
		oXSMU   = self.oXSMU
		oDriver = oXSMU.oDriver

		try:
			oXSMU.acquire_lock()
			oXSMU.adjustMeterRanges()

			(current, voltage, vsrc) = oXSMU.measureIVV2 (filterLength = 1)

			cm_range  = oDriver.cm_range
			vm_range  = oDriver.vm_range
			vm2_range = oDriver.vm2_range

		finally:
			oXSMU.release_lock()

		return (cm_range, vm_range, vm2_range,
		  DataPoint (current = current, voltage = voltage, vsrc = vsrc))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	'''
		Connection functions
	'''

	def connectDevice (self):

		oDriver = self.oXSMU.oDriver
		oApplet = self.oXSMU.oApplet

		oApplet.schedule_task (oApplet.setConnection, DEVICE_CONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.open (get_XSMU_serialNo())

		finally:
			oDriver.release_lock()

	def disconnectDevice (self):

		oDriver = self.oXSMU.oDriver
		oApplet = self.oXSMU.oApplet

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
	def setSourceParameters (self, mode, autorange, range, value):

		oDriver = self.oXSMU.oDriver
		oApplet = self.oXSMU.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.setSourceParameters (mode, autorange, range, value)

		finally:
			oDriver.release_lock()

	'''
		Meter parameters
	'''

	def CM_setRange (self, autorange, range):

		oDriver = self.oXSMU.oDriver
		oApplet = self.oXSMU.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.CM_setRange (autorange, range)

		finally:
			oDriver.release_lock()

	def VM_setRange (self, autorange, range):

		oDriver = self.oXSMU.oDriver
		oApplet = self.oXSMU.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.VM_setRange (autorange, range)

		finally:
			oDriver.release_lock()

	def VM2_setRange (self, autorange, range):

		oDriver = self.oXSMU.oDriver
		oApplet = self.oXSMU.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.VM2_setRange (autorange, range)

		finally:
			oDriver.release_lock()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def XSMU (master, sample):

	if not XSMU.singleton:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()

		oApp           = GUI (win, sample)
		XSMU.singleton = _XSMU (oApp, sample)

	if master not in XSMU.master:
		XSMU.master.append (master)

	return XSMU.singleton

def closeXSMU (master):

	if master in XSMU.master:
		XSMU.master.remove (master)

	if len (XSMU.master) == 0 and XSMU.singleton:
		XSMU.singleton.close()
		XSMU.singleton = None

XSMU.singleton = None
XSMU.master    = []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class SourceParameters:

	def __init__ (self, mode, autorange,
			   cm_range, cs_value, vs_range, vs_value):

		self.mode      = mode
		self.autorange = autorange
		self.cm_range  = cm_range
		self.cs_value  = cs_value
		self.vs_range  = vs_range
		self.vs_value  = vs_value

	def set (self, mode, autorange, range, value):

		if mode == SOURCE_MODE_CS:

			self.mode      = mode
			self.autorange = autorange
			self.cm_range  = range
			self.cs_value  = value

		elif mode == SOURCE_MODE_VS:

			self.mode      = mode
			self.autorange = autorange
			self.vs_range  = range
			self.vs_value  = value

		else: raise ValueError (mode)

	def CS_setRange (self, range):
		self.cm_range = range

	def range (self, mode = None):

		if mode == None : mode = self.mode

		return {
			SOURCE_MODE_CS : self.cm_range,
			SOURCE_MODE_VS : self.vs_range}.get (mode)

	def value (self, mode = None):

		if mode == None : mode = self.mode

		return {
			SOURCE_MODE_CS : self.cs_value,
			SOURCE_MODE_VS : self.vs_value}.get (mode)

	def get (self):
		return (
			self.mode,
			self.autorange,
			self.range(),
			self.value())

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class MeterParameters:

	def __init__ (self, cm_autorange, cm_range,
			   vm_autorange, vm_range, vm2_autorange, vm2_range):

		self.CM_setRange (cm_autorange, cm_range)
		self.VM_setRange (vm_autorange, vm_range)
		self.VM2_setRange (vm2_autorange, vm2_range)

	def CM_setRange (self, cm_autorange, cm_range):
		self.cm_autorange = cm_autorange
		self.cm_range     = cm_range

	def VM_setRange (self, vm_autorange, vm_range):
		self.vm_autorange = vm_autorange
		self.vm_range     = vm_range

	def VM2_setRange (self, vm2_autorange, vm2_range):
		self.vm2_autorange = vm2_autorange
		self.vm2_range     = vm2_range

	def set (self,
			 cm_autorange  = None, cm_range  = None,
			 vm_autorange  = None, vm_range  = None,
			 vm2_autorange = None, vm2_range = None):

		if cm_autorange  != None : self.cm_autorange  = cm_autorange
		if cm_range      != None : self.cm_range      = cm_range
		if vm_autorange  != None : self.vm_autorange  = vm_autorange
		if vm_range      != None : self.vm_range      = vm_range
		if vm2_autorange != None : self.vm2_autorange = vm2_autorange
		if vm2_range     != None : self.vm2_range     = vm2_range

	def get (self):
		return (
			self.cm_autorange,
			self.cm_range,
			self.vm_autorange,
			self.vm_range,
			self.vm2_autorange,
			self.vm2_range)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class AcquisitionSettings:

	def __init__ (self, delay, filterLength):
		self.set (delay, filterLength)

	def set (self, delay, filterLength):
		self.delay        = delay
		self.filterLength = filterLength

	def get (self):
		return (
			self.delay,
			self.filterLength)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class IVRampSettings:

	def __init__ (self, finalCurrent, finalVoltage, maxPower,
			   currentStep, voltageStep, bipolar, resTrackMode):

		self.set (finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

	def set (self, finalCurrent, finalVoltage, maxPower,
		  currentStep, voltageStep, bipolar, resTrackMode):

		self.finalCurrent = finalCurrent
		self.finalVoltage = finalVoltage
		self.maxPower     = maxPower
		self.currentStep  = currentStep
		self.voltageStep  = voltageStep
		self.bipolar      = bipolar
		self.resTrackMode = resTrackMode

	def get (self):
		return (
			self.finalCurrent,
			self.finalVoltage,
			self.maxPower,
			self.currentStep,
			self.voltageStep,
			self.bipolar,
			self.resTrackMode)

class IVTimeResolvedRampSettings:

	def __init__ (self, finalCurrent, finalVoltage, maxPower,
			   currentStep, voltageStep, bipolar, resTrackMode):

		self.set (finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

	def set (self, finalCurrent, finalVoltage, maxPower,
		  currentStep, voltageStep, bipolar, resTrackMode):

		self.finalCurrent = finalCurrent
		self.finalVoltage = finalVoltage
		self.maxPower     = maxPower
		self.currentStep  = currentStep
		self.voltageStep  = voltageStep
		self.bipolar      = bipolar
		self.resTrackMode = resTrackMode

	def get (self):
		return (
			self.finalCurrent,
			self.finalVoltage,
			self.maxPower,
			self.currentStep,
			self.voltageStep,
			self.bipolar,
			self.resTrackMode)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class OhmmeterSettings:

	def __init__ (self, maxCurrent, maxVoltage,
			   maxPower, bipolar, resTrackMode):

		self.set (maxCurrent, maxVoltage,
			maxPower, bipolar, resTrackMode)

	def set (self, maxCurrent, maxVoltage,
		  maxPower, bipolar, resTrackMode):

		self.maxCurrent   = maxCurrent
		self.maxVoltage   = maxVoltage
		self.maxPower     = maxPower
		self.bipolar      = bipolar
		self.resTrackMode = resTrackMode

	def get (self):
		return (
			self.maxCurrent,
			self.maxVoltage,
			self.maxPower,
			self.bipolar,
			self.resTrackMode)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _XSMU:

	def __init__ (self, oApp, sample):

		self.oApp = oApp
		self.sample = sample
		oDriver = self.oDriver = _Driver()

		# ++++ Device parameters ++++

		self.sourceParameters = SourceParameters (
			mode      = SOURCE_MODE_CS, autorange = True,
			cm_range  = CM_RANGE_10mA,  cs_value  = 0.0,
			vs_range  = VS_RANGE_10V,   vs_value  = 0.0)

		self.meterParameters = MeterParameters (
			cm_autorange = True, cm_range = CM_RANGE_10mA,
			vm_autorange = True, vm_range = VM_RANGE_10V,
			vm2_autorange = True, vm2_range = VM2_RANGE_10V)

		self.max_current   = 10e-3
		self.max_voltage   = 5.0
		self.max_power     = 50e-3
		self.run_mode      = RUN_MODE_RTime

		# ++++ Settings ++++

		self.acquisitionSettings = \
			AcquisitionSettings (delay = 2.0, filterLength = 16)

		self.ivRampSettings = IVRampSettings (
			finalCurrent = 10e-3,
			finalVoltage = 10.0,
			maxPower     = 100e-3,
			currentStep  = 1e-3,
			voltageStep  = 1.0,
			bipolar      = True,
			resTrackMode = R_TRACK_dV_dI)
		
		self.ivTimeResolvedRampSettings = IVTimeResolvedRampSettings (
			finalCurrent = 10e-3,
			finalVoltage = 10.0,
			maxPower     = 100e-3,
			currentStep  = 1e-3,
			voltageStep  = 1.0,
			bipolar      = True,
			resTrackMode = R_TRACK_V_I)

		self.ohmmeterSettings = OhmmeterSettings (
			maxCurrent   = 10e-3,
			maxVoltage   = 5.0,
			maxPower     = 100e-3,
			bipolar      = True,
			resTrackMode = R_TRACK_V_I)

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
			self.ivRampSettings.finalCurrent,
			self.ivRampSettings.finalVoltage,
			self.ivRampSettings.maxPower,
			self.ivRampSettings.currentStep,
			self.ivRampSettings.voltageStep,
			self.ivRampSettings.bipolar,
			self.ivRampSettings.resTrackMode)
		
		oApplet.schedule_task (
			oApplet.setIVTimeResolvedRampSettings,
			self.ivTimeResolvedRampSettings.finalCurrent,
			self.ivTimeResolvedRampSettings.finalVoltage,
			self.ivTimeResolvedRampSettings.maxPower,
			self.ivTimeResolvedRampSettings.currentStep,
			self.ivTimeResolvedRampSettings.voltageStep,
			self.ivTimeResolvedRampSettings.bipolar,
			self.ivTimeResolvedRampSettings.resTrackMode)

		oApplet.schedule_task (
			oApplet.setOhmmeterSettings,
			self.ohmmeterSettings.maxCurrent,
			self.ohmmeterSettings.maxVoltage,
			self.ohmmeterSettings.maxPower,
			self.ohmmeterSettings.bipolar,
			self.ohmmeterSettings.resTrackMode)

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
			oDeviceThread.setSourceParameters,
			self.sourceParameters.mode, self.sourceParameters.autorange,
			self.sourceParameters.range(), self.sourceParameters.value())

		oDeviceThread.schedule_task (
			oDeviceThread.CM_setRange,
			self.meterParameters.cm_autorange,
			self.meterParameters.cm_range)

		oDeviceThread.schedule_task (
			oDeviceThread.VM_setRange,
			self.meterParameters.vm_autorange,
			self.meterParameters.vm_range)

		oDeviceThread.schedule_task (
			oDeviceThread.VM2_setRange,
			self.meterParameters.vm2_autorange,
			self.meterParameters.vm2_range)

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
				'XSMU_ResourceError: Device thread unavailable')

		return thread

	def releaseDeviceThread (self):
		self.oDeviceThread = None

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def oAppCB (self, context, *args):

		oApplet = self.oApplet
		oDeviceThread = self.oDeviceThread

		if   context == CONNECT_DEVICE    : self.connectDevice()
		elif context == DISCONNECT_DEVICE : self.disconnectDevice()

		elif context == RUN_MODE          :
			oApplet.schedule_task (oApplet.setRunMode, *args)

		elif context == START_RUN         : self.startRun (*args)
		elif context == FINISH_RUN        : self.finishRun()
		elif context == OPEN_DIALOG       : self.openDialog (*args)
		elif context == OPEN_METHOD       : self.openMethod (*args)
		elif context == SAVE_METHOD       : self.saveMethod (*args)

		else: raise ValueError (context)

	# ++++++++++++++++++++++++++++++++++++++++'NoneType+++++++++++++++++++

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

			elif mode == RUN_MODE_VTime:
				module = _VTimeModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

			elif mode == RUN_MODE_IV:
				module = _IVModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

				module.initIVRampSettings (
					self.ivRampSettings.finalCurrent,
					self.ivRampSettings.finalVoltage,
					self.ivRampSettings.maxPower,
					self.ivRampSettings.currentStep,
					self.ivRampSettings.voltageStep,
					self.ivRampSettings.bipolar,
					self.ivRampSettings.resTrackMode)
			
			elif mode == RUN_MODE_IV_TIME_RESOLVED:
				module = _IVTimeResolvedModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

				module.initIVTimeResolvedRampSettings (
					self.ivTimeResolvedRampSettings.finalCurrent,
					self.ivTimeResolvedRampSettings.finalVoltage,
					self.ivTimeResolvedRampSettings.maxPower,
					self.ivTimeResolvedRampSettings.currentStep,
					self.ivTimeResolvedRampSettings.voltageStep,
					self.ivTimeResolvedRampSettings.bipolar,
					self.ivTimeResolvedRampSettings.resTrackMode)

			elif mode == RUN_MODE_RTime:
				module = _RTimeModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

				module.initOhmmeterSettings (
					self.ohmmeterSettings.maxCurrent,
					self.ohmmeterSettings.maxVoltage,
					self.ohmmeterSettings.maxPower,
					self.ohmmeterSettings.bipolar,
					self.ohmmeterSettings.resTrackMode)

			else:
				raise ResourceError (
					'XSMU_ResourceError: Module creation failed')

			self.oModule = module

		else:
			raise ResourceError (
				'XSMU_ResourceError: Module unavailable')

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

				elif mode == RUN_MODE_VTime:
					thread = _VTimeAcquisitionThread (module)

				elif mode == RUN_MODE_IV:
					thread = _IVAcquisitionThread (module)
				
				elif mode == RUN_MODE_IV_TIME_RESOLVED:
					thread = _IVTimeResolvedAcquisitionThread (module)

				elif mode == RUN_MODE_RTime:
					thread = _RTimeAcquisitionThread (module)

				else:
					raise ResourceError (
						'XSMU_ResourceError: Thread creation failed')

				thread.atexit (self.acquisition_atexit)
				self.oAcqThread = thread

			else:
				raise ResourceError (
					'XSMU_ResourceError: Thread unavailable')

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
		
		elif dialog == IV_TIME_RESOLVED_RAMP_SETTINGS_DIALOG:
			self.openIVTimeResolvedRampDialog()

		elif dialog == OHMMETER_SETTINGS_DIALOG:
			self.openOhmmeterDialog()

		else: raise ValueError (dialog)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openSourceDialog (self):

		# Creates a GUI_SourceParameters dialog

		w = self.dialog = GUI_SourceParameters (
			Toplevel (takefocus = True),
			self.sourceParameters.mode,
			self.sourceParameters.autorange,
			self.sourceParameters.range (SOURCE_MODE_CS),
			self.sourceParameters.value (SOURCE_MODE_CS),
			self.sourceParameters.range (SOURCE_MODE_VS),
			self.sourceParameters.value (SOURCE_MODE_VS))

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
				oDeviceThread.setSourceParameters, *args)

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
			self.sourceParameters.mode,
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

		oApplet    = self.oApplet
		oModule    = self.oModule

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
			self.ivRampSettings.finalCurrent,
			self.ivRampSettings.finalVoltage,
			self.ivRampSettings.maxPower,
			self.ivRampSettings.currentStep,
			self.ivRampSettings.voltageStep,
			self.ivRampSettings.bipolar,
			self.ivRampSettings.resTrackMode)

		w.callback (self.ivRampDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)
	
	def openIVTimeResolvedRampDialog (self):

		w = self.dialog = GUI_IVTimeResolvedRampSettings (
			Toplevel (takefocus = True),
			self.ivTimeResolvedRampSettings.finalCurrent,
			self.ivTimeResolvedRampSettings.finalVoltage,
			self.ivTimeResolvedRampSettings.maxPower,
			self.ivTimeResolvedRampSettings.currentStep,
			self.ivTimeResolvedRampSettings.voltageStep,
			self.ivTimeResolvedRampSettings.bipolar,
			self.ivTimeResolvedRampSettings.resTrackMode)

		w.callback (self.ivTimeResolvedRampDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def ivRampDialogCB (self, context, *args):

		oApplet    = self.oApplet
		oModule    = self.oModule

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
	
	def ivTimeResolvedRampDialogCB (self, context, *args):

		oApplet    = self.oApplet
		oModule    = self.oModule

		if context == APPLY:

			oApplet.schedule_task (oApplet.setIVTimeResolvedRampSettings, *args)

			if oModule and isinstance (oModule, _IVModule):
				oModule.schedule_task (oModule.setIVTimeResolvedRampSettings, *args)

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
			self.ohmmeterSettings.maxCurrent,
			self.ohmmeterSettings.maxVoltage,
			self.ohmmeterSettings.maxPower,
			self.ohmmeterSettings.bipolar,
			self.ohmmeterSettings.resTrackMode)

		w.callback (self.ohmmeterDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def ohmmeterDialogCB (self, context, *args):

		oApplet    = self.oApplet
		oModule    = self.oModule

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

	def doExcitationAutoTune (self, track_mode):

		print "Auto-tuning excitation ..."

		# track_mode is not used

		oDriver = self.oDriver
		src_mode = self.sourceParameters.mode

		if src_mode == None:
			src_mode = SOURCE_MODE_CS

		# First try with existing source mode

		value = {
			SOURCE_MODE_CS : self.max_current,
			SOURCE_MODE_VS : self.max_voltage
			}[src_mode]

		try:
			oDriver.acquire_lock()
			oDriver.setSourceParameters (
				src_mode, self.sourceParameters.autorange,
				self.sourceParameters.range (src_mode), value)

		finally:
			oDriver.release_lock()

		(current, vsrc) = self.measureIV2 (filterLength = 1)

		observable = {
			SOURCE_MODE_CS : abs (vsrc),
			SOURCE_MODE_VS : abs (current)
			}[src_mode]

		limit = 1.01 * {
			SOURCE_MODE_CS : abs (self.max_voltage),
			SOURCE_MODE_VS : abs (self.max_current)
			}[src_mode]

		# Check if compliance is hit
		# If yes, then switch to alternate source mode

		if (observable > limit):

			src_mode = {
				SOURCE_MODE_CS : SOURCE_MODE_VS,
				SOURCE_MODE_VS : SOURCE_MODE_CS
				}[src_mode]

			value = {
				SOURCE_MODE_CS : self.max_current,
				SOURCE_MODE_VS : self.max_voltage
				}[src_mode]

			try:
				oDriver.acquire_lock()
				oDriver.setSourceParameters (
					src_mode, self.sourceParameters.autorange,
					self.sourceParameters.range (src_mode), value)

			finally:
				oDriver.release_lock()

			(current, vsrc) = self.measureIV2 (filterLength = 1)

		# Check if power limit is hit
		# If yes, do a binary search in I-V space

		power = abs (current * vsrc)

		power_limited = False
		if (power > 1.01 * self.max_power):

			minfrac = 0.0
			maxfrac = 1.0
			power_limited = True

			# (100uA/65536) in 10mA range = 22 bits resolution
			for Try in range(22):

				midfrac  = (minfrac + maxfrac) / 2

				value = midfrac * {
					SOURCE_MODE_CS : self.max_current,
					SOURCE_MODE_VS : self.max_voltage
					}[src_mode]

				try:
					oDriver.acquire_lock()
					oDriver.setSourceParameters (
						src_mode, self.sourceParameters.autorange,
						self.sourceParameters.range (src_mode), value)

				finally:
					oDriver.release_lock()

				(current, vsrc) = self.measureIV2 (filterLength = 1)

				power = abs (current * vsrc)
				if   (power > 1.01 * self.max_power) : maxfrac = midfrac
				elif (power < 0.99 * self.max_power) : minfrac = midfrac
				else                                 : break

		(mode, mult, unit, fmt) = {
			SOURCE_MODE_CS : ("Current", 1e3, "mA", "%+.6f"),
			SOURCE_MODE_VS : ("Voltage", 1e3, "mV", "%+.1f")
			}[src_mode]

		print (
			"Source mode: " + mode + "\n"
			"Setpoint: " + str (fmt % (mult * value)) + unit + "\n" +
			"Power: " + str ("%.3f" % (1e3 * power)) + "mW" + "\n")

		return (src_mode, value, power_limited)

	def setExcitationLimits (self, max_current, max_voltage, max_power):
		self.max_current = max_current
		self.max_voltage = max_voltage
		self.max_power   = max_power

	# Useful functions callable from other modules

	def output_off (self):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			src_mode = SOURCE_MODE_CS

			oDriver.setSourceParameters (
				src_mode, self.sourceParameters.autorange,
				self.sourceParameters.range (src_mode), 0.0)

			sleep (1)
			vsrc = abs (oDriver.VM2_getReading (filterLength = 1))

			if vsrc > 0.01:

				src_mode = SOURCE_MODE_VS

				oDriver.setSourceParameters (
					src_mode, self.sourceParameters.autorange,
					self.sourceParameters.range (src_mode), 0.0)

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

			if self.meterParameters.vm2_autorange:
				oDriver.VM2_getReading (filterLength = 1)

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

	def measureV2 (self, filterLength):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			vsrc = oDriver.VM2_getReading (filterLength)

		finally:
			oDriver.release_lock()

		return vsrc

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

	def measureIV2 (self, filterLength):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			current = oDriver.CM_getReading  (filterLength)
			voltage = oDriver.VM2_getReading (filterLength)

		finally:
			oDriver.release_lock()

		return (current, voltage)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def measureIVV2 (self, filterLength):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			current = oDriver.CM_getReading  (filterLength)
			voltage = oDriver.VM_getReading  (filterLength)
			vsrc    = oDriver.VM2_getReading (filterLength)

		finally:
			oDriver.release_lock()

		return (current, voltage, vsrc)

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

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			mode      = self.sourceParameters.mode
			autorange = self.sourceParameters.autorange
			range     = self.sourceParameters.range()
			value     = self.sourceParameters.value()

			# ++++++++++++++++++++++++++

			# Measure positive values
			oDriver.setSourceParameters (mode, autorange, range, value)

			self.adjustMeterRanges()
			self.sleep (delay, bg_task, *bg_tasks)

			(posI, posV, posVsrc) = self.measureIVV2 (filterLength)

			# Measure negetive values
			if bipolar:

				oDriver.setSourceParameters (mode, autorange, range, -value)

				self.adjustMeterRanges()
				self.sleep (delay, bg_task, *bg_tasks)

				(negI, negV, negVsrc) = self.measureIVV2 (filterLength)

			# Calculate delta I and delta V
			if bipolar:
				delV = abs (posV - negV) / 2.0
				delI = abs (posI - negI) / 2.0
				delVsrc = abs (posVsrc - negVsrc) / 2.0

			else:
				delV = abs (posV)
				delI = abs (posI)
				delVsrc = abs (posVsrc)

			# Calculate resistance
			try:
				resistance = delV / delI

			except ZeroDivisionError:
				resistance = float ('inf')

			oDriver.setSourceParameters (mode, autorange, range, value)

		finally:
			oDriver.release_lock()

		return (delI, delV, delVsrc, resistance)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMethod (self):
		method = Method()
		method.setSourceParameters             (*self.sourceParameters.get())
		method.setMeterParameters              (*self.meterParameters.get())
		method.setAcquisitionSettings          (*self.acquisitionSettings.get())
		method.set_IV_RampSettings             (*self.ivRampSettings.get())
		method.set_IV_TimeResolvedRampSettings (*self.ivTimeResolvedRampSettings.get())
		method.setOhmmeterSettings             (*self.ohmmeterSettings.get())
		return method

	def applyMethod (self, method):
		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread
		oModule       = self.oModule

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		self.sourceParameters.set (
			*method.getSourceParameters (
				*self.sourceParameters.get()))

		oDeviceThread.schedule_task (
			oDeviceThread.setSourceParameters,
			*self.sourceParameters.get())

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
		
		settings = method.get_IV_TimeResolvedRampSettings (*self.ivRampSettings.get())

		oApplet.schedule_task (oApplet.setIVTimeResolvedRampSettings, *settings)

		if oModule and isinstance (oModule, _IVModule):
			oModule.schedule_task (
				oModule.setIVTimeResolvedRampSettings, *settings)

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

	def __init__ (self, master, oXSMU):
		XThreadModule.__init__ (self, master)
		self.oXSMU        = oXSMU
		self.t0           = systime()
		self.dataset      = DataSet()
		self.fd_log       = None
		self._alive       = False

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
		return 'xsmu'

	def is_alive (self):
		return True if self._alive else False

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def initAcquisitionSettings (self, delay, filterLength):
		self.delay        = delay
		self.filterLength = filterLength

	def setAcquisitionSettings (self, delay, filterLength):
		self.initAcquisitionSettings (delay, filterLength)
		oApplet = self.oXSMU.oApplet
		text = 'Acquisition settings updated'
		oApplet.schedule_task (oApplet.set_status, text)

	def init (self):

		oXSMU         = self.oXSMU
		oApplet       = oXSMU.oApplet
		self._alive   = True

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

		oXSMU   = self.oXSMU
		oApplet = oXSMU.oApplet
		oApplet.schedule_task (oApplet.setRunControlStatus, RUN_FINISHING)

		# Resets excitation voltage
		try:
			oXSMU.output_off()

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
			('Time',       '%12s', 'sec'),
			('Current',    '%12s',   'A'),
			('Voltage',    '%12s',   'V'),
			('Vsrc',       '%12s',   'V'),
			('Resistance', '%12s', 'ohm')
		]

		(sampleName, sampleID, sampleDescription) = self.oXSMU.sample.get()
		self.fd_log.write ('#Sample name        : ' + sampleName        + '\n')
		self.fd_log.write ('#Sample ID          : ' + sampleID          + '\n')

		label =            '#Sample description : '
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
			('Time       : ', '%12.1f', datapoint.time,       'sec'),
			('Current    : ', '%12.9f', datapoint.current,      'A'),
			('Voltage    : ', '%12.6f', datapoint.voltage,      'V'),
			('Vsrc       : ', '%12.6f', datapoint.vsrc,         'V'),
			('Resistance : ', '%12.6f', datapoint.resistance, 'ohm')
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
		dict.set_sample (self.oXSMU.sample.get())
		#dict.set_events ({})

		fields = [
			('01 Time',       DATASET_COL_TIME,       'second'),
			('02 Current',    DATASET_COL_CURRENT,         'A'),
			('03 Voltage',    DATASET_COL_VOLTAGE,         'V'),
			('04 Vsrc',       DATASET_COL_VSRC,            'V'),
			('05 Resistance', DATASET_COL_RESISTANCE,      'Ω')
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

		(sampleName, sampleID, _) = self.oXSMU.sample.get()

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

	def __init__ (self, master, oXSMU):
		_Module.__init__ (self, master, oXSMU)

	def run_type (self):
		return 'I_Time'

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Current (A)'

	def init (self):
		_Module.init (self)

		oXSMU   = self.oXSMU
		oApplet = oXSMU.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_ITime)

	def acquire (self, bg_task = None, *bg_tasks):

		oXSMU = self.oXSMU
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		# ++++++++++++++++++++++++++++++

		try:
			oXSMU.acquire_lock()
			current = oXSMU.measureI (self.filterLength)

		finally:
			oXSMU.release_lock()

		return DataPoint (time = t, current = current)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oXSMU   = self.oXSMU
		oApplet = oXSMU.oApplet
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
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _VTimeModule (_Module):

	def __init__ (self, master, oXSMU):
		_Module.__init__ (self, master, oXSMU)

	def run_type (self):
		return 'V_Time'

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Voltage (V)'

	def init (self):
		_Module.init (self)

		oXSMU   = self.oXSMU
		oApplet = oXSMU.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_VTime)

	def acquire (self, bg_task = None, *bg_tasks):

		oXSMU = self.oXSMU
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		# ++++++++++++++++++++++++++++++

		try:
			oXSMU.acquire_lock()
			voltage = oXSMU.measureV (self.filterLength)

		finally:
			oXSMU.release_lock()

		return DataPoint (time = t, voltage = voltage)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oXSMU   = self.oXSMU
		oApplet = oXSMU.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			datapoint = self.acquire (self.do_tasks, bg_task, *bg_tasks)
			self.update_log (datapoint)
			self.dataset.append (datapoint)

			oApplet.schedule_task (
				oApplet.updatePlot, self, datapoint.time, datapoint.voltage)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _VTimeAcquisitionThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		lastPollAt = 0.0

		try:

			self.module.init()

			while True:
				self.do_tasks()
				self.module.sleep (1, self.do_tasks)
				self.module.acquire_n_plot()

		except (CommError, LinkError) : pass
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _IVModule (_Module):

	def __init__ (self, master, oXSMU):
		_Module.__init__ (self, master, oXSMU)
		self.excitationVoltage = None
		self.excitationCurrent = None
		self.scan_mode         = None
		self.power_limited     = False
		self._complete         = False

	def run_type (self):
		return 'IV'

	def xlabel (self):
		return 'Voltage (V)'

	def ylabel (self):
		return 'Current (A)'

	def init (self):
		_Module.init (self)

		oXSMU   = self.oXSMU
		oApplet = oXSMU.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_IV)

		self.excitationVoltage = None
		self.excitationCurrent = None
		self.scan_mode         = None
		self.power_limited     = False
		self._complete         = False

	def initIVRampSettings (
		self, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.finalCurrent = finalCurrent
		self.finalVoltage = finalVoltage
		self.maxPower     = maxPower
		self.currentStep  = currentStep
		self.voltageStep  = voltageStep
		self.bipolar      = bipolar
		self.resTrackMode = resTrackMode

	def setIVRampSettings (
		self, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.initIVRampSettings (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

		text = 'IV settings updated'
		oApplet = self.oXSMU.oApplet
		oApplet.schedule_task (oApplet.set_status, text)

	def acquire (self, bg_task = None, *bg_tasks):

		oXSMU = self.oXSMU
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		try:
			oXSMU.acquire_lock()
			(current, voltage, vsrc) = oXSMU.measureIVV2 (self.filterLength)

		finally:
			oXSMU.release_lock()

		return DataPoint (
			time    = t,
			current = current,
			voltage = voltage,
			vsrc    = vsrc)

	def breakPlot (self):

		oApplet = self.oXSMU.oApplet

		blank_datapoint = DataPoint (
			time    = None,
			current = None,
			voltage = None,
			vsrc    = None)

		self.dataset.append (blank_datapoint)

		oApplet.schedule_task (
			oApplet.updatePlot, self,
			blank_datapoint.voltage, blank_datapoint.current)

		return blank_datapoint

	def excite_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oXSMU.oApplet
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

		oXSMU = self.oXSMU

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
				oXSMU.acquire_lock()

				current = (
					self.excitationCurrent if self.currentStep != 0.0
					else copysign (self.finalCurrent, self.excitationVoltage))

				voltage = (
					self.excitationVoltage if self.voltageStep != 0.0
					else copysign (self.finalVoltage, self.excitationCurrent))

				if current == 0.0 or voltage == 0.0:
					oXSMU.output_off()

				else:
					oXSMU.setExcitationLimits (current, voltage, self.maxPower)

					(src_mode, value, self.power_limited) = (
						oXSMU.doExcitationAutoTune (
							track_mode = self.resTrackMode))

			finally:
				oXSMU.release_lock()

		return breakPlot

	def findNextPositiveExcitation (self, breakPlot):

		oXSMU = self.oXSMU

		if (self.excitationCurrent == None
		or  self.excitationVoltage == None):

			self.excitationCurrent = 0.0
			self.excitationVoltage = 0.0
			self.power_limited     = False

		elif (not self.power_limited
		and abs (self.excitationCurrent) < self.finalCurrent
		and abs (self.excitationVoltage) < self.finalVoltage):

				# Estimating next current

				if oXSMU.sourceParameters.mode == SOURCE_MODE_CS:
					nextCurrent = (
						oXSMU.sourceParameters.value() + self.currentStep)

				else:
					nextCurrent = (
						self.dataset[-1].current + self.currentStep)

				try:
					self.excitationCurrent = self.currentStep * round (
						nextCurrent / self.currentStep)

				except ZeroDivisionError:
					self.excitationCurrent = nextCurrent

				# Estimating next voltage

				if oXSMU.sourceParameters.mode == SOURCE_MODE_VS:
					nextVoltage = (
						oXSMU.sourceParameters.value() + self.voltageStep)

				else:
					nextVoltage = (
						self.dataset[-1].vsrc + self.voltageStep)

				try:
					self.excitationVoltage = self.voltageStep * round (
						nextVoltage / self.voltageStep)

				except ZeroDivisionError:
					self.excitationVoltage = nextVoltage

		else:
			self.excitationCurrent = None
			self.excitationVoltage = None

			if self.bipolar:
				breakPlot      = DO_BREAKPLOT
				self.scan_mode = SCAN_MODE_NEGATIVE

			else:
				self.scan_mode = None
				self._complete = True

		return breakPlot

	def findNextNegativeExcitation (self, breakPlot):

		oXSMU = self.oXSMU

		if (self.excitationCurrent == None
		or  self.excitationVoltage == None):

			self.excitationCurrent = 0.0
			self.excitationVoltage = 0.0
			self.power_limited     = False

		elif (not self.power_limited
		and abs (self.excitationCurrent) < self.finalCurrent
		and abs (self.excitationVoltage) < self.finalVoltage):

				# Estimating next current

				if oXSMU.sourceParameters.mode == SOURCE_MODE_CS:
					nextCurrent = (
						oXSMU.sourceParameters.value() - self.currentStep)

				else:
					nextCurrent = (
						self.dataset[-1].current - self.currentStep)

				try:
					self.excitationCurrent = self.currentStep * round (
						nextCurrent / self.currentStep)

				except ZeroDivisionError:
					self.excitationCurrent = nextCurrent

				# Estimating next voltage

				if oXSMU.sourceParameters.mode == SOURCE_MODE_VS:
					nextVoltage = (
						oXSMU.sourceParameters.value() - self.voltageStep)

				else:
					nextVoltage = (
						self.dataset[-1].vsrc - self.voltageStep)

				try:
					self.excitationVoltage = self.voltageStep * round (
						nextVoltage / self.voltageStep)

				except ZeroDivisionError:
					self.excitationVoltage = nextVoltage

		else:
			self.scan_mode = None
			self.excitationCurrent = None
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
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _IVTimeResolvedModule (_Module):

	def __init__ (self, master, oXSMU):
		_Module.__init__ (self, master, oXSMU)
		self.excitationVoltage = None
		self.excitationCurrent = None
		self.scan_mode         = None
		self.power_limited     = False
		self._complete         = False

	def run_type (self):
		return 'IV-Time-Resolved'

	def xlabel (self):
		return 'Voltage (V)'

	def ylabel (self):
		return 'Current (A)'

	def init (self):
		_Module.init (self)

		oXSMU   = self.oXSMU
		oApplet = oXSMU.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_IV_TIME_RESOLVED)

		self.excitationVoltage = None
		self.excitationCurrent = None
		self.scan_mode         = None
		self.power_limited     = False
		self._complete         = False

	def initIVTimeResolvedRampSettings (
		self, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.finalCurrent = finalCurrent
		self.finalVoltage = finalVoltage
		self.maxPower     = maxPower
		self.currentStep  = currentStep
		self.voltageStep  = voltageStep
		self.bipolar      = bipolar
		self.resTrackMode = resTrackMode

	def setIVTimeResolvedRampSettings (
		self, finalCurrent, finalVoltage, maxPower,
		currentStep, voltageStep, bipolar, resTrackMode):

		self.initIVTimeResolvedRampSettings (
			finalCurrent, finalVoltage, maxPower,
			currentStep, voltageStep, bipolar, resTrackMode)

		text = 'IV Time Resolved settings updated'
		oApplet = self.oXSMU.oApplet
		oApplet.schedule_task (oApplet.set_status, text)

	def acquire (self, bg_task = None, *bg_tasks):

		oXSMU = self.oXSMU
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		try:
			oXSMU.acquire_lock()
			(current, voltage, vsrc) = oXSMU.measureIVV2 (self.filterLength)

		finally:
			oXSMU.release_lock()

		return DataPoint (
			time    = t,
			current = current,
			voltage = voltage,
			vsrc    = vsrc)

	def breakPlot (self):

		oApplet = self.oXSMU.oApplet

		blank_datapoint = DataPoint (
			time    = None,
			current = None,
			voltage = None,
			vsrc    = None)

		self.dataset.append (blank_datapoint)

		oApplet.schedule_task (
			oApplet.updatePlot, self,
			blank_datapoint.voltage, blank_datapoint.current)

		return blank_datapoint

	def excite_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oXSMU.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:
            
			breakPlot = self.applySameExcitation()
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

	def applySameExcitation (self):
        
    		oXSMU = self.oXSMU

		'''
			Find excitation
		'''

		breakPlot = NO_BREAKPLOT

		if self.scan_mode == None:
			self.scan_mode = SCAN_MODE_POSITIVE

		if self.scan_mode == SCAN_MODE_POSITIVE:
			breakPlot = self.keepSameExcitation (breakPlot)

		if self.scan_mode == SCAN_MODE_NEGATIVE:
			breakPlot = self.keepSameExcitation (breakPlot)

		if not self.complete():

			try:
				oXSMU.acquire_lock()

				current = (
					self.excitationCurrent if self.currentStep != 0.0
					else copysign (self.finalCurrent, self.excitationVoltage))

				voltage = (
					self.excitationVoltage if self.voltageStep != 0.0
					else copysign (self.finalVoltage, self.excitationCurrent))

				if current == 0.0 or voltage == 0.0:
					oXSMU.output_off()

				else:
					oXSMU.setExcitationLimits (current, voltage, self.maxPower)

					(src_mode, value, self.power_limited) = (
						oXSMU.doExcitationAutoTune (
							track_mode = self.resTrackMode))

			finally:
				oXSMU.release_lock()

		return breakPlot
		
	def keepSameExcitation (self, breakPlot):
    
        	oXSMU = self.oXSMU

		if (self.excitationCurrent == None
		or  self.excitationVoltage == None):

			self.excitationCurrent = 0.0
			self.excitationVoltage = 0.0
			self.power_limited     = False

		elif (not self.power_limited
		and abs (self.excitationCurrent) < self.finalCurrent
		and abs (self.excitationVoltage) < self.finalVoltage):

				# Estimating next current

				if oXSMU.sourceParameters.mode == SOURCE_MODE_CS:
					nextCurrent = (
						oXSMU.sourceParameters.value())

				else:
					nextCurrent = (
						self.dataset[-1].current)

				try:
					self.excitationCurrent = self.currentStep * round (
						nextCurrent / self.currentStep)

				except ZeroDivisionError:
					self.excitationCurrent = nextCurrent

				# Estimating next voltage

				if oXSMU.sourceParameters.mode == SOURCE_MODE_VS:
					nextVoltage = (
						oXSMU.sourceParameters.value())

				else:
					nextVoltage = (
						self.dataset[-1].vsrc)

				try:
					self.excitationVoltage = self.voltageStep * round (
						nextVoltage / self.voltageStep)

				except ZeroDivisionError:
					self.excitationVoltage = nextVoltage

		else:
			self.excitationCurrent = None
			self.excitationVoltage = None

			if self.bipolar:
				breakPlot      = DO_BREAKPLOT
				self.scan_mode = SCAN_MODE_NEGATIVE

			else:
				self.scan_mode = None
				self._complete = True

		return breakPlot
        
	def applyNextExcitation (self):

		oXSMU = self.oXSMU

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
				oXSMU.acquire_lock()

				current = (
					self.excitationCurrent if self.currentStep != 0.0
					else copysign (self.finalCurrent, self.excitationVoltage))

				voltage = (
					self.excitationVoltage if self.voltageStep != 0.0
					else copysign (self.finalVoltage, self.excitationCurrent))

				if current == 0.0 or voltage == 0.0:
					oXSMU.output_off()

				else:
					oXSMU.setExcitationLimits (current, voltage, self.maxPower)

					(src_mode, value, self.power_limited) = (
						oXSMU.doExcitationAutoTune (
							track_mode = self.resTrackMode))

			finally:
				oXSMU.release_lock()

		return breakPlot
        
	def findNextPositiveExcitation (self, breakPlot):

		oXSMU = self.oXSMU

		if (self.excitationCurrent == None
		or  self.excitationVoltage == None):

			self.excitationCurrent = 0.0
			self.excitationVoltage = 0.0
			self.power_limited     = False

		elif (not self.power_limited
		and abs (self.excitationCurrent) < self.finalCurrent
		and abs (self.excitationVoltage) < self.finalVoltage):

				# Estimating next current

				if oXSMU.sourceParameters.mode == SOURCE_MODE_CS:
					nextCurrent = (
						oXSMU.sourceParameters.value() + self.currentStep)

				else:
					nextCurrent = (
						self.dataset[-1].current + self.currentStep)

				try:
					self.excitationCurrent = self.currentStep * round (
						nextCurrent / self.currentStep)

				except ZeroDivisionError:
					self.excitationCurrent = nextCurrent

				# Estimating next voltage

				if oXSMU.sourceParameters.mode == SOURCE_MODE_VS:
					nextVoltage = (
						oXSMU.sourceParameters.value() + self.voltageStep)

				else:
					nextVoltage = (
						self.dataset[-1].vsrc + self.voltageStep)

				try:
					self.excitationVoltage = self.voltageStep * round (
						nextVoltage / self.voltageStep)

				except ZeroDivisionError:
					self.excitationVoltage = nextVoltage

		else:
			self.excitationCurrent = None
			self.excitationVoltage = None

			if self.bipolar:
				breakPlot      = DO_BREAKPLOT
				self.scan_mode = SCAN_MODE_NEGATIVE

			else:
				self.scan_mode = None
				self._complete = True

		return breakPlot

	def findNextNegativeExcitation (self, breakPlot):

		oXSMU = self.oXSMU

		if (self.excitationCurrent == None
		or  self.excitationVoltage == None):

			self.excitationCurrent = 0.0
			self.excitationVoltage = 0.0
			self.power_limited     = False

		elif (not self.power_limited
		and abs (self.excitationCurrent) < self.finalCurrent
		and abs (self.excitationVoltage) < self.finalVoltage):

				# Estimating next current

				if oXSMU.sourceParameters.mode == SOURCE_MODE_CS:
					nextCurrent = (
						oXSMU.sourceParameters.value() - self.currentStep)

				else:
					nextCurrent = (
						self.dataset[-1].current - self.currentStep)

				try:
					self.excitationCurrent = self.currentStep * round (
						nextCurrent / self.currentStep)

				except ZeroDivisionError:
					self.excitationCurrent = nextCurrent

				# Estimating next voltage

				if oXSMU.sourceParameters.mode == SOURCE_MODE_VS:
					nextVoltage = (
						oXSMU.sourceParameters.value() - self.voltageStep)

				else:
					nextVoltage = (
						self.dataset[-1].vsrc - self.voltageStep)

				try:
					self.excitationVoltage = self.voltageStep * round (
						nextVoltage / self.voltageStep)

				except ZeroDivisionError:
					self.excitationVoltage = nextVoltage

		else:
			self.scan_mode = None
			self.excitationCurrent = None
			self.excitationVoltage = None
			self._complete = True

		return breakPlot

	def complete (self):
		return True if self._complete else False

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _IVTimeResolvedAcquisitionThread (_AcquisitionThread):

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
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RTimeModule (_Module):

	def __init__ (self, master, oXSMU):
		_Module.__init__ (self, master, oXSMU)

	def run_type (self):
		return 'R_Time'

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Resistance (Ohm)'

	def init (self):
		_Module.init (self)

		oXSMU   = self.oXSMU
		oApplet = oXSMU.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_RTime)

	def initOhmmeterSettings (
		self, maxCurrent, maxVoltage,
		maxPower, bipolar, resTrackMode):

		self.maxCurrent   = maxCurrent
		self.maxVoltage   = maxVoltage
		self.maxPower     = maxPower
		self.bipolar      = bipolar
		self.resTrackMode = resTrackMode

	def setOhmmeterSettings (
		self, maxCurrent, maxVoltage,
		maxPower, bipolar, resTrackMode):

		self.initOhmmeterSettings (
			maxCurrent, maxVoltage,
			maxPower, bipolar, resTrackMode)

		text = 'Ohmmeter settings updated'
		oApplet = self.oXSMU.oApplet
		oApplet.schedule_task (oApplet.set_status, text)

	def acquire (self, bg_task = None, *bg_tasks):

		oXSMU = self.oXSMU
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		# +++++++++++++++++++++++++++++++++++++++++++++++

		try:
			oXSMU.acquire_lock()

			oXSMU.setExcitationLimits (
				self.maxCurrent, self.maxVoltage, self.maxPower)

			(src_mode, value, power_limited) = (
				oXSMU.doExcitationAutoTune (track_mode = self.resTrackMode))

			if power_limited:
				if src_mode == SOURCE_MODE_CS:
					self.maxCurrent = abs (value)

				if src_mode == SOURCE_MODE_VS:
					self.maxVoltage = abs (value)

			(current, voltage, vsrc, resistance) = oXSMU.measureR (
				self.bipolar, self.delay, self.filterLength,
				self.do_tasks, bg_task, *bg_tasks)

		finally:
			oXSMU.release_lock()

		# +++++++++++++++++++++++++++++++++++++++++++++++

		return DataPoint (
			time       = t,
			current    = current,
			voltage    = voltage,
			vsrc       = vsrc,
			resistance = resistance)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oApplet = self.oXSMU.oApplet
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
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

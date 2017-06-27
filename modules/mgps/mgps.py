# coding: utf-8
import libmgps

from app_mgps       import GUI
from app_mgps       import GUI_SourceParameters
from app_mgps       import GUI_MeterParameters
from app_mgps       import GUI_AcquisitionSettings

from MGPS_DataType  import DataPoint, DataSet
from MGPS_Method    import Method, XMethodError

from XDict          import XDict
from XThread        import XTaskQueue, XThread, XThreadModule, XTerminate
from Preferences    import get_MGPS_serialNo, getDataFolder

# Importing Python provided libraries
import os
from threading      import Thread, RLock, Lock
from time           import time as systime, localtime, sleep
from Tkinter        import Toplevel
from math           import copysign, sqrt

from MGPS_Constants import *

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
		self.src_mode = SOURCE_MODE_HS

		self.deviceID = None
		self.hs_range = None
		self.cs_range = None
		self.hm_range = None
		self.cm_range = None
		self.vm_range = None

		self.hs_autorange  = True
		self.cs_autorange  = True
		self.hm_autorange  = True
		self.cm_autorange  = True
		self.vm_autorange  = True

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
		number_of_devices = libmgps.scan()
		for i in range (0, number_of_devices):
			serialNos.append (libmgps.serialNo (i))

		return serialNos

	def open (self, serialNo):

		if serialNo in self.scan():

			self.deviceID, goodID, timeout = (
				libmgps.open_device (serialNo, COMM_TIMEOUT_INTERVAL))

			if timeout != 0.0 and goodID:

				self.do_callback (DEVICE_CONNECTED)

				libmgps.CS_enable (
					self.deviceID, CS_ACTIVATE, COMM_TIMEOUT_INTERVAL)

			else:
				libmgps.close_device (self.deviceID)
				self.deviceID = None
				self.do_callback (DEVICE_NOT_FOUND)

		else:
			self.do_callback (DEVICE_NOT_FOUND)

	def close (self):

		if self.deviceID != None:

			libmgps.HS_setMagneticField (
				self.deviceID, 0.0, COMM_TIMEOUT_INTERVAL)

			libmgps.CS_enable (
				self.deviceID, CS_DEACTIVATE, COMM_TIMEOUT_INTERVAL)

			libmgps.close_device (self.deviceID)

			self.deviceID = None
			self.hs_range = None
			self.cs_range = None
			self.hm_range = None
			self.cm_range = None
			self.vm_range = None
			self.cs_value = None

			self.do_callback (DEVICE_DISCONNECTED)

	def check_connected (self):

		if self.deviceID == None:
			raise LinkError ('MGPS_LinkError: Device not connected')

	def check_timeout (self, timeout, context = ''):

		if (timeout == 0.0):
			self.close()
			raise CommError ('MGPS_CommError: ' + str (context))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setSourceMode (self, mode):

		self.check_connected()

		if self.src_mode == None or self.src_mode != mode:

			if mode == SOURCE_MODE_CS:
				self.cs_range = None
				self.cs_value = None

			if mode == SOURCE_MODE_HS:
				self.hs_range = None
				self.hs_value = None

		self.src_mode = mode
		return mode

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HS_setRange (self, range):

		self.check_connected()

		if self.hs_range == None or self.hs_range != range:

			range, timeout = libmgps.HS_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set magnetic field source range')

		self.hs_range = range
		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HS_setMagneticField (self, value):

		self.check_connected()

		set_value, timeout = libmgps.HS_setMagneticField (
			self.deviceID, value, COMM_TIMEOUT_INTERVAL)

		self.check_timeout (timeout, 'Set Magnetic field')
		self.hs_value = value
		return value

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HS_findRange (self, value):

		range = HS_RANGE_MIN

		while True:

			if abs (value) > HS_RANGES [range]:
				if range + 1 > HS_RANGE_MAX : break
				else                        : range += 1

			else : break

		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HS_verifyCalibration (self, index, filterLength = 128):

		self.check_connected()

		timeout = COMM_TIMEOUT_INTERVAL

		timeout += filterLength * 0.02

		(index, current, magnetic_field, timeout) = \
			libmgps.HS_verifyCalibration (self.deviceID, index, timeout)

		self.check_timeout (timeout, 'Verify Magnetic Field source calibration')
		return current


	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HS_saveCalibration (self, filterLength = 128):

		self.check_connected()

		timeout = COMM_TIMEOUT_INTERVAL

		timeout += filterLength * 0.02

		timeout = libmgps.HS_saveCalibration (self.deviceID, timeout)

		self.check_timeout (timeout, 'Save Magnetic Field source calibration')


	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HS_setCalibration (self, index, value, filterLength = 128):

		self.check_connected()

		timeout = COMM_TIMEOUT_INTERVAL

		timeout += filterLength * 0.02

		(index, current, magnetic_field, timeout) = \
			libmgps.HS_setCalibration (self.deviceID, index, value, timeout)

		self.check_timeout (timeout, 'Set Magnetic Field source calibration')
		return magnetic_field

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HS_setMagnetID (self, magnetID):

		self.check_connected()

		timeout = COMM_TIMEOUT_INTERVAL

		(magnetID, timeout) = \
			libmgps.HS_setMagnetID (self.deviceID, magnetID, timeout)

		self.check_timeout (timeout, 'Set Magnetic ID')
		return magnetID

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HS_getMagnetID (self):

		self.check_connected()

		timeout = COMM_TIMEOUT_INTERVAL

		(magnetID, timeout) = \
			libmgps.HS_getMagnetID (self.deviceID, magnetID, timeout)

		self.check_timeout (timeout, 'Get Magnet ID')
		return magnetID

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CS_enable (self):

		self.check_connected()

		timeout = COMM_TIMEOUT_INTERVAL

		libmgps.CS_enable (self.deviceID, CS_ACTIVATE,
					timeout)

		self.check_timeout (timeout, 'CS_enable')

		return CS_ACTIVATE


	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CS_disable (self):

		self.check_connected()

		timeout = COMM_TIMEOUT_INTERVAL

		libmgps.CS_enable (self.deviceID, CS_DEACTIVATE,
					timeout)

		self.check_timeout (timeout, 'CS_disable')

		return CS_DEACTIVATE


	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CS_setRange (self, range):

		self.check_connected()

		if self.cs_range == None or self.cs_range != range:

			range, timeout = libmgps.CS_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set current source range')

		self.cs_range = range
		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CS_setCurrent (self, value):

		self.check_connected()

		set_value, timeout = libmgps.CS_setCurrent (
			self.deviceID, value, COMM_TIMEOUT_INTERVAL)

		self.check_timeout (timeout, 'Set current')
		self.cs_value = set_value
		return set_value

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CS_findRange (self, value):

		range = CS_RANGE_MIN

		while True:

			if abs (value) > CS_RANGES [range]:
				if range + 1 > CS_RANGE_MAX : break
				else                        : range += 1

			else : break

		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HM_setRange (self, range):

		self.check_connected()

		if self.hm_range == None or self.hm_range != range:

			range, timeout = libmgps.HM_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set gauss meter range')

		self.hm_range = range
		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _HM_doAutoRange (self):

		limits = [(0.8 * 0.1 * rng, 1.2 * rng) for rng in HM_RANGES]

		self.check_connected()
		if self.hm_range == None: self._HM_setRange (HM_RANGE_MAX)

		while True:

			timeout      = COMM_TIMEOUT_INTERVAL
			filterLength = 1

			(magnetic_field, timeout) = libmgps.HM_getReading (
				self.deviceID, filterLength, timeout)

			self.check_timeout (timeout, 'Get gauss meter reading')

			(low, hi) = limits[self.hm_range]

			if abs (magnetic_field) < low:

				range = self.hm_range - 1
				if range < HM_RANGE_MIN : break
				else                    : self._HM_setRange (range)

			elif abs (magnetic_field) > hi:

				range = self.hm_range + 1
				if range > HM_RANGE_MAX : break
				else                    : self._HM_setRange (range)

			else: break

		return self.hm_range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HM_setRange (self, autorange, range):

		self.check_connected()
		self.hm_autorange = autorange

		if autorange:
			range = self._HM_doAutoRange()

		else:
			range = self._HM_setRange (range)

		self.do_callback (HM_RANGE_CHANGED, autorange, range)
		return (autorange, range)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HM_getReading (self, filterLength = 128):

		self.check_connected()

		if self.hm_autorange:
			range = self._HM_doAutoRange()
			self.do_callback (HM_RANGE_CHANGED, self.hm_autorange, range)

		timeout = COMM_TIMEOUT_INTERVAL

		timeout += filterLength * 0.02

		(current, timeout) = \
			libmgps.HM_getReading (self.deviceID, filterLength, timeout)

		self.check_timeout (timeout, 'Get gauss meter reading')
		return current

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HS_setCalibration (self, index, value, filterLength = 128):
		self.check_connected()

		timeout = COMM_TIMEOUT_INTERVAL

		timeout += filterLength * 0.02

		(index, current, magnetic_field, timeout) = \
			HS_setCalibration (self.deviceID, index, value, timeout)

		self.check_timeout (timeout, 'Set Magnetic Field source calibration')
		return (index, timeout)


	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CM_setRange (self, range):

		self.check_connected()

		if self.cm_range == None or self.cm_range != range:

			range, timeout = libmgps.CM_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set current meter range')

		self.cm_range = range
		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _CM_doAutoRange (self):

		limits = [(0.99 * 0.1 * rng, 1.01 * rng) for rng in CM_RANGES]

		self.check_connected()
		if self.cm_range == None: self._CM_setRange (CM_RANGE_MAX)

		while True:

			timeout      = COMM_TIMEOUT_INTERVAL
			filterLength = 1

			(current, timeout) = libmgps.CM_getReading (
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

		if autorange:
			range = self._CM_doAutoRange()

		else:
			range = self._CM_setRange (range)

		self.do_callback (CM_RANGE_CHANGED, autorange, range)
		return (autorange, range)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CM_getReading (self, filterLength = 128):

		self.check_connected()

		if self.cm_autorange:
			range = self._CM_doAutoRange()
			self.do_callback (CM_RANGE_CHANGED, self.cm_autorange, range)

		timeout = COMM_TIMEOUT_INTERVAL

		timeout += filterLength * 0.01

		(current, timeout) = \
			libmgps.CM_getReading (self.deviceID, filterLength, timeout)

		self.check_timeout (timeout, 'Get ammeter reading')
		return current

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _VM_setRange (self, range):

		self.check_connected()

		if self.vm_range == None or self.vm_range != range:

			range, timeout = libmgps.VM_setRange (
				self.deviceID, range, COMM_TIMEOUT_INTERVAL)

			self.check_timeout (timeout, 'Set voltmeter range')

		self.vm_range = range
		return range

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _VM_doAutoRange (self):

		limits = [(0.99 * 0.1 * rng, 1.01 * rng) for rng in VM_RANGES]
		self.check_connected()

		if self.vm_range == None:
			self._VM_setRange (VM_RANGE_MAX)

		while True:

			timeout      = COMM_TIMEOUT_INTERVAL
			filterLength = 1

			(voltage, timeout) = libmgps.VM_getReading (
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

		timeout += filterLength * 0.01

		(voltage, timeout) = libmgps.VM_getReading (
			self.deviceID, filterLength, timeout)

		self.check_timeout (timeout, 'Get voltmeter reading')

		return voltage

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setSourceParameters (self, mode, autorange, range, value):

		self.check_connected()

		self.src_autorange = autorange
		mode               = self._setSourceMode (mode)

		# +++++++++++++++++++++++++++++++++++++++++++
		# Finding source range

		if autorange:

			find_range = {
				SOURCE_MODE_HS : self._HS_findRange,
				SOURCE_MODE_CS : self._CS_findRange}.get (mode)

			range = find_range (value)

		# +++++++++++++++++++++++++++++++++++++++++++
		# Settings source range

		set_range = {
			SOURCE_MODE_HS : self._HS_setRange,
			SOURCE_MODE_CS : self._CS_setRange}.get (mode)

		range = set_range (range)

		# +++++++++++++++++++++++++++++++++++++++++++
		# Setting source value

		set_output = {
			SOURCE_MODE_HS : self._HS_setMagneticField,
			SOURCE_MODE_CS : self._CS_setCurrent}.get (mode)

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

	def __init__ (self, oMGPS):
		self.oMGPS = oMGPS
		self._plots = {}
		self._taskq = XTaskQueue()
		self._lastPlotUpdateAt = 0.0
		self._hApplet = self.oMGPS.oApp.master.after (50, self._applet)

	def _applet (self):

		self._taskq.process()
		oApp = self.oMGPS.oApp

		t = systime()
		if t >= self._lastPlotUpdateAt + 2:
			self._lastPlotUpdateAt = t

			for (wPlot, traceID) in self._plots.values():
				if wPlot.damaged() : wPlot.redraw()

		self._hApplet = oApp.master.after (50, self._applet)

	def schedule_task (self, task, *args):
		return self._taskq.push (task, *args)

	def refresh (self):
		self.oMGPS.oApp.master.update()

	def close (self):
		oApp = self.oMGPS.oApp
		oApp.close()
		oApp.master.after_cancel (self._hApplet)
		oApp.master.destroy()

	# +++++++++++++ Update display functions +++++++++++++++

	def set_status (self, status):
		self.oMGPS.oApp.set_status (status)

	def setConnection (self, status):
		self.oMGPS.oApp.setConnection (status)

	def HM_setReading (self, range, reading):
		self.oMGPS.oApp.HM_setReading (range, reading)

	def CM_setReading (self, range, reading):
		self.oMGPS.oApp.CM_setReading (range, reading)

	def VM_setReading (self, range, reading):
		self.oMGPS.oApp.VM_setReading (range, reading)

	def initPlot (self, thread, title, xlabel, ylabel):
		oApp = self.oMGPS.oApp
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
		oApp = self.oMGPS.oApp
		oApp.clearPlot()
		self._plots.clear()

	def HM_setRange (self, autorange, range):
		self.oMGPS.oApp.HM_setRange (autorange, range)
		self.oMGPS.meterParameters.HM_setRange (autorange, range)

	def CM_setRange (self, autorange, range):
		self.oMGPS.oApp.CM_setRange (autorange, range)
		self.oMGPS.meterParameters.CM_setRange (autorange, range)

	def VM_setRange (self, autorange, range):
		self.oMGPS.oApp.VM_setRange (autorange, range)
		self.oMGPS.meterParameters.VM_setRange (autorange, range)

	def setSourceParameters (self, mode, autorange, range, value):
		self.oMGPS.oApp.setSourceParameters (mode, autorange, range, value)
		self.oMGPS.sourceParameters.set (mode, autorange, range, value)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setRunMode (self, value):
		self.oMGPS.oApp.setRunMode (value)
		self.oMGPS.run_mode = value

	def setRunControlStatus (self, status):
		self.oMGPS.oApp.setRunControlStatus (status)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setAcquisitionSettings (self, delay, filterLength):
		self.oMGPS.oApp.setAcquisitionSettings (delay, filterLength)
		self.oMGPS.acquisitionSettings.set (delay, filterLength)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquisition_atexit (self):
		self.oMGPS.releaseAcquisition()

	def devicethread_atexit (self):
		self.oMGPS.releaseDeviceThread();

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _DeviceThread (XThread):

	def __init__ (self, oMGPS):

		XThread.__init__ (self, daemon = True)

		self.oMGPS = oMGPS

		'''
			Register driver callback
		'''
		oDriver = self.oMGPS.oDriver

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
				oApplet = self.oMGPS.oApplet
				oApplet.schedule_task (oApplet.set_status, str (e))

			except XTerminate: break

		self.disconnectDevice()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _DriverCB (self, context, *args):

		oApplet = self.oMGPS.oApplet

		if context == DEVICE_CONNECTED:
			oApplet.schedule_task (
				oApplet.setConnection, DEVICE_CONNECTED).wait()

		elif context == DEVICE_DISCONNECTED:
			oApplet.schedule_task (
				oApplet.setConnection, DEVICE_DISCONNECTED).wait()

		elif context == DEVICE_NOT_FOUND:
			oApplet.schedule_task (
				oApplet.setConnection, DEVICE_NOT_FOUND).wait()

		elif context == HM_RANGE_CHANGED:
			oApplet.schedule_task (oApplet.HM_setRange, *args).wait()

		elif context == CM_RANGE_CHANGED:
			oApplet.schedule_task (oApplet.CM_setRange, *args).wait()

		elif context == VM_RANGE_CHANGED:
			oApplet.schedule_task (oApplet.VM_setRange, *args).wait()

		elif context == SOURCE_PARAMETERS_CHANGED:
			oApplet.schedule_task (oApplet.setSourceParameters, *args).wait()

		else : raise ValueError (context)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquire_n_display (self):

		(hm_range, cm_range, vm_range, datapoint) = self.acquire()

		oApplet = self.oMGPS.oApplet

		oApplet.schedule_task (
			oApplet.HM_setReading, hm_range, datapoint.magnetic_field)

		oApplet.schedule_task (
			oApplet.CM_setReading, cm_range, datapoint.current)

		oApplet.schedule_task (
			oApplet.VM_setReading, vm_range, datapoint.voltage)

		return datapoint

	def acquire (self):
		oMGPS   = self.oMGPS
		oDriver = oMGPS.oDriver

		try:
			oMGPS.acquire_lock()
			oMGPS.adjustMeterRanges()

			(magnetic_field, current, voltage) = \
				oMGPS.measureHIV (filterLength = 1)

			hm_range  = oDriver.hm_range
			cm_range  = oDriver.cm_range
			vm_range  = oDriver.vm_range

		finally:
			oMGPS.release_lock()

		return (hm_range, cm_range, vm_range,
		  DataPoint (magnetic_field = magnetic_field,
			current = current, voltage = voltage))

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	'''
		Connection functions
	'''

	def connectDevice (self):

		oDriver = self.oMGPS.oDriver
		oApplet = self.oMGPS.oApplet

		oApplet.schedule_task (oApplet.setConnection, DEVICE_CONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.open (get_MGPS_serialNo())

		finally:
			oDriver.release_lock()

	def disconnectDevice (self):

		oDriver = self.oMGPS.oDriver
		oApplet = self.oMGPS.oApplet

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

		oDriver = self.oMGPS.oDriver
		oApplet = self.oMGPS.oApplet


		try:
			oDriver.acquire_lock()
			oDriver.setSourceParameters (mode, autorange, range, value)

		finally:
			oDriver.release_lock()

	'''
		Meter parameters
	'''

	def HM_setRange (self, autorange, range):

		oDriver = self.oMGPS.oDriver
		oApplet = self.oMGPS.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.HM_setRange (autorange, range)

		finally:
			oDriver.release_lock()

	def CM_setRange (self, autorange, range):

		oDriver = self.oMGPS.oDriver
		oApplet = self.oMGPS.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.CM_setRange (autorange, range)

		finally:
			oDriver.release_lock()

	def VM_setRange (self, autorange, range):

		oDriver = self.oMGPS.oDriver
		oApplet = self.oMGPS.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.VM_setRange (autorange, range)

		finally:
			oDriver.release_lock()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def MGPS (master, sample):

	if not MGPS.singleton:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()

		oApp           = GUI (win, sample)
		MGPS.singleton = _MGPS (oApp, sample)

	if master not in MGPS.master:
		MGPS.master.append (master)

	return MGPS.singleton

def closeMGPS (master):

	if master in MGPS.master:
		MGPS.master.remove (master)

	if len (MGPS.master) == 0 and MGPS.singleton:
		MGPS.singleton.close()
		MGPS.singleton = None

MGPS.singleton = None
MGPS.master    = []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class SourceParameters:

	def __init__ (self, mode, autorange,
		hs_range, hs_value, cs_range, cs_value):

		self.mode      = mode
		self.autorange = autorange
		self.hs_range  = hs_range
		self.hs_value  = hs_value
		self.cs_range  = cs_range
		self.cs_value  = cs_value

	def set (self, mode, autorange, range, value):

		if mode == SOURCE_MODE_HS:

			self.mode      = mode
			self.autorange = autorange
			self.hs_range  = range
			self.hs_value  = value

		elif mode == SOURCE_MODE_CS:

			self.mode      = mode
			self.autorange = autorange
			self.cs_range  = range
			self.cs_value  = value

		else: raise ValueError (mode)

	def HS_setRange (self, range):
		self.hs_range = range

	def CS_setRange (self, range):
		self.cs_range = range

	def range (self, mode = None):
		if mode == None : mode = self.mode

		return {
			SOURCE_MODE_HS : self.hs_range,
			SOURCE_MODE_CS : self.cs_range}.get (mode)

	def value (self, mode = None):
		if mode == None : mode = self.mode

		return {
			SOURCE_MODE_HS : self.hs_value,
			SOURCE_MODE_CS : self.cs_value}.get (mode)

	def get (self):
		return (
			self.mode,
			self.autorange,
			self.range(),
			self.value())

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class MeterParameters:

	def __init__ (self, hm_autorange, hm_range,
			   cm_autorange, cm_range,
			   vm_autorange, vm_range):

		self.HM_setRange (hm_autorange, hm_range)
		self.CM_setRange (cm_autorange, cm_range)
		self.VM_setRange (vm_autorange, vm_range)

	def HM_setRange (self, hm_autorange, hm_range):
		self.hm_autorange = hm_autorange
		self.hm_range     = hm_range

	def CM_setRange (self, cm_autorange, cm_range):
		self.cm_autorange = cm_autorange
		self.cm_range     = cm_range

	def VM_setRange (self, vm_autorange, vm_range):
		self.vm_autorange = vm_autorange
		self.vm_range     = vm_range

	def set (self,
			 hm_autorange  = None, hm_range  = None,
			 cm_autorange  = None, cm_range  = None,
			 vm_autorange  = None, vm_range  = None):

		if hm_autorange  != None : self.hm_autorange  = hm_autorange
		if hm_range      != None : self.hm_range      = hm_range
		if cm_autorange  != None : self.cm_autorange  = cm_autorange
		if cm_range      != None : self.cm_range      = cm_range
		if vm_autorange  != None : self.vm_autorange  = vm_autorange
		if vm_range      != None : self.vm_range      = vm_range

	def get (self):
		return (
			self.hm_autorange,
			self.hm_range,
			self.cm_autorange,
			self.cm_range,
			self.vm_autorange,
			self.vm_range)

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
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _MGPS:

	def __init__ (self, oApp, sample):

		self.oApp = oApp
		self.sample = sample
		oDriver = self.oDriver = _Driver()

		# ++++ Device parameters ++++

		self.sourceParameters = SourceParameters (
			mode      = SOURCE_MODE_HS, autorange = True,
			hs_range  = HS_RANGE_1, hs_value  = 0.0,
			cs_range  = CS_RANGE_1, cs_value  = 0.0)

		self.meterParameters = MeterParameters (
			hm_autorange = False, hm_range = HS_RANGE_1,
			cm_autorange = False, cm_range = CM_RANGE_1,
			vm_autorange = False, vm_range = VM_RANGE_1)

		self.max_magnetic_field   = 100.0
		self.max_current          = 6.0
		self.max_power            = 90.0
		self.run_mode             = RUN_MODE_HTime

		# ++++ Settings ++++

		self.acquisitionSettings = \
			AcquisitionSettings (delay = 2.0, filterLength = 16)

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
			self.sourceParameters.mode,
			self.sourceParameters.autorange,
			self.sourceParameters.range(),
			self.sourceParameters.value())

		oDeviceThread.schedule_task (
			oDeviceThread.HM_setRange,
			self.meterParameters.hm_autorange,
			self.meterParameters.hm_range)

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
				'MGPS_ResourceError: Device thread unavailable')

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

		elif context == START_RUN          : self.startRun (*args)
		elif context == FINISH_RUN         : self.finishRun()
		elif context == OPEN_DIALOG        : self.openDialog (*args)
		elif context == OPEN_METHOD        : self.openMethod (*args)
		elif context == SAVE_METHOD        : self.saveMethod (*args)
		elif context == UPLOAD_CALIBRATION : self.uploadCalibration (*args)

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

			if mode == RUN_MODE_HTime:
				module = _HTimeModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

			elif mode == RUN_MODE_ITime:
				module = _ITimeModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

			elif mode == RUN_MODE_VTime:
				module = _VTimeModule (master, self)
				module.initAcquisitionSettings (
					self.acquisitionSettings.delay,
					self.acquisitionSettings.filterLength)

			else:
				raise ResourceError (
					'MGPS_ResourceError: Module creation failed')

			self.oModule = module

		else:
			raise ResourceError (
				'MGPS_ResourceError: Module unavailable')

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

				if mode == RUN_MODE_HTime:
					thread =  _HTimeAcquisitionThread (module)

				elif mode == RUN_MODE_ITime:
					thread =  _ITimeAcquisitionThread (module)

				elif mode == RUN_MODE_VTime:
					thread = _VTimeAcquisitionThread (module)

				else:
					raise ResourceError (
						'MGPS_ResourceError: Thread creation failed')

				thread.atexit (self.acquisition_atexit)
				self.oAcqThread = thread

			else:
				raise ResourceError (
					'MGPS_ResourceError: Thread unavailable')

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
			self.sourceParameters.range (SOURCE_MODE_HS),
			self.sourceParameters.value (SOURCE_MODE_HS))

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
			self.meterParameters.hm_autorange,
			self.meterParameters.hm_range,
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
				oDeviceThread.HM_setRange,
				self.meterParameters.hm_autorange,
				self.meterParameters.hm_range)

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
	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	# Useful functions callable from other modules

	def output_off (self):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			oDriver.setSourceParameters (
				self.sourceParameters.mode,
				self.sourceParameters.autorange,
				self.sourceParameters.range(),0.0)

		finally:
			oDriver.release_lock()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def adjustMeterRanges (self):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			if self.meterParameters.hm_autorange:
				oDriver.HM_getReading (filterLength = 1)

			if self.meterParameters.cm_autorange:
				oDriver.CM_getReading (filterLength = 1)

			if self.meterParameters.vm_autorange:
				oDriver.VM_getReading (filterLength = 1)

		finally:
			oDriver.release_lock()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CS_enable (self):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			enable_status = oDriver._CS_enable ()

		finally:
			oDriver.release_lock()

		return enable_status

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def CS_disable (self):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			enable_status = oDriver._CS_disable ()

		finally:
			oDriver.release_lock()

		return enable_status

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HS_verifyCalibration (self, index):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			current = oDriver._HS_verifyCalibration (index)

		finally:
			oDriver.release_lock()

		return current

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HS_saveCalibration (self):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()

			oDriver._HS_saveCalibration ()

		finally:
			oDriver.release_lock()


	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HS_setCalibration (self, index, value):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			magnetic_field = oDriver._HS_setCalibration (index, value)

		finally:
			oDriver.release_lock()

		return magnetic_field

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HS_setMagnetID (self, magnetID):

		oDriver = self.oDriver
		oApplet = self.oApplet

		try:
			oDriver.acquire_lock()
			magnetID = oDriver._HS_setMagnetID (magnetID)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		finally:
			oDriver.release_lock()


		return magnetID

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def HS_getMagnetID (self):

		oDriver = self.oDriver
		oApplet = self.oApplet

		try:
			oDriver.acquire_lock()
			magnetID = oDriver._HS_getMagnetID ()

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		finally:
			oDriver.release_lock()


		return magnetID

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def measureH (self, filterLength):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			magnetic_field = oDriver.HM_getReading  (filterLength)

		finally:
			oDriver.release_lock()

		return magnetic_field

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

	def measureHIV (self, filterLength):

		oDriver = self.oDriver

		try:
			oDriver.acquire_lock()
			magnetic_field = oDriver.HM_getReading  (filterLength)
			current 	   = oDriver.CM_getReading  (filterLength)
			voltage		   = oDriver.VM_getReading  (filterLength)

		finally:
			oDriver.release_lock()

		return (magnetic_field, current, voltage)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def sleep (self, duration, bg_task = None, *bg_tasks):

		entry = systime()
		while systime() < entry + duration:
			sleep (0.05)
			if bg_task: bg_task()
			for task in bg_tasks:
				if task: task()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMethod (self):
		method = Method()
		method.setSourceParameters    (*self.sourceParameters.get())
		method.setMeterParameters     (*self.meterParameters.get())
		method.setAcquisitionSettings (*self.acquisitionSettings.get())
		method.setRunMode             (self.run_mode)
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
			oDeviceThread.HM_setRange,
			self.meterParameters.hm_autorange,
			self.meterParameters.hm_range)

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

		# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

		run_mode = method.getRunMode (self.run_mode)
		oApplet.schedule_task (oApplet.setRunMode, run_mode)

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

	def uploadCalibration (self, fd):
		filename, file_extension = os.path.splitext (fd.name)
		if   (file_extension == '.csv') : self.uploadCalibration_CSV (fd)
		else : print "Unknown format: ", file_extension

		oApplet = self.oApplet
		text = 'Calibration uploaded : ' + fd.name
		oApplet.schedule_task (oApplet.set_status, text)

	def uploadCalibration_CSV (self, fd):
		import csv
		reader = csv.reader(fd)
		for row in reader:
			if (row[0] == 'MagnetID'):
				self.HS_setMagnetID (row [1]);
			if (row[0] == 'TableEntry'):
				self.HS_setCalibration (int(row[1]), float (row[3]))
		self.HS_saveCalibration()

	def uploadCalibration_JSON (self, fd):
		print "JSON files are not yet supported.."

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Module (XThreadModule):

	def __init__ (self, master, oMGPS):
		XThreadModule.__init__ (self, master)
		self.oMGPS        = oMGPS
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
		return 'mgps'

	def is_alive (self):
		return True if self._alive else False

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def initAcquisitionSettings (self, delay, filterLength):
		self.delay        = delay
		self.filterLength = filterLength

	def setAcquisitionSettings (self, delay, filterLength):
		self.initAcquisitionSettings (delay, filterLength)
		oApplet = self.oMGPS.oApplet
		text = 'Acquisition settings updated'
		oApplet.schedule_task (oApplet.set_status, text)

	def init (self):

		oMGPS         = self.oMGPS
		oApplet       = oMGPS.oApplet
		self._alive   = True

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

		oMGPS   = self.oMGPS
		oApplet = oMGPS.oApplet
		oApplet.schedule_task (oApplet.setRunControlStatus, RUN_FINISHING)

		# Resets excitation voltage
		try:
			oMGPS.output_off()

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
			('Time',           '%12s',   'sec'),
			('Magnetic field', '%12s',    'mT'),
			('Current',        '%12s',     'A'),
			('Voltage',        '%12s',     'V')
		]

		(sampleName, sampleID, sampleDescription) = self.oMGPS.sample.get()
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
			(
				'Time               : ', '%12.1f',
				datapoint.time, 'sec'
			),

			(
				'Magnetic field     : ', '%12.5f',
				datapoint.magnetic_field, 'T'
			),

			(
				'Current            : ', '%12.4f',
				datapoint.current, 'A'
			),

			(
				'Voltage            : ', '%12.4f',
				datapoint.voltage, 'V'
			)
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
		dict.set_sample (self.oMGPS.sample.get())
		#dict.set_events ({})

		fields = [
			('01 Time',           DATASET_COL_TIME,          'second'),
			('02 Magnetic Field', DATASET_COL_MAGNETIC_FIELD,     'T'),
			('03 Current',        DATASET_COL_CURRENT,            'A'),
			('04 Voltage',        DATASET_COL_VOLTAGE,            'V')
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

		(sampleName, sampleID, _) = self.oMGPS.sample.get()

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

class _HTimeModule (_Module):

	def __init__ (self, master, oMGPS):
		_Module.__init__ (self, master, oMGPS)

	def run_type (self):
		return 'H_Time'

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Magnetic field (T)'

	def init (self):
		_Module.init (self)

		oMGPS   = self.oMGPS
		oApplet = oMGPS.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_HTime)

	def acquire (self, bg_task = None, *bg_tasks):

		oMGPS = self.oMGPS
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		# ++++++++++++++++++++++++++++++

		try:
			oMGPS.acquire_lock()
			(magnetic_field, current, voltage) = (
				oMGPS.measureHIV (self.filterLength))

		finally:
			oMGPS.release_lock()

		return DataPoint (
			time = t, magnetic_field = magnetic_field,
			current = current, voltage = voltage)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oMGPS   = self.oMGPS
		oApplet = oMGPS.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			datapoint = self.acquire (self.do_tasks, bg_task, *bg_tasks)
			self.update_log (datapoint)
			self.dataset.append (datapoint)

			oApplet.schedule_task (
				oApplet.updatePlot, self,
				datapoint.time, datapoint.magnetic_field)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

	def setMagneticField (self, value):

		oDriver = self.oMGPS.oDriver
		source_parameters = self.oMGPS.sourceParameters

		try:
			oDriver.acquire_lock()

			magnetic_field = oDriver.setSourceParameters (
				source_parameters.mode, source_parameters.autorange,
				source_parameters.hs_range, value)

		finally:
			oDriver.release_lock()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _HTimeAcquisitionThread (_AcquisitionThread):

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

class _ITimeModule (_Module):

	def __init__ (self, master, oMGPS):
		_Module.__init__ (self, master, oMGPS)

	def run_type (self):
		return 'I_Time'

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Current (A)'

	def init (self):
		_Module.init (self)

		oMGPS   = self.oMGPS
		oApplet = oMGPS.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_ITime)

	def acquire (self, bg_task = None, *bg_tasks):

		oMGPS = self.oMGPS
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		# ++++++++++++++++++++++++++++++

		try:
			oMGPS.acquire_lock()
			current = oMGPS.measureI (self.filterLength)
			voltage = oMGPS.measureV (self.filterLength)

		finally:
			oMGPS.release_lock()

		return DataPoint (
			time = t, current = current, voltage = voltage)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oMGPS   = self.oMGPS
		oApplet = oMGPS.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			datapoint = self.acquire (self.do_tasks, bg_task, *bg_tasks)
			self.update_log (datapoint)
			self.dataset.append (datapoint)

			oApplet.schedule_task (
				oApplet.updatePlot,
				self, datapoint.time, datapoint.current)

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

	def __init__ (self, master, oMGPS):
		_Module.__init__ (self, master, oMGPS)

	def run_type (self):
		return 'V_Time'

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Voltage (V)'

	def init (self):
		_Module.init (self)

		oMGPS   = self.oMGPS
		oApplet = oMGPS.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_VTime)

	def acquire (self, bg_task = None, *bg_tasks):

		oMGPS = self.oMGPS
		t = systime() - self.t0
		self.do_tasks (bg_task, *bg_tasks)

		# ++++++++++++++++++++++++++++++

		try:
			oMGPS.acquire_lock()
			current = oMGPS.measureI (self.filterLength)
			voltage = oMGPS.measureV (self.filterLength)

		finally:
			oMGPS.release_lock()

		return DataPoint (
			time = t, voltage = voltage, current = current)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oMGPS   = self.oMGPS
		oApplet = oMGPS.oApplet
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

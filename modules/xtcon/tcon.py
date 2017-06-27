import Preferences

from TCON_DataType import DataPoint, DataSet
from TCON_DataType import StepEntry, StepTable

from app_tcon import GUI
from app_tcon import GUI_IsothermalSettings
from app_tcon import GUI_RampSettings
from app_tcon import GUI_StepSettings
from app_tcon import GUI_PIDSettings
from app_tcon import GUI_Calibration

from TCON_Constants import *
from TCON_Method    import Method, XMethodError

from Plot2D      import Plot2D
from XDict       import XDict
from XThread     import XTaskQueue, XThread, XTerminate, XThreadModule

# Importing Python provided libraries
import os, tkMessageBox, copy
from threading   import Thread, RLock, current_thread, Lock
from serial      import Serial, PARITY_NONE, SerialException
from termios     import error as TermiosException
from time        import time as systime, localtime, sleep
from struct      import unpack
from random      import random
from Tkinter     import NORMAL, DISABLED, Toplevel
from collections import deque

import libxtcon

#---Temp. Range ----
MIN_HTR_TEMP = 77
MAX_HTR_TEMP = 480
HTR_TEMP_RANGE = [MIN_HTR_TEMP , MAX_HTR_TEMP]

class LinkError     (Exception) : pass
class CommError     (Exception) : pass
class ResourceError (Exception) : pass

def Driver():

	if Driver.singleton == None:

		Driver.singleton = _Driver()
		#Driver.singleton = _DummyDriver()

	return Driver.singleton

Driver.singleton = None

class _Driver:

	def __init__ (self):
		self._thlock 		= RLock()
		self._deviceID 		= None

		self._P				= DEFAULT_P
		self._I				= DEFAULT_I
		self._D				= DEFAULT_D
		self._IRange		= DEFAULT_IRANGE

		self._runMode 		= None
		self._ctrlSensor 	= DEFAULT_CTRL_SENSOR

		self._isothermalSetpoint = 0.0
		self._rampFinalTemp		 = 0.0
		self._rampRate			 = 0.0

		self._sensorTemperature = [None]*TOTAL_SENSORS

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
		N = libxtcon.scan()
		for i in range (0, N):
			serialNos.append (libxtcon.serialNo (i))

		return serialNos

	def open (self, serialNo):
		if serialNo in self.scan():
			self._deviceID, goodID, timeout = \
				libxtcon.open_device (serialNo, COMM_TIMEOUT_INTERVAL)

			if timeout != 0.0 and goodID:
				self.do_callback (DEVICE_CONNECTED)

			else:
				libxtcon.close_device (self._deviceID)
				self._deviceID = None
				self.do_callback (DEVICE_NOT_FOUND)
		else:
			self.do_callback (DEVICE_NOT_FOUND)

	def close (self):
		if self._deviceID != None:
			libxtcon.close_device (self._deviceID)
			self._deviceID = None
			self._position = None
			self.do_callback (DEVICE_DISCONNECTED)

	def check_connected (self):
		if self._deviceID == None:
			raise LinkError ('TCON_LinkError: Device not connected')

	def check_timeout (self, timeout, context = ''):
		if (timeout == 0.0):
			self.close()
			raise CommError ('TCON_CommError: ' + str (context))

	def readSensor1Temperature (self):
		self.check_connected()
		sensor, T, timeout = libxtcon.getSensorTemperature (
			self._deviceID, SENSOR_RTD1, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Read sensor 1')
		self._sensorTemperature[sensor] = T
		return self._sensorTemperature[SENSOR_RTD1]

	def readSensor2Temperature (self):
		self.check_connected()
		sensor, T, timeout = libxtcon.getSensorTemperature (
			self._deviceID, SENSOR_RTD2, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Read sensor 2')
		self._sensorTemperature[sensor] = T
		return self._sensorTemperature[SENSOR_RTD2]

	def readSensor3Temperature (self):
		self.check_connected()
		sensor, T, timeout = libxtcon.getSensorTemperature (
			self._deviceID, SENSOR_TC1, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Read sensor 3')
		self._sensorTemperature[sensor] = T
		return self._sensorTemperature[SENSOR_TC1]

	def getSampleTemperature (self):
		sensor  = Preferences.getSampleTemperatureSensor()
		if (sensor == Preferences.KTYPE_TC):
			T = self.readSensor3Temperature()

		elif (sensor == Preferences.PT100):
			T = self.readSensor2Temperature()

		else: raise ValueError (sensor)
		return T

	def getHeaterTemperature (self):
		return self.readSensor1Temperature()

	def getColdJunctionTemperature (self):
		sensor  = Preferences.getSampleTemperatureSensor()
		if (sensor == Preferences.KTYPE_TC):
			T = self.readSensor2Temperature()

		elif (sensor == Preferences.PT100):
			T = 0.0

		else: raise ValueError (sensor)

		return T

	def getHeaterPower (self):
		self.check_connected()
		_, _, heaterPower, timeout = libxtcon.getPidStatus (
			self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Get heater power')
		self._heaterPower = heaterPower
		return heaterPower

	def saveCalibration (self):
		self.check_connected()
		timeout = libxtcon.saveSensorCalibration (
			self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Save calibration')

	def loadCalibration (self):
		self.check_connected()
		timeout = libxtcon.loadSensorCalibration (
			self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Load calibration')

	def loadDefaultCalibration (self):
		self.check_connected()
		timeout = libxtcon.loadSensorDefaultCalibration (
			self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Load default calibration')

	def htrPT100Calibration (self, R = 100.0):
		self.check_connected()
		sensor, key, ret_R, timeout = libxtcon.setRtdCalibration (
			self._deviceID, SENSOR_RTD1, 0, R, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Heater Pt100 calibration')

	def cjPT100Calibration (self, R = 100.0):
		self.check_connected()
		sensor, key, ret_R, timeout = libxtcon.setRtdCalibration (
			self._deviceID, SENSOR_RTD2, 0, R, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Cold-junction Pt100 calibration')

	def tcGain0mVCalibration (self):
		# in mV
		V = 0.00
		index = 0
		self.check_connected()
		sensor, i, ret_V, timeout = libxtcon.setThcoupleCalibration	(
			self._deviceID, SENSOR_TC1, index, V, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Thermocouple offset calibration')

	def tcGain4p99mVCalibration (self, V = 4.99):
		# in mV
		index = 1
		self.check_connected()
		sensor, i, ret_V, timeout = libxtcon.setThcoupleCalibration (
			self._deviceID, SENSOR_TC1, index, V, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Thermocouple span calibration')

	def getPID (self):
		self.check_connected()
		P, I, D, IRange, _, timeout = libxtcon.getPidAttribs (
			self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Get PID')
		self._P = P
		self._I = I
		self._D = D
		self._IRange = IRange
		return (P, round(I,8), D, IRange)

	def setPID (self, P, I, D, IRange):
		self.check_connected()
		P, I, D, IRange, _, timeout = libxtcon.setPidAttribs (
			self._deviceID, P, I, D, IRange, self._ctrlSensor,
			COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Set PID')
		self._P = P
		self._I = I
		self._D = D
		self._IRange = IRange
		return (P, round(I,8), D, IRange)

	def getCtrlSensor (self):
		self.check_connected()
		_, _, _ , _, ctrlSensor, timeout = libxtcon.getPidAttribs (
			self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Get control sensor')
		self._ctrlSensor = ctrlSensor
		return ctrlSensor

	def setCtrlSensor (self, sensor):
		self.check_connected()
		_, _, _ , _, ctrlSensor, timeout = libxtcon.setPidAttribs (
			self._deviceID, self._P, self._I, self._D,
			self._IRange, sensor, COMM_TIMEOUT_INTERVAL)

		self.check_timeout (timeout, 'Set control sensor')
		self._ctrlSensor = ctrlSensor
		return ctrlSensor

	def getIsothermalSetpoint (self):
		self.check_connected()
		_, setpoint, _, timeout = libxtcon.getPidStatus (
			self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Get isothermal setpoint')
		self._isothermalSetpoint = setpoint
		return setpoint

	def setIsothermalSetpoint (self, setpoint):
		self.check_connected()
		setpoint, timeout = libxtcon.setIsothermal (
			self._deviceID, setpoint, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Set isothermal setpoint')
		self._isothermalSetpoint = setpoint
		return setpoint

	def getLinearRamp (self):
		return (self._rampFinalTemp, self._rampRate)

	def setLinearRamp (self, rampFinalT, rampRate):
		self.check_connected()
		rampFinalT, rampRate, timeout = libxtcon.setLinearRamp (
			self._deviceID, rampFinalT, rampRate, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Set linear ramp')
		self._rampFinalTemp = rampFinalT
		self._rampRate = rampRate
		return (rampFinalT, rampRate)

	def startLinearRamp (self):
		self.check_connected()
		runMode, timeout = libxtcon.startRun (
			self._deviceID, TCON_RUN_MODE_LINEAR_RAMP, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Start linear ramp')
		self._runMode = runMode

	def stopLinearRamp (self):
		self.check_connected()
		timeout = libxtcon.stopRun (self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Stop linear ramp')
		self.getRunMode()

	def startIsothermalControl (self):
		self.check_connected()
		runMode, timeout = libxtcon.startRun (
			self._deviceID, TCON_RUN_MODE_ISOTHERMAL, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Start isothermal control')
		self._runMode = runMode

	def stopIsothermalControl (self):
		self.check_connected()
		timeout = libxtcon.stopRun (self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Stop isothermal control')
		self.getRunMode()

	def getRunMode (self):
		self.check_connected()
		runMode, _, _, timeout = libxtcon.getPidStatus (
			self._deviceID, COMM_TIMEOUT_INTERVAL)
		self.check_timeout (timeout, 'Get run mode')
		self._runMode = runMode
		return runMode

	def heaterActive (self):
		return (self.getRunMode() != TCON_RUN_MODE_IDLE)

class _Applet:

	def __init__ (self, oTCON):

		self.oTCON = oTCON
		self._plots = {}
		self._taskq = XTaskQueue()
		self._lastPlotUpdateAt = 0.0
		self._hApplet = self.oTCON.oApp.master.after (50, self._applet)

	def _applet (self):

		self._taskq.process()
		oApp = self.oTCON.oApp

		t = systime()
		if t >= self._lastPlotUpdateAt + 2:
			self._lastPlotUpdateAt = t

			for (wPlot, trace1, trace2) in self._plots.values():
				if wPlot.damaged() : wPlot.redraw()

		self._hApplet = oApp.master.after (50, self._applet)

	def schedule_task (self, task, *args):
		self._taskq.push (task, *args)

	def setConnectionStatus (self, status):
		self.oTCON.oApp.setConnectionStatus (status)

	def setRunMode (self, runMode):
		self.oTCON.oApp.setRunMode (runMode)
		self.oTCON.runMode = runMode

	def setRunControlStatus (self, status):
		self.oTCON.oApp.setRunControlStatus (status)

	def refresh (self):
		self.oTCON.oApp.master.update()

	def close (self):
		oApp = self.oTCON.oApp
		oApp.close()
		oApp.master.after_cancel (self._hApplet)
		oApp.master.destroy()

	# +++++++++++++ GUI set functions +++++++++++++++

	def setDisplayedParameters (self,
								heaterTemperature,
								heaterPower,
								heaterSetpoint,
								sampleTemperature):
		oApp = self.oTCON.oApp
		oApp.setHeaterTemperature (heaterTemperature)
		oApp.setHeaterPower       (heaterPower)
		oApp.setHeaterSetpoint	  (heaterSetpoint)
		oApp.setSampleTemperature (sampleTemperature)

	def initPlot (self, thread, title, xlabel, ylabel, key1, key2):
		oApp = self.oTCON.oApp
		wPlot = oApp.newPlot (title)
		wPlot.xlabel (xlabel)
		wPlot.ylabel (ylabel)
		trace1 = wPlot.new_dataset ('k-', key1)
		trace2 = wPlot.new_dataset ('b-', key2)
		wPlot.damage()
		self._plots[thread] = (wPlot, trace1, trace2)

	def updatePlot (self, thread, datapoint):

		(wPlot, trace1, trace2) = self._plots[thread]

		wPlot.add_datapoint (
			trace1, datapoint.time, datapoint.heaterTemperature)

		wPlot.add_datapoint (
			trace2, datapoint.time, datapoint.sampleTemperature)

		wPlot.damage()

	def clearPlot (self):
		oApp = self.oTCON.oApp
		oApp.clearPlot()
		self._plots.clear()

	def set_status (self, text):
		self.oTCON.oApp.set_status (text)

	# +++++++++++++ Variable set functions +++++++++++++++

	def setIsothermalTemperature (self, T):
		self.oTCON.oApp.setIsothermalSettingsDisplay (T)
		self.oTCON.isothermalSetpoint = T

	def setRampParameters (self, finalTemperature, rampRate):
		self.oTCON.oApp.setRampSettingsDisplay (finalTemperature, rampRate)
		self.oTCON.rampFinalTemperature = finalTemperature
		self.oTCON.rampRate             = rampRate

	def setStepTable (self, table):
		self.oTCON.stepTable = table

	def setPID (self, P, I, D, IRange):

		text = ('PID values set to: '
			+ 'P = ' + str (P) + ', '
			+ 'I = ' + str (I) + ', '
			+ 'D = ' + str (D) + ', '
			+ 'IRange = ' + str (IRange))

		self.oTCON.oApp.set_status (text)
		self.oTCON.pid.set (P, I, D, IRange)

	# ++++ Set settings display ++++

	def setSteppedRampDisplay (
		self, rampIndex, heaterSetpoint, state, *args):

		self.oTCON.oApp.setSteppedRampDisplay (
			rampIndex, heaterSetpoint, state, *args)

	# ++++ Display Calibration Confirmation ++++++

	def saveCalibration (self):
		text = 'Calibration Saved'
		self.oTCON.oApp.set_status (text)

	def loadCalibration (self):
		text = 'Calibration Loaded'
		self.oTCON.oApp.set_status (text)

	def loadDefaultCalibration (self):
		text = 'Default Calibration Loaded'
		self.oTCON.oApp.set_status (text)
		self.oTCON.Pt100_R = DEFAULT_PT100_R
		self.oTCON.TC_mV   = DEFAULT_TC_VOLTAGE

	def htrPt100Calibration (self, R):
		text = 'Heater Pt100 Calibrated'
		self.oTCON.oApp.set_status (text)
		self.oTCON.Pt100_R = R

	def cjPt100Calibration (self, R):
		text = 'Cold Junction Pt100 Calibrated'
		self.oTCON.oApp.set_status (text)
		self.oTCON.Pt100_R = R

	def tcGain0mVCalibration (self):
		text = 'ThermoCouple Calibrated at 0mV'
		self.oTCON.oApp.set_status (text)

	def tcGain4p99mVCalibration (self, mV):
		text = 'ThermoCouple Calibrated at 4.99mV'
		self.oTCON.oApp.set_status (text)
		self.oTCON.TC_mV   = mV

	def acquisition_atexit (self):
		self.oTCON.releaseAcquisition()

	def devicethread_atexit (self):
		self.oTCON.releaseDeviceThread();

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _DeviceThread (XThread):

	def __init__ (self, oTCON):

		XThread.__init__ (self, daemon = True)

		self.t0 = systime()
		self.oTCON = oTCON
		self.oTCON.oDriver.callback (self.driverCB)

	def thread (self):

		lastPollAt = 0.0

		while True:

			try:

				while True:

					sleep (0.05)
					self.do_tasks()

					t = systime()
					if t >= lastPollAt + 1:

						lastPollAt = t
						self.acquire_n_display()

			except LinkError:
				pass

			except CommError as e :
				oApplet = self.oTCON.oApplet
				oApplet.schedule_task (oApplet.set_status, str (e))

			except XTerminate: break

		self.disconnectDevice()

	def acquire_n_display (self):

		oTCON   = self.oTCON
		oApplet = oTCON.oApplet
		oDriver = oTCON.oDriver

		try:
			oDriver.acquire_lock()

			(heaterTemperature, sampleTemperature) = \
				oTCON.cryostat.temperature_remap (
					oDriver.readSensor1Temperature(),
					oDriver.readSensor2Temperature())

			heaterSetpoint      = oDriver.getIsothermalSetpoint()
			heaterPower         = oDriver.getHeaterPower()

			oApplet.schedule_task (oApplet.setDisplayedParameters,
									heaterTemperature,
									heaterPower,
									heaterSetpoint,
									sampleTemperature)
		finally:
			oDriver.release_lock()

	def driverCB (self, context, *args):

		oApplet = self.oTCON.oApplet

		if context == DEVICE_CONNECTED:
			oApplet.schedule_task (
				oApplet.setConnectionStatus, DEVICE_CONNECTED)

		elif context == DEVICE_NOT_FOUND:
			oApplet.schedule_task (
				oApplet.setConnectionStatus, DEVICE_NOT_FOUND)

		elif context == DEVICE_DISCONNECTED:
			oApplet.schedule_task (
				oApplet.setConnectionStatus, DEVICE_DISCONNECTED)

	def connectDevice (self):
		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		oApplet.schedule_task (oApplet.setConnectionStatus, DEVICE_CONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.open (Preferences.get_XTCON_serialNo())

		finally:
			oDriver.release_lock()

	def disconnectDevice (self):
		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		oApplet.schedule_task (
			oApplet.setConnectionStatus, DEVICE_DISCONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.close()

		finally:
			oDriver.release_lock()

	def setPID (self, P, I, D, IRange):

		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		try:
			oDriver.acquire_lock()
			(P, I, D, IRange) = oDriver.setPID (P, I, D, IRange)
			oApplet.schedule_task (oApplet.setPID, P, I, D, IRange)

		finally:
			oDriver.release_lock()

	def saveCalibration (self):

		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.saveCalibration ()
			oApplet.schedule_task (oApplet.saveCalibration)

		finally:
			oDriver.release_lock()

	def loadCalibration (self):

		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.loadCalibration ()
			oApplet.schedule_task (oApplet.loadCalibration)

		finally:
			oDriver.release_lock()

	def loadDefaultCalibration (self):

		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.loadDefaultCalibration ()
			oApplet.schedule_task (oApplet.loadDefaultCalibration)

		finally:
			oDriver.release_lock()

	def htrPt100Calibration (self, R):

		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.htrPT100Calibration (R)
			oApplet.schedule_task (oApplet.htrPt100Calibration, R)

		finally:
			oDriver.release_lock()

	def cjPt100Calibration (self, R):

		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.cjPT100Calibration (R)
			oApplet.schedule_task (oApplet.cjPt100Calibration, R)

		finally:
			oDriver.release_lock()

	def tcGain0mVCalibration (self):

		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.tcGain0mVCalibration ()
			oApplet.schedule_task (oApplet.tcGain0mVCalibration)

		finally:
			oDriver.release_lock()

	def tcGain4p99mVCalibration (self, mV):

		oApplet = self.oTCON.oApplet
		oDriver = self.oTCON.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.tcGain4p99mVCalibration (mV)
			oApplet.schedule_task (oApplet.tcGain4p99mVCalibration, mV)

		finally:
			oDriver.release_lock()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Module (XThreadModule):

	def __init__ (self, master, oTCON):
		XThreadModule.__init__ (self, master)
		self.oTCON   = oTCON
		self.t0      = systime()
		self.dataset = DataSet()
		self.fd_log  = None
		self._alive  = False

	# ++++ Useful functions used by derived classes ++++

	'''
		Redefine these in the derived class
		to set run-specific folder name and extension.
	'''

	def folder_name (self):
		return 'tcon'

	def run_type (self):
		return ''

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Temperature (K)'

	def is_alive (self):
		return True if self._alive else False

	def init (self):

		oTCON       = self.oTCON
		oApplet     = oTCON.oApplet
		self._alive = True

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
				self.xlabel(), self.ylabel(), 'Heater', 'Sample')

			text = self.run_type() + ' started'
			oApplet.schedule_task (oApplet.set_status, text)
			oApplet.schedule_task (oApplet.setRunControlStatus, RUN_STARTED)

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

	def atexit (self):

		oTCON   = self.oTCON
		oApplet = oTCON.oApplet

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

		self._alive = False

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquire_datapoint (self, bg_task, *bg_tasks):

		oTCON   = self.oTCON
		oApplet = oTCON.oApplet
		oDriver = oTCON.oDriver

		self.do_tasks (bg_task, *bg_tasks)

		try:
			oDriver.acquire_lock()

			t                   = systime() - self.t0

			(heaterTemperature, sampleTemperature) = \
				oTCON.cryostat.temperature_remap (
					oDriver.readSensor1Temperature(),
					oDriver.readSensor2Temperature())

			coldJuncTemperature = oDriver.getColdJunctionTemperature()
			heaterSetpoint      = oDriver.getIsothermalSetpoint()
			heaterPower         = oDriver.getHeaterPower()

		finally:
			oDriver.release_lock()

		return DataPoint (
			time                = t,
			sampleTemperature   = sampleTemperature,
			heaterTemperature   = heaterTemperature,
			coldJuncTemperature = coldJuncTemperature,
			heaterSetpoint      = heaterSetpoint,
			heaterPower         = heaterPower)

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
			('02 Sample Temperature',  'K'),
			('03 Heater Temperature',  'K'),
			('04 CJ Temperature',      'K'),
			('05 Heater Setpoint',     'K'),
			('06 Heater power',        '%')
		]

		(sampleName, sampleID, sampleDescription) = self.oTCON.sample.get()
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

			('Sample temperature',
				'%-.2f', datapoint.sampleTemperature,
				1.0, 'K'),

			('Heater temperature',
				'%-.1f', datapoint.heaterTemperature,
				1.0, 'K'),

			('CJ temperature',
				'%-.1f', datapoint.coldJuncTemperature,
				1.0, 'K'),

			('Heater setpoint',
				'%-.1f', datapoint.heaterSetpoint,
				1.0, 'K'),

			('Heater power',
				'%-.0f', datapoint.heaterPower,
				1.0, '%')
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
		dict.set_sample (self.oTCON.sample.get())

		fields = [
			(
				'01 Time',
				DATASET_COL_TIME, 1.0, 'sec'
			),

			(
				'02 Sample Temperature',
				DATASET_COL_SAMPLE_TEMPERATURE, 1.0, 'K'
			),

			(
				'03 Heater Temperature',
				DATASET_COL_HEATER_TEMPERATURE, 1.0, 'K'
			),

			(
				'04 CJ Temperature',
				DATASET_COL_CJ_TEMPERATURE, 1.0, 'K'
			),

			(
				'05 Heater Setpoint',
				DATASET_COL_HEATER_SETPOINT, 1.0, 'K'
			),

			(
				'06 Heater Power',
				DATASET_COL_HEATER_POWER, 100.0, '%'
			)
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

		(sampleName, sampleID, _) = self.oTCON.sample.get()

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

class _AcquisitionThread (XThread):

	def __init__ (self, module):
		XThread.__init__ (self, daemon = True)
		self.module = module

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _MonitorModule (_Module):

	def __init__ (self, master, oTCON):
		_Module.__init__(self, master, oTCON)

	def run_type (self):
		return 'Monitor'

	def init (self):
		_Module.init (self)
		oApplet = self.oTCON.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_MONITOR)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oTCON   = self.oTCON
		oApplet = oTCON.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			datapoint = (
				self.acquire_datapoint (
					self.do_tasks, bg_task, *bg_tasks))

			self.update_log (datapoint)
			self.dataset.append (datapoint)
			oApplet.schedule_task (oApplet.updatePlot, self, datapoint)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
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

		except (CommError, LinkError) : pass
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _IsothermalModule (_Module):

	def __init__ (self, master, oTCON, K):
		_Module.__init__ (self, master, oTCON)
		self.heaterSetpoint = K

	def run_type (self):
		return 'Isothermal'

	def init (self):
		_Module.init (self)

		oTCON   = self.oTCON
		oDriver = oTCON.oDriver
		oApplet = self.oTCON.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_ISOTHERMAL)

		try:
			oDriver.acquire_lock()

			self.heaterSetpoint = \
				oDriver.setIsothermalSetpoint (self.heaterSetpoint)

			oDriver.startIsothermalControl()

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		finally:
			oDriver.release_lock()

	def atexit (self):

		oTCON   = self.oTCON
		oDriver = oTCON.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.stopIsothermalControl()

		except (CommError, LinkError) : pass
		finally                       : oDriver.release_lock()

		_Module.atexit (self)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oTCON   = self.oTCON
		oApplet = oTCON.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			datapoint = (
				self.acquire_datapoint (
					self.do_tasks, bg_task, *bg_tasks))

			self.update_log (datapoint)
			self.dataset.append (datapoint)
			oApplet.schedule_task (oApplet.updatePlot, self, datapoint)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

	def setIsothermalSetpoint (self, heaterSetpoint):

		oTCON   = self.oTCON
		oDriver = oTCON.oDriver
		oApplet  = oTCON.oApplet

		try:
			oDriver.acquire_lock()

			self.heaterSetpoint = \
				oDriver.setIsothermalSetpoint (heaterSetpoint)

			text = 'Heater setpoint updated'
			oApplet.schedule_task (oApplet.set_status, text)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		finally:
			oDriver.release_lock()

		return self.heaterSetpoint

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _IsothermalAcquisitionThread (_AcquisitionThread):

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

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _LinearRampModule (_Module):

	def __init__ (self, master, oTCON, final_temperature, ramp_rate):
		_Module.__init__(self, master, oTCON)
		self.finalTemperature = final_temperature
		self.rampRate         = ramp_rate
		self._complete        = False

	def run_type (self):
		return 'LinearRamp'

	def init (self):

		_Module.init (self)

		self._complete = False
		oTCON          = self.oTCON
		oDriver        = oTCON.oDriver
		oApplet        = self.oTCON.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_LINEAR_RAMP)

		try:
			oDriver.acquire_lock()

			(self.finalTemperature, self.rampRate) = \
				oDriver.setLinearRamp (self.finalTemperature, self.rampRate)

			oDriver.startLinearRamp()

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		finally:
			oDriver.release_lock()

	def atexit (self):

		oTCON   = self.oTCON
		oDriver = oTCON.oDriver

		try:
			oDriver.acquire_lock()
			oDriver.stopLinearRamp()

		except (CommError, LinkError) : pass
		finally                       : oDriver.release_lock()

		_Module.atexit (self)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oTCON   = self.oTCON
		oApplet = oTCON.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			datapoint = (
				self.acquire_datapoint (
					self.do_tasks, bg_task, *bg_tasks))

			self.update_log (datapoint)
			self.dataset.append (datapoint)
			oApplet.schedule_task (oApplet.updatePlot, self, datapoint)

			if ((self.rampRate > 0)
			and (datapoint.sampleTemperature >= self.finalTemperature)):
				self._complete = True

			elif ((self.rampRate < 0)
			and (datapoint.sampleTemperature <= self.finalTemperature)):
				self._complete = True

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

	def setRampSettings (self, finalTemperature, rampRate):

		oTCON   = self.oTCON
		oDriver = oTCON.oDriver
		oApplet  = oTCON.oApplet

		try:
			oDriver.acquire_lock()

			(self.finalTemperature, self.rampRate) = \
				oDriver.setLinearRamp (finalTemperature, rampRate)

			text = 'Ramp settings updated'
			oApplet.schedule_task (oApplet.set_status, text)

		finally:
			oDriver.release_lock()

		return self.finalTemperature, self.rampRate

	def complete (self, datapoint = None):
		return True if self._complete else False

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RamppedAcquisitionThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		lastPollAt = 0.0

		try:

			self.module.init()

			while True:
				self.do_tasks()
				self.module.sleep (1, self.do_tasks)
				self.module.acquire_n_plot (self.do_tasks)
				if self.module.complete(): break

		except (CommError, LinkError) : pass
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _StepRampModule (_Module):

	def __init__ (self, master, oTCON, stepTable):
		_Module.__init__(self, master, oTCON)

		self.stepTable 			= stepTable

		self.activeStepIndex    = None
		self.state              = None
		self.heaterSetpoint     = None

		self.history            = None
		self.fluctuation        = None
		self.lastStateChangeAt  = None

	def run_type (self):
		return 'StepRamp'

	def init (self):

		_Module.init (self)
		oTCON   = self.oTCON
		oApplet = self.oTCON.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_STEPPED_RAMP)

		self.activeStepIndex    = 0
		self.state              = STEP_STATE_IDLE

		self.history            = deque()
		self.fluctuation        = (0.0, 0.0)
		self.lastStateChangeAt  = 0.0

	def atexit (self):
		oTCON   = self.oTCON
		oDriver = oTCON.oDriver
		oApplet = oTCON.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.stopIsothermalControl()

		except (CommError, LinkError) : pass
		finally                       : oDriver.release_lock()

		oApplet.schedule_task (
			oApplet.setSteppedRampDisplay, 0, 0.0, STEP_STATE_FINISHED)

		_Module.atexit (self)

	def setStepTable (self, stepTable):

		oTCON      = self.oTCON
		oDriver    = oTCON.oDriver
		oApplet    = oTCON.oApplet

		self.stepTable = stepTable

		self.activeStepIndex = self.stepTable.activeStepIndex (
			self.activeStepIndex, self.heaterSetpoint)

		if self.activeStepIndex == None:
			self.state = STEP_STATE_FINISHED

		text = 'Temperature step-table updated'
		oApplet.schedule_task (oApplet.set_status, text)

	def acquire_n_plot (self, bg_task = None, *bg_tasks):

		oTCON   = self.oTCON
		oApplet = oTCON.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			datapoint = (
				self.acquire_datapoint (
					self.do_tasks, bg_task, *bg_tasks))

			self.update_log (datapoint)
			self.dataset.append (datapoint)
			oApplet.schedule_task (oApplet.updatePlot, self, datapoint)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

	def set_n_stabilize (self, bg_task = None, *bg_tasks):

		oTCON   = self.oTCON
		oApplet = oTCON.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			self.initiateNextStep()

			if not self.complete():

				while True:

					self.do_tasks (bg_task, *bg_tasks)
					self.sleep (1, self.do_tasks, bg_task, *bg_tasks)

					datapoint = (
						self.acquire_datapoint (
							self.do_tasks, bg_task, *bg_tasks))

					self.checkStability (datapoint)
					self.update_log (datapoint)
					self.dataset.append (datapoint)
					oApplet.schedule_task (oApplet.updatePlot, self, datapoint)
					self.describe_state()

					if self.stable() : break

			else:
				datapoint = None

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

	def initiateNextStep (self):
		oTCON      = self.oTCON
		oDriver    = oTCON.oDriver

		if self.state == STEP_STATE_IDLE:
			self.activeStepIndex = 0
			self.heaterSetpoint = (self.activeStep().initialTemperature)

		else:
			(self.activeStepIndex, self.heaterSetpoint) = (
				self.stepTable.nextTemperature (
					self.activeStepIndex, self.heaterSetpoint))

		if self.activeStepIndex != None:
			self.history.clear()
			self.state = STEP_STATE_PREDELAY
			self.lastStateChangeAt = systime()

			try:
				oDriver.acquire_lock()
				oDriver.setIsothermalSetpoint (self.heaterSetpoint)

				if not oDriver.heaterActive():
					oDriver.startIsothermalControl()

			finally:
				oDriver.release_lock()

		else:
			self.state = STEP_STATE_FINISHED

	def activeStep (self):
		return self.stepTable[self.activeStepIndex]

	def checkStability (self, datapoint = None):

		if datapoint == None:
			datapoint = self.acquire_datapoint()

		if self.state == STEP_STATE_PREDELAY:

			t = systime()
			if t >= self.lastStateChangeAt + self.activeStep().preDelay:

				self.lastStateChangeAt = t
				self.history.clear()
				self.state = STEP_STATE_CHECK_STABILITY

		if self.state == STEP_STATE_CHECK_STABILITY:

			self.history.append (datapoint)
			oldest_time = self.history[0].time
			latest_time = self.history[-1].time

			history = []
			for item in self.history:
				history.append (item.sampleTemperature)

			max_temp = max (history); min_temp = min (history)

			self.fluctuation = (
				latest_time - oldest_time, max_temp - min_temp)

			'''
			Remove older datapoints which are not
			useful for stability measurement
			'''
			while True:

				if len (self.history) == 0:
					break

				oldest_time = self.history[0].time
				latest_time = self.history[-1].time

				if oldest_time > latest_time - self.activeStep().period:
					break

				self.history.popleft()

			(dt, dT) = self.fluctuation

			if (dt >= self.activeStep().period
			and dT <= self.activeStep().tolerance):

				self.lastStateChangeAt = systime()
				self.state = STEP_STATE_POSTDELAY

		if self.state == STEP_STATE_POSTDELAY:

			t = systime()
			if t >= self.lastStateChangeAt + self.activeStep().postDelay:
				self.lastStateChangeAt = t
				self.state = STEP_STATE_STABLE
				return True

		return False

	def complete (self):
		return (self.state == STEP_STATE_FINISHED)

	def stable (self):
		return (self.state == STEP_STATE_STABLE)

	def describe_state (self):
		oTCON   = self.oTCON
		oApplet = oTCON.oApplet

		remaining_time = 0.0

		if self.state == STEP_STATE_IDLE:
			oApplet.schedule_task (
				oApplet.setSteppedRampDisplay,
				self.activeStepIndex, self.heaterSetpoint, self.state)

		elif self.state == STEP_STATE_PREDELAY:
			remaining_time = (self.lastStateChangeAt +
				self.activeStep().preDelay - systime())
			oApplet.schedule_task (
				oApplet.setSteppedRampDisplay,
					self.activeStepIndex, self.heaterSetpoint,
						self.state, remaining_time)

		elif self.state == STEP_STATE_CHECK_STABILITY:
			(dt, dT) = self.fluctuation
			oApplet.schedule_task (
				oApplet.setSteppedRampDisplay,
					self.activeStepIndex, self.heaterSetpoint,
						self.state, dT, dt)

		elif self.state == STEP_STATE_POSTDELAY:
			remaining_time = (self.lastStateChangeAt +
				self.activeStep().postDelay - systime())
			oApplet.schedule_task (
				oApplet.setSteppedRampDisplay,
					self.activeStepIndex, self.heaterSetpoint,
						self.state, remaining_time)

		elif self.state == STEP_STATE_STABLE:
			oApplet.schedule_task (
				oApplet.setSteppedRampDisplay,
					self.activeStepIndex, self.heaterSetpoint,
						self.state)

		elif self.state == STEP_STATE_FINISHED:
			oApplet.schedule_task (
				oApplet.setSteppedRampDisplay,
					self.activeStepIndex, self.heaterSetpoint,
						self.state)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _SteppedAcquisitionThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def run_type (self):
		return 'StepRamp'

	def thread (self):

		lastPollAt  = 0.0

		try:

			self.module.init()

			while True:
				self.do_tasks()
				self.module.set_n_stabilize (self.do_tasks)
				if self.module.complete() : break

		except (CommError, LinkError) : pass
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

def TCON (master, sample, cryostat):

	if TCON.singleton == None:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()

		oApp           = GUI   (win, sample)
		TCON.singleton = _TCON (oApp, sample, cryostat)

	if master not in TCON.master:
		TCON.master.append (master)

	return TCON.singleton

def closeTCON (master):

	if master in TCON.master:
		TCON.master.remove (master)

	if len (TCON.master) == 0 and TCON.singleton:
		TCON.singleton.close()
		TCON.singleton = None

TCON.singleton = None
TCON.master    = []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _PID:

	def __init__ (self):
		self.P      = 0.5
		self.I      = 0.004
		self.D      = 1.0
		self.IRange = 3.0

	def set (self, P, I, D, IRange):
		self.P      = P
		self.I      = I
		self.D      = D
		self.IRange = 3.0

	def get (self):
		return (self.P, self.I, self.D, self.IRange)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _TCON:

	def __init__ (self, oApp, sample, cryostat):

		self.oApp = oApp
		self.oApp.callback (self.oAppCB)
		self.sample = sample
		self.cryostat = cryostat
		self.oDriver  = Driver()

		# ++++ Isothermal settings ++++
		self.isothermalSetpoint = 300

		# ++++ Ramp settings ++++
		self.rampFinalTemperature = 450
		self.rampRate = 1.0

		# ++++ Step settings ++++

		self.stepTable = StepTable()
		for i in range (0, 10):
			self.stepTable.append (StepEntry())

		# ++++ Pt100 Calibration Settings++++
		self.Pt100_R = DEFAULT_PT100_R
		self.TC_mV = DEFAULT_TC_VOLTAGE

		# ++++ Control settings ++++
		self.pid = _PID()

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

		# ++++ synchronize app ++++

		self.oApplet.schedule_task (
			self.oApplet.setIsothermalTemperature,
			self.isothermalSetpoint)

		self.oApplet.schedule_task (
			self.oApplet.setRampParameters,
			self.rampFinalTemperature,
			self.rampRate)

		self.oApplet.schedule_task (
			self.oApplet.setStepTable,
			self.stepTable)

		self.oApplet.schedule_task (
			self.oApplet.setRunMode,
			self.runMode)

		# ++++ Attempt for auto-connect ++++

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

		thread = None

		if self.oDeviceThread == None:

			thread = _DeviceThread (self)
			thread.atexit (self.devicethread_atexit)
			self.oDeviceThread = thread

		else:
			raise ResourceError (
				'TCON_ResourceError: Device thread unavailable')

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
		elif context == OPEN_DIALOG       : self.openDialog (*args)
		elif context == OPEN_METHOD       : self.openMethod (*args)
		elif context == SAVE_METHOD       : self.saveMethod (*args)
		elif context == OPEN_DEVICE       : self.open_device (*args)
		else                              : raise ValueError (context)

	# ---------------- Connection functions ----------------------

	def connectDevice (self):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		oApplet.setConnectionStatus (DEVICE_CONNECTING)
		oDeviceThread.schedule_task (oDeviceThread.connectDevice)
		oDeviceThread.schedule_task (oDeviceThread.setPID, *self.pid.get())

	def disconnectDevice (self):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		oApplet.setConnectionStatus (DEVICE_DISCONNECTING)
		oDeviceThread.schedule_task (oDeviceThread.disconnectDevice)

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

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareModule (self, master, runMode):

		module = None

		if self.oModule == None:

			if runMode == RUN_MODE_MONITOR:
				module = _MonitorModule (master, self)

			elif runMode == RUN_MODE_ISOTHERMAL:
				module = _IsothermalModule (
					master, self, self.isothermalSetpoint)

			elif runMode == RUN_MODE_LINEAR_RAMP:
				module = _LinearRampModule (
					master, self, self.rampFinalTemperature, self.rampRate)

			elif runMode == RUN_MODE_STEPPED_RAMP:
				module = _StepRampModule (master, self, self.stepTable)

			else:
				raise ResourceError (
					'TCON_ResourceError: Module creation failed')

			self.oModule = module

		else:
			raise ResourceError (
				'TCON_ResourceError: Module unavailable')

		return module

	def releaseModule (self, caller):
		if self.oModule and caller == self.oModule.master:
			self.oModule = None

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareAcquisition (self, runMode):

		thread = None

		try:

			if self.oAcqThread == None:

				module = self.prepareModule (self, runMode)

				if runMode == RUN_MODE_MONITOR:
					thread = _MonitorThread (module)

				elif runMode == RUN_MODE_ISOTHERMAL:
					thread = _IsothermalAcquisitionThread (module)

				elif runMode == RUN_MODE_LINEAR_RAMP:
					thread = _RamppedAcquisitionThread (module)

				elif runMode == RUN_MODE_STEPPED_RAMP:
					thread = _SteppedAcquisitionThread (module)

				else:
					raise ResourceError (
						'TCON_ResourceError: Thread creation failed')

				thread.atexit (self.acquisition_atexit)
				self.oAcqThread = thread

			else:
				raise ResourceError (
					'TCON_ResourceError: Thread unavailable')

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

	# ++++++++ Settings and Tools dialog callback functions ++++++++

	def openDialog (self, dialog):
		if   dialog == ISOTHERMAL_DIALOG   : self.openIsothermalSettingsDialog()
		elif dialog == LINEAR_RAMP_DIALOG  : self.openLinearRampSettingsDialog()
		elif dialog == STEP_TABLE_DIALOG   : self.openStepTableDialog()
		elif dialog == PID_SETTINGS_DIALOG : self.openPIDSettingsDialog()
		elif dialog == CALIBRATION_DIALOG  : self.openCalibrationDialog()
		else: raise ValueError (dialog)

	# ++++ Isothermal settings ++++

	def openIsothermalSettingsDialog (self):

		# Creates a GUI_IsothermalSettings dialog
		w = self.dialog = GUI_IsothermalSettings (
			Toplevel (takefocus = True), self.isothermalSetpoint)

		# Registers a callback to the newly created dialog
		w.callback (self.isothermalSettingsDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def isothermalSettingsDialogCB (self, context, *args):

		oApplet    = self.oApplet
		oModule    = self.oModule

		if context == APPLY:

			oApplet.setIsothermalTemperature (*args)

			if oModule and isinstance (oModule, _IsothermalModule):
				oModule.schedule_task (oModule.setIsothermalSetpoint, *args)

			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# ++++ Ramp settings ++++

	def openLinearRampSettingsDialog (self):

		# Creates a GUI_RampSettings dialog
		w = self.dialog = GUI_RampSettings (
			Toplevel (takefocus = True),
			self.rampFinalTemperature, self.rampRate)

		# Registers a callback to the newly created dialog
		w.callback (self.linearRampSettingsDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def linearRampSettingsDialogCB (self, context, *args):

		oApplet = self.oApplet
		oModule = self.oModule

		if context == APPLY:

			oApplet.setRampParameters (*args)

			if oModule and isinstance (oModule, _LinearRampModule):
				oModule.schedule_task (oModule.setRampSettings, *args)

			self.dialog.master.destroy()
			self.dialog = None

		if context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

	# ++++ Step settings ++++

	def openStepTableDialog (self):

		# Creates a GUI_StepSettings dialog
		w = self.dialog = GUI_StepSettings (
			Toplevel (takefocus = True),
			copy.deepcopy (self.stepTable))

		# Registers a callback to the newly created dialog
		w.callback (self.stepTableDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def stepTableDialogCB (self, context, *args):

		oApplet = self.oApplet
		oModule = self.oModule

		if context == APPLY:

			oApplet.setStepTable (*args)

			if oModule and isinstance (oModule, _StepRampModule):
				oModule.schedule_task (oModule.setStepTable, *args)

			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# ++++ PID settings ++++

	def openPIDSettingsDialog (self):

		# Creates a GUI_PIDSettings dialog
		w = self.dialog = GUI_PIDSettings (
			Toplevel (takefocus = True), *self.pid.get())

		# Registers a callback to the newly created dialog
		w.callback (self.pidSettingsDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def pidSettingsDialogCB (self, context, *args):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		if context == APPLY:
			oApplet.schedule_task (oApplet.setPID, *args)
			oDeviceThread.schedule_task (oDeviceThread.setPID, *args)
			self.dialog.master.destroy()
			self.dialog = None

		elif context == CANCEL:
			self.dialog.master.destroy()
			self.dialog = None

		else: raise ValueError (context)

	# ++++ Calibration Tool ++++

	def openCalibrationDialog (self):

		# Creates a GUI_Calibration dialog
		w = self.dialog = GUI_Calibration (
							Toplevel (takefocus = True),
							self.Pt100_R, self.TC_mV)

		# Registers a callback to the newly created dialog
		w.callback (self.calibrationDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	def calibrationDialogCB (self, context, *args):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread

		if context == SAVE_CALIBRATION:

			oDeviceThread.schedule_task (oDeviceThread.saveCalibration)
			self.dialog.master.destroy()
			self.dialog = None

		elif context == LOAD_CALIBRATION:

			oDeviceThread.schedule_task (oDeviceThread.loadCalibration)
			self.dialog.master.destroy()
			self.dialog = None

		elif context == LOAD_DEFAULT_CALIBRATION:
			oApplet.schedule_task (oApplet.loadDefaultCalibration)
			oDeviceThread.schedule_task ( \
				oDeviceThread.loadDefaultCalibration)
			self.dialog.setPt100_R(DEFAULT_PT100_R)
			self.dialog.setTC_mV(DEFAULT_TC_VOLTAGE)

		elif context == HTR_PT100_CALIBRATION:
			oApplet.schedule_task (oApplet.htrPt100Calibration, *args)
			oDeviceThread.schedule_task ( \
				oDeviceThread.htrPt100Calibration, *args)

		elif context == CJ_PT100_CALIBRATION:
			oApplet.schedule_task (oApplet.cjPt100Calibration, *args)
			oDeviceThread.schedule_task ( \
				oDeviceThread.cjPt100Calibration, *args)

		elif context == TC_GAIN_CALIB_0:
			oDeviceThread.schedule_task ( \
				oDeviceThread.tcGain0mVCalibration)

		elif context == TC_GAIN_CALIB_499:
			oApplet.schedule_task (oApplet.tcGain4p99mVCalibration, *args)
			oDeviceThread.schedule_task ( \
				oDeviceThread.tcGain4p99mVCalibration, *args)

		else: raise ValueError (context)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMethod (self):
		method = Method()
		method.setRunMode (self.runMode)
		method.setIsothermalSettings (self.isothermalSetpoint)
		method.setRampSettings (self.rampFinalTemperature, self.rampRate)
		method.setStepSettings (self.stepTable)
		method.set_PID_Settings (*self.pid.get())
		method.set_cryostat_settings (self.cryostat.get_method())
		return method

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def applyMethod (self, method):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread
		oModule       = self.oModule

		mode = method.getRunMode (self.runMode)
		oApplet.schedule_task (oApplet.setRunMode, mode)

		# +++++++++++++++++++++++++++++++++++++

		setpoint = method.getIsothermalSettings (self.isothermalSetpoint)

		oApplet.schedule_task (
			oApplet.setIsothermalTemperature, setpoint)

		if oModule and isinstance (oModule, _IsothermalModule):
			oModule.schedule_task (oModule.setIsothermalSetpoint, setpoint)

		# +++++++++++++++++++++++++++++++++++++

		settings = method.getRampSettings (
			self.rampFinalTemperature, self.rampRate)

		oApplet.schedule_task (oApplet.setRampParameters, *settings)

		if oModule and isinstance (oModule, _LinearRampModule):
			oModule.schedule_task (oModule.setRampSettings, *settings)

		# +++++++++++++++++++++++++++++++++++++

		stepTable = method.getStepSettings()
		oApplet.schedule_task (oApplet.setStepTable, stepTable)

		if oModule and isinstance (oModule, _StepRampModule):
			oModule.schedule_task (oModule.setStepTable, stepTable)

		# +++++++++++++++++++++++++++++++++++++

		pid = method.get_PID_Settings (*self.pid.get())
		oApplet.schedule_task (oApplet.setPID, *pid)
		oDeviceThread.schedule_task (oDeviceThread.setPID, *pid)

		# +++++++++++++++++++++++++++++++++++++

		self.cryostat.apply_method (
			method.get_cryostat_settings (
				self.cryostat.get_method()))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

	def open_device (self, device):

		if device == CRYOSTAT_DEVICE : self.cryostat.show()
		else                         : raise ValueError (context)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

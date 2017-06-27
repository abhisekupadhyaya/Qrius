# coding: utf-8
import libxlia

from app_xlia       import GUI
from app_xlia       import GUI_ReferenceSettings
from app_xlia       import GUI_MeasurementSettings
from app_xlia       import GUI_AcquisitionSettings
from app_xlia       import GUI_VFRampSettings

from XDict          import XDict
from XThread        import XThread, XThreadModule, XTaskQueue, XTerminate
from Preferences    import get_XLIA_serialNo, getDataFolder
from Preferences    import get_XLIA_currentSenseResistance
from XLIA_DataType  import DataPoint, DataSet
from XLIA_Constants import *
from XLIA_Method    import Method, XMethodError

# Importing Python provided libraries
import os
from threading      import Thread, RLock
from time           import time as systime, localtime, sleep
from Tkinter        import Toplevel
from math           import log10

def Driver (dummy = False):

	if Driver.singleton == None:
		Driver.singleton = _Driver()

	return Driver.singleton

Driver.singleton = None

class LinkError     (Exception) : pass
class CommError     (Exception) : pass
class ResourceError (Exception) : pass

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _ReferenceParameters:

	def __init__ (self):
		self.amplitude = None
		self.frequency = None
		self.phase     = None

	def set (self, amplitude, frequency, phase):
		self.amplitude = amplitude
		self.frequency = frequency
		self.phase     = phase

	def get (self):
		return (self.amplitude, self.frequency, self.phase)

	def clear (self):
		self.amplitude = None
		self.frequency = None
		self.phase     = None

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _MeasurementSettings:

	def __init__ (self):
		self.inputChannel   = None
		self.preAmpCoupling = None
		self.preAmpGain     = None
		self.postAmpGain    = None
		self.intgtrTC       = None

	def set (self,
		  inputChannel   = None,
		  preAmpCoupling = None,
		  preAmpGain     = None,
		  postAmpGain    = None,
		  intgtrTC       = None):

		if inputChannel   != None : self.inputChannel   = inputChannel
		if preAmpCoupling != None : self.preAmpCoupling = preAmpCoupling
		if preAmpGain     != None : self.preAmpGain     = preAmpGain
		if postAmpGain    != None : self.postAmpGain    = postAmpGain
		if intgtrTC       != None : self.intgtrTC       = intgtrTC

	def get (self):
		return (
			self.inputChannel,
			self.preAmpCoupling,
			self.preAmpGain,
			self.postAmpGain,
			self.intgtrTC)

	def clear (self):
		self.inputChannel   = None
		self.preAmpCoupling = None
		self.preAmpGain     = None
		self.postAmpGain    = None
		self.intgtrTC       = None

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Driver:

	def __init__ (self):
		self._thlock  = RLock()
		self.deviceID            = None
		self.referenceParameters = _ReferenceParameters()
		self.measurementSettings = _MeasurementSettings()

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def scan (self):

		serialNos = []
		number_of_devices = libxlia.scan()

		for i in range (0, number_of_devices):
			serialNos.append (libxlia.serialNo (i))

		return serialNos

	def check_connected (self):
		if self.deviceID == None:
			raise LinkError ('XLIA_LinkError: Device not connected')

	def check_timeout (self, timeout, context = ''):
		if (timeout == 0.0):
			self.close()
			raise CommError ('XLIA_CommError: ' + str (context))

	def acquire_lock (self):
		self._thlock.acquire()

	def release_lock (self):
		self._thlock.release()

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def open (self, serialNo):

		if serialNo in self.scan():

			self.deviceID, goodID, timeout = (
				libxlia.open_device (serialNo, COMM_TIMEOUT_DELAY))

			if timeout != 0.0 and goodID:
				self.do_callback (DEVICE_CONNECTED)

			else:
				libxlia.close_device (self.deviceID)
				self.deviceID = None
				self.do_callback (DEVICE_NOT_FOUND)

		else:
			self.do_callback (DEVICE_NOT_FOUND)

	def close (self):

		if self.deviceID != None:
			libxlia.close_device (self.deviceID)
			self.deviceID       = None
			self.referenceParameters.clear()
			self.measurementSettings.clear()
			self.do_callback (DEVICE_DISCONNECTED)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setReferenceParameters (self, ampl, freq, phase):

		self.check_connected()

		ampl, freq, phase, timeout = \
			libxlia.setReferenceParameters (
				self.deviceID, ampl, freq, phase, COMM_TIMEOUT_DELAY)

		self.check_timeout (timeout, 'Set reference parameters')
		self.referenceParameters.set (ampl, freq, phase)
		self.do_callback (REFERENCE_PARAMETER, *self.referenceParameters.get())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setInputChannel (self, chn):

		self.check_connected()

		if (self.measurementSettings.inputChannel == None
		or  self.measurementSettings.inputChannel != chn):

			options = {
				INPUT_CHANNEL_INPUT_VOLTAGE     : 0,
				INPUT_CHANNEL_REFERENCE_CURRENT : 1
			}

			(enable, timeout) = libxlia.enablePreAmpNotch1 (
				self.deviceID, options[chn], COMM_TIMEOUT_DELAY)

			self.check_timeout (timeout, 'Set input channel')

			options = {
				0 : INPUT_CHANNEL_INPUT_VOLTAGE,
				1 : INPUT_CHANNEL_REFERENCE_CURRENT
			}

			chn = options[enable]

		self.measurementSettings.set (inputChannel = chn)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setPreAmpCoupling (self, coupling):

		self.check_connected()

		if (self.measurementSettings.preAmpCoupling == None
		or  self.measurementSettings.preAmpCoupling != coupling):

			options = {
				PREAMP_COUPLING_DC : 0,
				PREAMP_COUPLING_AC : 1
			}

			(enable, timeout) = libxlia.enablePreAmp_AC_Coupling (
					self.deviceID, options[coupling], COMM_TIMEOUT_DELAY)

			self.check_timeout (timeout, 'Set preamp coupling')

			options = {
				0 : PREAMP_COUPLING_DC,
				1 : PREAMP_COUPLING_AC
			}

			coupling = options[enable]

		self.measurementSettings.set (preAmpCoupling = coupling)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setPreAmpGain (self, gain):

		self.check_connected()

		if (self.measurementSettings.preAmpGain == None
		or  self.measurementSettings.preAmpGain != gain):

			options = {
				PREAMP_GAIN_1   : 0,
				PREAMP_GAIN_10  : 1,
				PREAMP_GAIN_100 : 2
			}

			gain, timeout = libxlia.setPreAmpGain (
				self.deviceID, options[gain], COMM_TIMEOUT_DELAY)

			self.check_timeout (timeout, 'Set preamp gain')

			options = {
				0 : PREAMP_GAIN_1,
				1 : PREAMP_GAIN_10,
				2 : PREAMP_GAIN_100
			}

			gain = options[gain]

		self.measurementSettings.set (preAmpGain = gain)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setPostAmpGain (self, gain):

		self.check_connected()

		if (self.measurementSettings.postAmpGain == None
		or  self.measurementSettings.postAmpGain != gain):

			options = {
				POSTAMP_GAIN_1   : 0,
				POSTAMP_GAIN_10  : 1,
				POSTAMP_GAIN_100 : 2
			}

			gain, timeout = libxlia.setPostAmpGain (
				self.deviceID, options[gain], COMM_TIMEOUT_DELAY)

			self.check_timeout (timeout, 'Set postamp gain')

			options = {
				0 : POSTAMP_GAIN_1,
				1 : POSTAMP_GAIN_10,
				2 : POSTAMP_GAIN_100
			}

			gain = options[gain]

		self.measurementSettings.set (postAmpGain = gain)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def _setIntgtrTC (self, tc):

		self.check_connected()

		if (self.measurementSettings.intgtrTC == None
		or  self.measurementSettings.intgtrTC != tc):

			options = {
				INTGTR_TC_2ms  : 0,
				INTGTR_TC_5ms  : 1,
				INTGTR_TC_1sec : 2
			}

			tc, timeout = libxlia.setIntegratorTimeConstant (
				self.deviceID, options[tc], COMM_TIMEOUT_DELAY)

			self.check_timeout (timeout, 'Set integrator time constants')

			options = {
				0 : INTGTR_TC_2ms,
				1 : INTGTR_TC_5ms,
				2 : INTGTR_TC_1sec
			}

			tc = options[tc]

		self.measurementSettings.set (intgtrTC = tc)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def setMeasurementSettings (self,
							 inputChannel   = None,
							 preAmpCoupling = None,
							 preAmpGain     = None,
							 postAmpGain    = None,
							 intgtrTC       = None):

		functions = [
			(self._setInputChannel   , inputChannel   ),
			(self._setPreAmpCoupling , preAmpCoupling ),
			(self._setPreAmpGain     , preAmpGain     ),
			(self._setPostAmpGain    , postAmpGain    ),
			(self._setIntgtrTC       , intgtrTC       )
		]

		for (fn, arg) in functions:
			if arg != None : fn (arg)

		self.do_callback (MEASUREMENT_SETTINGS,
					*self.measurementSettings.get())

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def doQuickMeasurement (self, filterLength):

		self.check_connected()

		'''
		** 2ms for each reading (emperical)
		'''
		timeout = max (COMM_TIMEOUT_DELAY, filterLength * 0.002)

		(outIP, outQP, amplitude,
			phase, timeout) = libxlia.doFilteredMeasurement (
				self.deviceID, filterLength, timeout)

		self.check_timeout (timeout, 'Do filtered measurement')
		return (outIP, outQP, amplitude, phase)

	def doMeasurement (self, filterLength):

		self.check_connected()

		'''
		** 2 second sleep after each phase adjust
		** 2ms for each reading (emperical)
		** Total four phase settings, viz. 0, 180, 270, 90.
		'''
		timeout = 4 * (2 + max (COMM_TIMEOUT_DELAY, filterLength * 0.002))

		(outIP, outQP, amplitude,
			phase, timeout) = libxlia.doFilteredMeasurement1 (
				self.deviceID, filterLength, 10 * COMM_TIMEOUT_DELAY)

		self.check_timeout (timeout, 'Do filtered measurement')
		return (outIP, outQP, amplitude, phase)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def doAutoRange (self):

		self.check_connected()

		(preAmpGain, postAmpGain, timeout) = \
			libxlia.auto_range (self.deviceID, 10 * COMM_TIMEOUT_DELAY)

		self.check_timeout (timeout, 'Do auto range')
		self.measurementSettings.set (
			preAmpGain = preAmpGain, postAmpGain = postAmpGain)

		self.do_callback (MEASUREMENT_SETTINGS,
					*self.measurementSettings.get())

		return (preAmpGain, postAmpGain)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def initialize (
		self, refAmpl, refFreq, refPhase,
		inputChannel, preAmpCoupling, preAmpGain, postAmpGain, intgtrTC):

		disable = 0
		self.check_connected()

		self.setReferenceParameters (refAmpl, refFreq, refPhase)

		self.setMeasurementSettings (
			inputChannel, preAmpCoupling,
			preAmpGain, postAmpGain, intgtrTC)

		(_, timeout) = \
			libxlia.enablePreAmpNotch2 (
				self.deviceID, disable, COMM_TIMEOUT_DELAY)

		self.check_timeout (timeout, 'Disable preamp notch-2')

		(_, timeout) = \
			libxlia.enableMultiplierExternalReference (
				self.deviceID, disable, COMM_TIMEOUT_DELAY)

		self.check_timeout (timeout, 'Disable multipler external reference')

		(_, timeout) = \
			libxlia.enableRelativeMeasurement (
				self.deviceID, disable, COMM_TIMEOUT_DELAY)

		self.check_timeout (timeout, 'Disable relative measurement')

'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''

class _Applet:

	def __init__ (self, oXLIA):
		self.oXLIA = oXLIA
		self._plots = {}
		self._taskq = XTaskQueue()
		self._lastPlotUpdateAt = 0.0
		self._hApplet = self.oXLIA.oApp.master.after (50, self._applet)

	def _applet (self):

		self._taskq.process()
		oApp = self.oXLIA.oApp

		t = systime()
		if t >= self._lastPlotUpdateAt + 2:
			self._lastPlotUpdateAt = t

			for (wPlot, traceID) in self._plots.values():
				if wPlot.damaged() : wPlot.redraw()

		self._hApplet = oApp.master.after (50, self._applet)

	def schedule_task (self, task, *args):
		self._taskq.push (task, *args)

	def refresh (self):
		self.oXLIA.oApp.master.update()

	def close (self):
		oApp = self.oXLIA.oApp
		oApp.close()
		oApp.master.after_cancel (self._hApplet)
		oApp.master.destroy()

	# +++++++++++++ Update display functions +++++++++++++++

	def setConnectionStatus (self, status):
		oApp  = self.oXLIA.oApp
		oApp.setConnectionStatus (status)

	def setReferenceParameters (self, ampl, freq, phase):

		oApp  = self.oXLIA.oApp
		oApp.setReferenceParameters (ampl, freq, phase)

		oXLIA = self.oXLIA
		oXLIA.referenceParameters.set (ampl, freq, phase)

	def setMeasurementSettings (self,
								inputChannel   = None,
								preAmpCoupling = None,
								preAmpGain     = None,
								postAmpGain    = None,
								intgtrTC       = None):

		oXLIA = self.oXLIA
		oXLIA.measurementSettings.set (
			inputChannel, preAmpCoupling,
			preAmpGain, postAmpGain, intgtrTC)

		oApp  = self.oXLIA.oApp
		oApp.setMeasurementSettings (*oXLIA.measurementSettings.get())

	def setReadoutDisplay (
		self, ampl, phase, inphase,
		quad, preAmpGain, postAmpGain):

		oApp  = self.oXLIA.oApp
		oApp.setReadoutDisplay (
			ampl, phase, inphase, quad, preAmpGain, postAmpGain)

	def set_status (self, text):
		self.oXLIA.oApp.set_status (text)

	def setRunMode (self, mode):
		self.oXLIA.oApp.setRunMode (mode)
		self.oXLIA.runMode = mode

	def setAcquisitionSettings (
		self, delay, filterLength, driveMode,
		driveCurrentSetPoint, driveVoltageSetPoint):

		self.oXLIA.oApp.setAcquisitionSettings (
			delay, filterLength, driveMode,
			driveCurrentSetPoint, driveVoltageSetPoint)

		self.oXLIA.acquisitionSettings.set (
			delay, filterLength, driveMode,
			driveCurrentSetPoint, driveVoltageSetPoint)

	def setVFRampSettings (
		self, initialFrequency, finalFrequency,
		linearFreqStep, logFreqStep, frequencySteppingMode):

		self.oXLIA.oApp.setVFRampSettings (
			initialFrequency, finalFrequency,
			linearFreqStep, logFreqStep, frequencySteppingMode)

		self.oXLIA.oVFRampSettings.set (
			initialFrequency, finalFrequency,
			linearFreqStep, logFreqStep, frequencySteppingMode)

	def setRunControlStatus (self, status):
		self.oXLIA.oApp.setRunControlStatus (status)

	def initPlot (self, thread, title, xlabel, ylabel):
		oApp = self.oXLIA.oApp
		wPlot = oApp.newPlot (title)
		wPlot.xlabel (xlabel)
		wPlot.ylabel (ylabel)
		traceID = wPlot.new_dataset ('k-')
		wPlot.damage()
		self._plots[thread] = (wPlot, traceID)

	# 'linear' or 'log'
	def setPlotScale (self, thread, xscale, yscale):
		if thread in self._plots:
			(wPlot, traceID) = self._plots[thread]
			wPlot.xscale (xscale)
			wPlot.yscale (yscale)
			wPlot.damage()

	def updatePlot (self, thread, x, y):
		if thread in self._plots:
			(wPlot, traceID) = self._plots[thread]
			wPlot.add_datapoint (traceID, x, y)
			wPlot.damage()

	def clearPlot (self):
		oApp = self.oXLIA.oApp
		oApp.clearPlot()
		self._plots.clear()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquisition_atexit (self):
		self.oXLIA.releaseAcquisition()

	def devicethread_atexit (self):
		self.oXLIA.releaseDeviceThread();

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''

class _DeviceThread (XThread):

	def __init__ (self, oXLIA):

		XThread.__init__ (self, daemon = True)

		self.oXLIA = oXLIA
		self.oXLIA.oDriver.callback (self.driverCB)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def thread (self):

		oXLIA      = self.oXLIA
		oApplet = oXLIA.oApplet
		lastPollAt = 0.0

		while True:

			try:

				while True:

					self.do_tasks()

					t = systime()
					if t >= lastPollAt + 2:

						lastPollAt = t
						self.acquire_n_show()

					else: sleep (0.05)

			except (LinkError, CommError) : pass
			except XTerminate: break

		self.disconnectDevice()

	def acquire_n_show (self):

		oDriver = self.oXLIA.oDriver
		oApplet = self.oXLIA.oApplet

		try:
			oDriver.acquire_lock()
			(outIP, outQP, amplitude, phase) = (
				oDriver.doQuickMeasurement (filterLength = 1))

			preAmpGain  = oDriver.measurementSettings.preAmpGain
			postAmpGain = oDriver.measurementSettings.postAmpGain

		finally:
			oDriver.release_lock()

		oApplet.schedule_task (
			oApplet.setReadoutDisplay,
			amplitude, phase, outIP, outQP, preAmpGain, postAmpGain)

		return (outIP, outQP, amplitude, phase)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def driverCB (self, context, *args):

		oApplet = self.oXLIA.oApplet

		if   context == DEVICE_CONNECTED:
			oApplet.schedule_task (
				oApplet.setConnectionStatus, DEVICE_CONNECTED)

		elif context == DEVICE_DISCONNECTED:
			oApplet.schedule_task (
				oApplet.setConnectionStatus, DEVICE_DISCONNECTED)

		elif context == DEVICE_NOT_FOUND:
			oApplet.schedule_task (
				oApplet.setConnectionStatus, DEVICE_NOT_FOUND)

		elif context == REFERENCE_PARAMETER:
			oApplet.schedule_task (oApplet.setReferenceParameters, *args)

		elif context == MEASUREMENT_SETTINGS:
			oApplet.schedule_task (oApplet.setMeasurementSettings, *args)

		else: raise ValueError (context)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def connectDevice (
		self, refAmpl, refFreq, refPhase,
		inputChannel, preAmpCoupling, preAmpGain, postAmpGain, intgtrTC):

		oDriver = self.oXLIA.oDriver
		oApplet = self.oXLIA.oApplet

		oApplet.schedule_task (
			oApplet.setConnectionStatus, DEVICE_CONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.open (get_XLIA_serialNo())
			oDriver.initialize (
				refAmpl, refFreq, refPhase,
				inputChannel, preAmpCoupling,
				preAmpGain, postAmpGain, intgtrTC)

		finally:
			oDriver.release_lock()

	def disconnectDevice (self):

		oDriver = self.oXLIA.oDriver
		oApplet = self.oXLIA.oApplet

		oApplet.schedule_task (
			oApplet.setConnectionStatus, DEVICE_DISCONNECTING)

		try:
			oDriver.acquire_lock()
			oDriver.close()

		finally:
			oDriver.release_lock()

	def setReferenceParameters (self, ampl, freq, phase):

		oDriver = self.oXLIA.oDriver
		oApplet = self.oXLIA.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.setReferenceParameters (ampl, freq, phase)

		except CommError:
			text = 'Communication error'
			oApplet.schedule_task (oApplet.set_status, text)

		finally:
			oDriver.release_lock()

	def setMeasurementSettings (self,
								inputChannel   = None,
								preAmpCoupling = None,
								preAmpGain     = None,
								postAmpGain    = None,
								intgtrTC       = None):

		oDriver = self.oXLIA.oDriver
		oApplet = self.oXLIA.oApplet

		try:
			oDriver.acquire_lock()
			oDriver.setMeasurementSettings (
				inputChannel, preAmpCoupling,
				preAmpGain, postAmpGain, intgtrTC)

		except CommError:
			text = 'Communication error'
			oApplet.schedule_task (oApplet.set_status, text)

		finally:
			oDriver.release_lock()

'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''

def XLIA (master, sample):

	if XLIA.singleton == None:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()

		oApp           = GUI (win, sample)
		XLIA.singleton = _XLIA (oApp, sample)

	if master not in XLIA.master:
		XLIA.master.append (master)

	return XLIA.singleton

def closeXLIA (master):

	if master in XLIA.master:
		XLIA.master.remove (master)

	if len (XLIA.master) == 0 and XLIA.singleton:
		XLIA.singleton.close()
		XLIA.singleton = None

XLIA.singleton = None
XLIA.master    = []

class AcquisitionSettings:

	def __init__ (self):
		self.delay                = 1.0
		self.filterLength         = 16
		self.driveMode            = DRIVE_MODE_CS
		self.driveCurrentSetPoint = 25e-3
		self.driveVoltageSetPoint = MAX_DRIVE_VOLTAGE

	def set (
		self, delay, filterLength, driveMode,
		driveCurrentSetPoint, driveVoltageSetPoint):

		self.delay                = delay
		self.filterLength         = filterLength
		self.driveMode            = driveMode
		self.driveCurrentSetPoint = driveCurrentSetPoint
		self.driveVoltageSetPoint = driveVoltageSetPoint

	def get (self):
		return (
			self.delay,
			self.filterLength,
			self.driveMode,
			self.driveCurrentSetPoint,
			self.driveVoltageSetPoint)

class VFRampSettings:

	def __init__ (self):
		self.initialFrequency = 10.0
		self.finalFrequency   = 10000.0
		self.linearFreqStep   = 10.0

		'''
		10 data points per decade is a good choice while doing logarithmic
		frequency stepping. In log scale, this stepping translates to an
		interval of 0.1. Thus if a point is at 10^x,
		then the next point would be at 10^(x+0.1). Thus the ratio
		of two successive frequencies is 10^(x+0.1) / 10^x = 10^0.1
		'''
		self.logFreqStep      = 10.0 ** 0.1
		self.frequencySteppingMode = VF_FREQ_STEP_MODE_LOG

	def set (self, initialFrequency, finalFrequency,
		  linearFreqStep, logFreqStep, frequencySteppingMode):

		self.initialFrequency = initialFrequency
		self.finalFrequency   = finalFrequency
		self.linearFreqStep   = linearFreqStep
		self.logFreqStep      = logFreqStep
		self.frequencySteppingMode = frequencySteppingMode

	def get (self):
		return (
			self.initialFrequency,
			self.finalFrequency,
			self.linearFreqStep,
			self.logFreqStep,
			self.frequencySteppingMode)

class _XLIA:

	def __init__ (self, oApp, sample):

		self.oApp    = oApp
		self.sample  = sample
		self.oDriver = Driver()
		self.t0      = None

		# ++++ Device parameters ++++

		self.referenceParameters = _ReferenceParameters()
		self.referenceParameters.set (
			amplitude = 1.0, frequency = 180.0, phase = 0.0)

		self.measurementSettings = _MeasurementSettings()
		self.measurementSettings.set (
			inputChannel   = INPUT_CHANNEL_INPUT_VOLTAGE,
			preAmpCoupling = PREAMP_COUPLING_DC,
			preAmpGain     = PREAMP_GAIN_10,
			postAmpGain    = POSTAMP_GAIN_10,
			intgtrTC       = INTGTR_TC_1sec)

		self.acquisitionSettings = AcquisitionSettings()
		self.oVFRampSettings     = VFRampSettings     ()
		self.runMode             = RUN_MODE_VTime

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

		# ++++ Finalize ++++

		self.oApp.callback (self.oAppCB)

		oApplet = self.oApplet
		oApplet.schedule_task (
			oApplet.setAcquisitionSettings, *self.acquisitionSettings.get())

		oApplet.schedule_task (
			oApplet.setVFRampSettings, *self.oVFRampSettings.get())

		oApplet.schedule_task (oApplet.setRunMode, self.runMode)
		self.connectDevice()

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	# ++++ Device connection functions ++++

	def connectDevice (self):

		oApplet = self.oApplet
		oApplet.schedule_task (
			oApplet.setConnectionStatus, DEVICE_CONNECTING)

		oDeviceThread = self.oDeviceThread
		oDeviceThread.schedule_task (
			oDeviceThread.connectDevice, *(
				self.referenceParameters.get() +
				self.measurementSettings.get()))

	def disconnectDevice (self):

		oApplet = self.oApplet
		oApplet.schedule_task (
			oApplet.setConnectionStatus, DEVICE_DISCONNECTING)

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
				'XLIA_ResourceError: Device thread unavailable')

		return thread

	def releaseDeviceThread (self):
		self.oDeviceThread = None

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def oAppCB (self, context, *args):

		oApplet = self.oApplet

		if context == CONNECT_DEVICE      : self.connectDevice    ()
		elif context == DISCONNECT_DEVICE : self.disconnectDevice ()
		elif context == OPEN_DIALOG       : self.openDialog       (*args)

		elif context == RUN_MODE          :
			oApplet.schedule_task (oApplet.setRunMode, *args)

		elif context == START_RUN         : self.startRun         (*args)
		elif context == FINISH_RUN        : self.finishRun        ()
		elif context == OPEN_METHOD       : self.openMethod       (*args)
		elif context == SAVE_METHOD       : self.saveMethod       (*args)
		else                              : raise ValueError      (context)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareModule (self, master, mode):

		module = None
		oXLIA  = self

		if self.oModule == None:

			if mode == RUN_MODE_VTime:
				module = _VTimeModule (master, oXLIA)
				module.initAcquisitionSettings (*self.acquisitionSettings.get())

			elif mode == RUN_MODE_VF:
				module = _VF_Module (master, oXLIA)
				module.initAcquisitionSettings (*self.acquisitionSettings.get())
				module.setRampSettings (*self.oVFRampSettings.get())

			else:
				raise ResourceError (
					'XLIA_ResourceError: Module creation failed')

			self.oModule = module

		else:
			raise ResourceError (
				'XLIA_ResourceError: Module unavailable')

		return module

	def releaseModule (self, caller):
		if self.oModule and caller == self.oModule.master:
			self.oModule = None

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def prepareAcquisition (self, mode):

		thread = None
		master = self

		try:

			if self.oAcqThread == None:

				module = self.prepareModule (master, mode)

				if mode == RUN_MODE_VTime:
					thread =  _VTimeAcquisitionThread (module)

				elif mode == RUN_MODE_VF:
					thread =  _VF_AcquisitionThread (module)

				else:
					raise ResourceError (
						'XLIA_ResourceError: Thread creation failed')

				thread.atexit (self.acquisition_atexit)
				self.oAcqThread = thread

			else:
				raise ResourceError (
					'XLIA_ResourceError: Thread unavailable')

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

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openDialog (self, dialog):

		if dialog == REFERENCE_PARAMETER_DIALOG:
			self.openReferenceSettingsDialog()

		elif dialog == MEASUREMENT_SETTINGS_DIALOG:
			self.openMeasurementSettingsDialog()

		elif dialog == ACQUISITION_SETTINGS_DIALOG:
			self.openAcquisitionSettingsDialog()

		elif dialog == VF_RAMP_SETTINGS_DIALOG:
			self.open_VF_RampSettingsDialog()

		else: raise ValueError (dialog)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openReferenceSettingsDialog (self):

		w = self.wDialog = GUI_ReferenceSettings (Toplevel())
		w.set (*self.referenceParameters.get())
		w.callback (self.referenceSettingsDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def referenceSettingsDialogCB (self, context, *args):

		oDeviceThread = self.oDeviceThread

		if context == APPLY:
			self.wDialog.master.destroy()
			self.wDialog = None

		elif context == CANCEL:
			self.referenceParameters.set (*args)
			oDeviceThread.schedule_task (
				oDeviceThread.setReferenceParameters, *args)

			self.wDialog.master.destroy()
			self.wDialog = None

		elif context == REFERENCE_PARAMETER:
			self.referenceParameters.set (*args)
			oDeviceThread.schedule_task (
				oDeviceThread.setReferenceParameters, *args)

		else: raise ValueError (context)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openMeasurementSettingsDialog (self):

		w = self.wDialog = GUI_MeasurementSettings (Toplevel())
		w.set (*self.measurementSettings.get())
		w.callback (self.measurementSettingsDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

	# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def measurementSettingsDialogCB (self, context, *args):

		oDeviceThread = self.oDeviceThread

		if context == APPLY:
			self.wDialog.master.destroy()
			self.wDialog = None

		elif context == CANCEL:

			self.measurementSettings.set (*args)
			oDeviceThread.schedule_task (
				oDeviceThread.setMeasurementSettings, *args)

			self.wDialog.master.destroy()
			self.wDialog = None

		elif context == MEASUREMENT_SETTINGS:
			self.measurementSettings.set (*args)
			oDeviceThread.schedule_task (
				oDeviceThread.setMeasurementSettings, *args)

		else: raise ValueError (context)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def openAcquisitionSettingsDialog (self):

		w = self.wDialog = GUI_AcquisitionSettings (Toplevel())
		w.set (*self.acquisitionSettings.get())
		w.callback (self.acquisitionSettingsDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def acquisitionSettingsDialogCB (self, context, *args):

		oApplet    = self.oApplet
		oModule    = self.oModule

		if context == APPLY:

			self.acquisitionSettings.set (*args)
			oApplet.schedule_task (oApplet.setAcquisitionSettings, *args)

			if oModule:
				oModule.schedule_task (
					oModule.setAcquisitionSettings, *args)

			self.wDialog.master.destroy()
			self.wDialog = None

		elif context == CANCEL:

			self.wDialog.master.destroy()
			self.wDialog = None

		else: raise ValueError (context)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def open_VF_RampSettingsDialog (self):

		w = self.wDialog = GUI_VFRampSettings (Toplevel())
		w.set (*self.oVFRampSettings.get())
		w.callback (self.VF_RampSettingsDialogCB)

		# Makes it modal
		parent = self.oApp.master.focus_displayof().winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def VF_RampSettingsDialogCB (self, context, *args):

		oApplet    = self.oApplet
		oModule    = self.oModule

		if context == APPLY:

			oApplet = self.oApplet
			oApplet.schedule_task (oApplet.setVFRampSettings, *args)

			if oModule and isinstance (oModule, _VF_Module):
				oModule.schedule_task (oModule.setRampSettings, *args)

			self.wDialog.master.destroy()
			self.wDialog = None

		elif context == CANCEL:

			self.wDialog.master.destroy()
			self.wDialog = None

		else: raise ValueError (context)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	def getMethod (self):
		method = Method()
		method.setRunMode (self.runMode)
		method.setReferenceParameters (*self.referenceParameters.get())
		method.setMeasurementSettings (*self.measurementSettings.get())
		method.setAcquisitionSettings (*self.acquisitionSettings.get())
		method.set_VF_RampSettings (*self.oVFRampSettings.get())
		return method

	def applyMethod (self, method):

		oApplet       = self.oApplet
		oDeviceThread = self.oDeviceThread
		oModule    = self.oModule

		# +++++++++++++++++++++++++++++++++++++++++++

		mode = method.getRunMode (self.runMode)
		oApplet.schedule_task (oApplet.setRunMode, mode)

		# +++++++++++++++++++++++++++++++++++++++++++

		self.referenceParameters.set (
			*method.getReferenceParameters (
				*self.referenceParameters.get()))

		oDeviceThread.schedule_task (
			oDeviceThread.setReferenceParameters,
			*self.referenceParameters.get())

		# +++++++++++++++++++++++++++++++++++++++++++

		self.measurementSettings.set (
			*method.getMeasurementSettings (
				*self.measurementSettings.get()))

		oDeviceThread.schedule_task (
			oDeviceThread.setMeasurementSettings,
			*self.measurementSettings.get())

		# +++++++++++++++++++++++++++++++++++++++++++

		settings = (
			method.getAcquisitionSettings (
				*self.acquisitionSettings.get()))

		oApplet.schedule_task (oApplet.setAcquisitionSettings, *settings)

		if oModule:
			oModule.schedule_task (
				oModule.setAcquisitionSettings, *settings)

		# +++++++++++++++++++++++++++++++++++++++++++

		settings = (
			method.get_VF_RampSettings (
				*self.oVFRampSettings.get()))

		oApplet.schedule_task (oApplet.setVFRampSettings, *settings)

		if oModule and isinstance (oModule, _VF_Module):
			oModule.schedule_task (
				oModule.setRampSettings, *settings)

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _RangeSettings:

	def __init__ (self):

		self._CMFS_preAmpGain = None
		self._CMFS_postAmpGain = None

		self._CM_preAmpGain = None
		self._CM_postAmpGain = None

		self._VM_preAmpGain = None
		self._VM_postAmpGain = None

	def CMFS_gain (self):
		return (self._CMFS_preAmpGain, self._CMFS_postAmpGain)

	def CM_gain (self):
		return (self._CM_preAmpGain, self._CM_postAmpGain)

	def VM_gain (self):
		return (self._VM_preAmpGain, self._VM_postAmpGain)

	def set_CMFS_gain (self, preAmpGain, postAmpGain):
		self._CMFS_preAmpGain  = preAmpGain
		self._CMFS_postAmpGain = postAmpGain

	def set_CM_gain (self, preAmpGain, postAmpGain):
		self._CM_preAmpGain  = preAmpGain
		self._CM_postAmpGain = postAmpGain

	def set_VM_gain (self, preAmpGain, postAmpGain):
		self._VM_preAmpGain  = preAmpGain
		self._VM_postAmpGain = postAmpGain

	def reset (self):
		self._CMFS_preAmpGain = None
		self._CMFS_postAmpGain = None

		self._CM_preAmpGain = None
		self._CM_postAmpGain = None

		self._VM_preAmpGain = None
		self._VM_postAmpGain = None

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Module (XThreadModule):

	def __init__ (self, master, oXLIA):
		XThreadModule.__init__ (self, master)
		self.oXLIA   = oXLIA
		self.t0      = systime()
		self.dataset = DataSet()
		self.fd_log  = None
		self._rangeSettings = _RangeSettings()
		self._alive  = False

	def sleep (self, duration, bg_task = None, *bg_tasks):
		entry = systime()
		self.do_tasks (bg_task, *bg_tasks)
		while systime() < entry + duration:
			sleep (0.05)
			self.do_tasks (bg_task, *bg_tasks)

	def initAcquisitionSettings (
		self, delay, filterLength,
		driveMode, driveCurrent, driveVoltage):

		self.delay        = delay
		self.filterLength = filterLength

		self.driveMode = driveMode
		self.driveCurrentSetPoint = driveCurrent
		self.driveVoltageSetPoint = driveVoltage

	def setAcquisitionSettings (
		self, delay, filterLength,
		driveMode, driveCurrent, driveVoltage):

		self.initAcquisitionSettings (
			delay, filterLength,
			driveMode, driveCurrent, driveVoltage)

		oApplet = self.oXLIA.oApplet
		text = 'Acquisition settings updated'
		oApplet.schedule_task (oApplet.set_status, text)

	# ++++ Useful functions used by derived classes ++++

	'''
		Redefine these in the derived class
		to set run-type specific folder name and extension.
	'''

	def folder_name (self):
		return 'xlia'

	def run_type (self):
		return ''

	def xlabel (self):
		return ''

	def ylabel (self):
		return ''

	def is_alive (self):
		return True if self._alive else False

	# ++++ init and exit functions ++++

	def init (self):

		oXLIA       = self.oXLIA
		oApplet     = oXLIA.oApplet
		self._alive = True

		try:
			self.filename = self.get_timestamp()
			oApplet.schedule_task (oApplet.setRunControlStatus, RUN_STARTING)

			self.t0             = systime()
			self.dataset        = DataSet()
			self._rangeSettings = _RangeSettings()

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

		oXLIA   = self.oXLIA
		oApplet = oXLIA.oApplet
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
		self._alive = False

	# ++++ Logging functions ++++

	def open_log (self):

		(self.fd_log, full_path) = self.open_file (
			self.filename + '_' + self.run_type(), 'csv', 'w')

		fields = [
			('Time',                 'sec'),
			('Reference frequency',   'Hz'),
			('Reference amplitude', 'Volt'),
			('Reference phase',      'Rad'),
			('Current amplitude',      'A'),
			('Current phase',        'Rad'),
			('Signal amplitude',       'V'),
			('Signal phase',         'Rad')
		]

		(sampleName, sampleID, sampleDescription) = self.oXLIA.sample.get()
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

			('Reference amplitude',
				'%-.3f', datapoint.refAmplitude,
				1.0, 'V'),

			('Reference phase',
				'%-.1f', datapoint.refPhase,
				rad_to_deg, 'Deg'),

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
				rad_to_deg, 'Deg')
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
		dict.set_sample (self.oXLIA.sample.get())

		fields = [
			('01 Time',                DATASET_COL_TIME,          'sec'),
			('02 Reference frequency', DATASET_COL_REF_FREQ,       'Hz'),
			('03 Reference amplitude', DATASET_COL_REF_AMPL,     'Volt'),
			('04 Reference phase',     DATASET_COL_REF_PHASE,     'Rad'),
			('05 Current amplitude',   DATASET_COL_CURRENT_AMPL,    'A'),
			('06 Current phase',       DATASET_COL_CURRENT_PHASE, 'Rad'),
			('07 Signal amplitude',    DATASET_COL_SIGNAL_AMPL,     'V'),
			('08 Signal phase',        DATASET_COL_SIGNAL_PHASE,  'Rad')
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

		(sampleName, sampleID, _) = self.oXLIA.sample.get()

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

	# ++++ Acquisition functions ++++

	def acquire_current (self, mode, bg_task = None, *bg_tasks):

		oXLIA   = self.oXLIA
		oDriver = oXLIA.oDriver

		doMeasurement = {
					MEASUREMENT_MODE_QUICK : oDriver.doQuickMeasurement,
					MEASUREMENT_MODE_FULL  : oDriver.doMeasurement
			}.get (mode)

		try:

			oDriver.acquire_lock()

			oDriver.setMeasurementSettings (
				inputChannel = INPUT_CHANNEL_REFERENCE_CURRENT)

			(preAmpGain, postAmpGain) = self._rangeSettings.CM_gain()
			if all (gain != None for gain in (preAmpGain, postAmpGain)):
				oDriver.setMeasurementSettings (
					preAmpGain = preAmpGain, postAmpGain = postAmpGain)

			self.sleep (1.0, bg_task, *bg_tasks)

			(preAmpGain, postAmpGain) = oDriver.doAutoRange()
			self._rangeSettings.set_CM_gain (preAmpGain, postAmpGain)

			self.sleep (self.delay, bg_task, *bg_tasks)

			(_, _, amplitude, phase) = (
				doMeasurement (self.filterLength))

			amplitude = amplitude / get_XLIA_currentSenseResistance()
			(refAmpl, refFreq, refPhase) = oDriver.referenceParameters.get()

		finally:
			oDriver.release_lock()

		return DataPoint (
			systime() - self.t0,
			refAmpl, refFreq, refPhase,
			amplitude, phase, 0.0, 0.0)

	def acquire_signal (self, mode, bg_task = None, *bg_tasks):

		oXLIA   = self.oXLIA
		oDriver = oXLIA.oDriver

		doMeasurement = {
			MEASUREMENT_MODE_QUICK : oDriver.doQuickMeasurement,
			MEASUREMENT_MODE_FULL  : oDriver.doMeasurement
		}.get (mode)

		try:

			oDriver.acquire_lock()

			oDriver.setMeasurementSettings (
				inputChannel = INPUT_CHANNEL_INPUT_VOLTAGE)

			(preAmpGain, postAmpGain) = self._rangeSettings.VM_gain()
			if all (gain != None for gain in (preAmpGain, postAmpGain)):
				oDriver.setMeasurementSettings (
					preAmpGain = preAmpGain, postAmpGain = postAmpGain)

			self.sleep (1.0, bg_task, *bg_tasks)

			(preAmpGain, postAmpGain) = oDriver.doAutoRange()
			self._rangeSettings.set_VM_gain (preAmpGain, postAmpGain)

			self.sleep (self.delay, bg_task, *bg_tasks)

			(_, _, amplitude, phase) = (
				doMeasurement (self.filterLength))

			(refAmpl, refFreq, refPhase) = oDriver.referenceParameters.get()

		finally:
			oDriver.release_lock()

		return DataPoint (
			systime() - self.t0,
			refAmpl, refFreq, refPhase,
			0.0, 0.0, amplitude, phase)

	def acquire_datapoint (self, mode, bg_task = None, *bg_tasks):

		oXLIA   = self.oXLIA
		oDriver = oXLIA.oDriver

		try:
			oDriver.acquire_lock()

			current_datapoint = \
				self.acquire_current (mode, bg_task, *bg_tasks)

			signal_datapoint = \
				self.acquire_signal (mode, bg_task, *bg_tasks)

			(refAmpl, refFreq, refPhase) = oDriver.referenceParameters.get()

		finally:
			oDriver.release_lock()

		return DataPoint (
			systime() - self.t0,
			refAmpl, refFreq, refPhase,
			current_datapoint.currentAmplitude, current_datapoint.currentPhase,
			signal_datapoint.signalAmplitude, signal_datapoint.signalPhase)

	def doDriveRegulation (self, mode, bg_task = None, *bg_tasks):

		if self.driveMode == DRIVE_MODE_CS:
			self.doCurrentRegulation (mode, bg_task, *bg_tasks)

		elif self.driveMode == DRIVE_MODE_VS:
			self.doVoltageRegulation (mode, bg_task, *bg_tasks)

		else: pass

	def doCurrentRegulation (self, mode, bg_task = None, *bg_tasks):

		oXLIA   = self.oXLIA
		oDriver = oXLIA.oDriver

		doMeasurement = {
			MEASUREMENT_MODE_QUICK : oDriver.doQuickMeasurement,
			MEASUREMENT_MODE_FULL  : oDriver.doMeasurement
		}.get (mode)

		try:
			oDriver.acquire_lock()

			(amplitude, frequency, phase) = oDriver.referenceParameters.get()
			oDriver.setReferenceParameters (MAX_DRIVE_VOLTAGE, frequency, phase)

			oDriver.setMeasurementSettings (
				inputChannel = INPUT_CHANNEL_REFERENCE_CURRENT)

			(preAmpGain, postAmpGain) = self._rangeSettings.CMFS_gain()
			if all (gain != None for gain in (preAmpGain, postAmpGain)):
				oDriver.setMeasurementSettings (
					preAmpGain = preAmpGain, postAmpGain = postAmpGain)

			(preAmpGain, postAmpGain) = oDriver.doAutoRange()
			self._rangeSettings.set_CMFS_gain (preAmpGain, postAmpGain)

			self.sleep (self.delay, bg_task, *bg_tasks)

			(_, _, currentAmplitude, currentPhase) = (
							doMeasurement (filterLength = 1))

			currentAmplitude = (
				currentAmplitude / get_XLIA_currentSenseResistance())

			try:
				driveAmplitude = MAX_DRIVE_VOLTAGE * (
					self.driveCurrentSetPoint / currentAmplitude)

			except ZeroDivisionError:
				driveAmplitude = float ('inf')

			driveAmplitude = min (driveAmplitude, MAX_DRIVE_VOLTAGE)
			(amplitude, frequency, phase) = oDriver.referenceParameters.get()
			oDriver.setReferenceParameters (driveAmplitude, frequency, phase)

		finally:
			oDriver.release_lock()

	def doVoltageRegulation (self, mode, bg_task = None, *bg_tasks):

		oXLIA   = self.oXLIA
		oDriver = oXLIA.oDriver

		try:
			oDriver.acquire_lock()

			(amplitude, frequency, phase) = oDriver.referenceParameters.get()

			oDriver.setReferenceParameters (
				self.driveVoltageSetPoint, frequency, phase)

			self.sleep (0.0, bg_task, *bg_tasks)

		finally:
			oDriver.release_lock()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _AcquisitionThread (XThread):

	def __init__ (self, module):
		XThread.__init__ (self, daemon = True)
		self.module = module

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _VTimeModule (_Module):

	def __init__ (self, master, oXLIA):
		_Module.__init__(self, master, oXLIA)

	def run_type (self):
		return 'V_Time'

	def xlabel (self):
		return 'Time (sec)'

	def ylabel (self):
		return 'Voltage'

	def init (self):
		_Module.init (self)

		oXLIA   = self.oXLIA
		oApplet = oXLIA.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_VTime)

	def acquire_n_plot (self, mode, bg_task = None, *bg_tasks):

		oXLIA   = self.oXLIA
		oApplet = oXLIA.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			self.doDriveRegulation (
				mode, self.do_tasks, bg_task, *bg_tasks)

			datapoint = self.acquire_datapoint (
				mode, self.do_tasks, bg_task, *bg_tasks)

			self.update_log (datapoint)
			self.dataset.append (datapoint)

			oApplet.schedule_task (
				oApplet.updatePlot, self, datapoint.time,
				datapoint.signalAmplitude)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _VTimeAcquisitionThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:

			self.module.init()

			while True:
				self.do_tasks()
				self.module.acquire_n_plot (
					MEASUREMENT_MODE_QUICK, self.do_tasks)

		except (CommError, LinkError) : pass
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _VF_Module (_Module):

	def __init__ (self, master, oXLIA):
		_Module.__init__(self, master, oXLIA)
		self.frequency = None

	def run_type (self):
		return 'VF'

	def xlabel (self):
		return 'Frequency (Hz)'

	def ylabel (self):
		return 'Voltage (Volt)'

	def setRampSettings (
		self, initialFrequency, finalFrequency,
		linearFreqStep, logFreqStep, frequencySteppingMode):

		self.initialFrequency      = initialFrequency
		self.finalFrequency        = finalFrequency
		self.linearFreqStep        = linearFreqStep
		self.logFreqStep           = logFreqStep
		self.frequencySteppingMode = frequencySteppingMode

	def init (self):
		_Module.init (self)

		oXLIA   = self.oXLIA
		oApplet = oXLIA.oApplet
		oApplet.schedule_task (oApplet.setRunMode, RUN_MODE_VF)

		if self.frequencySteppingMode == VF_FREQ_STEP_MODE_LINEAR:
			oApplet.schedule_task (
				oApplet.setPlotScale, self, 'linear', 'linear')

		elif self.frequencySteppingMode == VF_FREQ_STEP_MODE_LOG:
			oApplet.schedule_task (
				oApplet.setPlotScale, self, 'log', 'linear')

		self.frequency = None

	def applyNextFrequency (self):

		oDriver = self.oXLIA.oDriver

		if self.frequency == None:
			self.frequency = self.initialFrequency

		elif self.frequencySteppingMode == VF_FREQ_STEP_MODE_LINEAR:
			self.frequency += self.linearFreqStep
			self.frequency = (self.linearFreqStep *
					round (self.frequency / self.linearFreqStep))

		elif self.frequencySteppingMode == VF_FREQ_STEP_MODE_LOG:
			logF  = log10 (self.frequency)
			logdF = log10 (self.logFreqStep)
			logF  = logdF * round ((logF + logdF) / logdF)
			self.frequency = 10 ** logF

		if not self.complete():

			try:
				oDriver.acquire_lock()

				(amplitude, frequency, phase) = \
					oDriver.referenceParameters.get()

				oDriver.setReferenceParameters (
					amplitude, self.frequency, phase)

			finally:
				oDriver.release_lock()

	def complete (self):
		return True if (
			round (self.frequency) > self.finalFrequency) else False

	def acquire_n_plot (self, mode, bg_task = None, *bg_tasks):

		oXLIA   = self.oXLIA
		oApplet = oXLIA.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			self.doDriveRegulation (
				mode, self.do_tasks, bg_task, *bg_tasks)

			datapoint = self.acquire_datapoint (
				mode, self.do_tasks, bg_task, *bg_tasks)

			self.update_log (datapoint)
			self.dataset.append (datapoint)

			oApplet.schedule_task (
				oApplet.updatePlot, self, datapoint.refFrequency,
				datapoint.signalAmplitude)

		except (CommError, LinkError) as e:
			oApplet.schedule_task (oApplet.set_status, str (e))
			raise

		except (IOError, OSError) as e:
			text = e.strerror + ' on ' + e.filename
			oApplet.schedule_task (oApplet.set_status, text)
			raise

		return datapoint

	def excite_n_plot (self, mode, bg_task = None, *bg_tasks):

		oXLIA   = self.oXLIA
		oApplet = oXLIA.oApplet
		self.do_tasks (bg_task, *bg_tasks)

		try:

			self.applyNextFrequency()

			if not self.complete():

				self.doDriveRegulation (
					mode, self.do_tasks, bg_task, *bg_tasks)

				datapoint = self.acquire_datapoint (
					mode, self.do_tasks, bg_task, *bg_tasks)

				self.update_log (datapoint)
				self.dataset.append (datapoint)

				oApplet.schedule_task (
					oApplet.updatePlot, self, datapoint.refFrequency,
					datapoint.signalAmplitude)

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

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _VF_AcquisitionThread (_AcquisitionThread):

	def __init__ (self, module):
		_AcquisitionThread.__init__ (self, module)

	def thread (self):

		try:

			self.module.init()

			while True:
				self.do_tasks()
				self.module.excite_n_plot (
					MEASUREMENT_MODE_QUICK, self.do_tasks)

				if self.module.complete():
					break

		except (CommError, LinkError) : pass
		except (IOError, OSError)     : pass
		except XTerminate             : pass

		self.module.atexit()

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

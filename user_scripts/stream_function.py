import sys, time
import libxsmu
import libxtcon
import csv
import numpy as np


logfile = open ('log.txt', 'w')
logfile.close ()

def set_VM_range (SMU_deviceID):
	timeout = 15.0
	voltageMeterRange = 3 # 0: 1mV, 1: 10mV, 2: 100mV, 3: 1V, 4: 10V, 5: 100V
	voltageMeterRange, timeout = \
	libxsmu.VM_setRange (SMU_deviceID, voltageMeterRange, timeout)
	print \
	"voltageMeterRange    :", voltageMeterRange, "\n" \
	"Remaining time        :", timeout, "sec", "\n"

	if (timeout == 0.0):
		print 'Communication timeout in VM_setRange.'
		exit (-2)

	for index in range (0, 5):
		timeout = 1.0
		i, adc, voltage, timeout = \
		libxsmu.VM_getCalibration (SMU_deviceID, index, timeout)

		print i, adc, voltage, timeout

		if (timeout == 0.0):
			print 'Communication timeout in VM_getCalibration'
			exit (-2)

		print


def set_DC_voltage (SMU_deviceID, value):
    
    ############################
    # Set VS range

    timeout = 1.0
    voltageSourceRange = 0 # 0: 10V, 1: 100V

    print \
    "voltageSourceRange    :", voltageSourceRange, "\n" \
    "Remaining time        :", timeout, "sec", "\n"

    voltageSourceRange, timeout = \
        libxsmu.VS_setRange (SMU_deviceID, voltageSourceRange, timeout)

    if (timeout == 0.0):
        print 'Communication timeout in VS_setRange.'
        exit (-2)
        
    ############################
    # Set VS voltage

    timeout = 1.0
    voltage = value
    voltage, timeout = libxsmu.VS_setVoltage (SMU_deviceID, voltage, timeout)
    print \
            "Voltage: ", voltage, "\n" \
            "Timeout: ", timeout

    if (timeout == 0.0):
        print 'Communication timeout in VS_setVoltage'
        exit (-2)

    ############################
    time.sleep(1)
    

def set_DC_current (SMU_deviceID, value):

    ############################
    # Set CS range

    currentSourceRange = 3 # 0: 10uA, 1: 100uA, 2: 1mA, 3: 10mA, 4: 100mA
    timeout = 1.0
    
    if (np.abs(value) < 0.0001):
        currentSourceRange = 1
        
    elif (np.abs(value) < 0.001):
        currentSourceRange = 2
        
    elif (np.abs(value) < 0.01):
        currentSourceRange = 3
        
    currentSourceRange, timeout = \
	libxsmu.CS_setRange (SMU_deviceID, currentSourceRange, timeout)
    
    print \
	"currentSourceRange    :", currentSourceRange, "\n" \
	"Remaining time        :", timeout, "sec", "\n"

    if (timeout == 0.0):
	print 'Communication timeout in CS_setRange.'
	exit (-2)

        
    ############################
    # Set CS current

    timeout = 1.0
    current = value
    current, timeout = libxsmu.CS_setCurrent (SMU_deviceID, current, timeout)
    
    print \
            "Current: ", current, "\n" \
            "Timeout: ", timeout

    if (timeout == 0.0):
        print 'Communication timeout in CS_setCurrent'
        exit (-2)

    ############################
    time.sleep(1)

def get_volt(SMU_deviceID, adc_value):
	
	corrected_adc_value = adc_value - 8388608
	
	HEADROOM = 1.02

	left    = 0
	right   = 4

	adc_unit        = []
	measured_voltage = []

	for index in range(0,5):
		timeout = 1.0
		i, adc, voltage, timeout = \
			libxsmu.VM_getCalibration (SMU_deviceID, index, timeout)
		
		adc_unit.append(adc)
		measured_voltage.append(voltage)

	
	if(corrected_adc_value < adc_unit[left]):
		right = left + 1;

		slope = (measured_voltage[right] - measured_voltage[left])/ \
				(adc_unit[right] - adc_unit[left])

		rv = measured_voltage[left] + (slope*(corrected_adc_value-adc_unit[left]))

		if(rv < HEADROOM*measured_voltage[left]):
			return HEADROOM*measured_voltage[left]
		else:
			return rv

	elif(corrected_adc_value > adc_unit[right]):
		left = right-1
		
		slope = (measured_voltage[right] - measured_voltage[left])/ \
				(adc_unit[right] - adc_unit[left])

		rv = measured_voltage[left] + (slope*(corrected_adc_value-adc_unit[left]))

		if(rv > HEADROOM*measured_voltage[right]):
			return HEADROOM*measured_voltage[right]
		else:
			return rv
			
	else:
		while True:
			middle = int((left + right) / 2)

			if(corrected_adc_value < adc_unit[middle]):
				right = middle

			elif(corrected_adc_value > adc_unit[middle]):
				left = middle

			else:
				return measured_voltage[middle]

			if((right-left) <= 1):
				break

		slope = (measured_voltage[right] - measured_voltage[left])/ \
				(adc_unit[right] - adc_unit[left])

		rv = measured_voltage[left] + (slope*(corrected_adc_value-adc_unit[left]))

		return rv


def measureV (SMU_deviceID, TCon_deviceID, sensorID, run_time):
##########################################################################
# Start recording streamed data from the XSMU
	timeout = 1.0
	i, adc, measured_voltage, timeout = \
		libxsmu.VM_getCalibration (SMU_deviceID, 4, timeout)
	
	timeout = 5

	timeout = libxsmu.StartRec (SMU_deviceID, timeout)
	print \
	      "Started Recording Streamed Data"

	time.sleep (5)

	##########################################################################
	# Get streamed data from data queue
	print \
		"Getting Data"

	logfile = open ('log.txt', 'w')

	t0 = time.time()
	_time_ = 0
	while (time.time() - t0 < run_time):
		print "Remaining time: ", 60 - (time.time() - t0) / 60.0, " minutes" 
		timeout = 5.0
		sensor, temperature, timeout = libxtcon.getSensorTemperature (TCon_deviceID, sensorID, timeout)
		recSize, timeout = libxsmu.recSize (SMU_deviceID, timeout)
		data = libxsmu.getData (SMU_deviceID)
		for adc_value in data:
			real_volt = get_volt(SMU_deviceID, adc_value)
			logfile.write (str (_time_) + ", " + str (real_volt) + "," + str (temperature) + '\n')
			print temperature, ',\t', _time_, ',\t', real_volt* 1e9, ' ADC'
			logfile.flush()
			_time_ = _time_ + 0.1
		time.sleep (10)

	timeout = 5
	timeout = libxsmu.StopRec (SMU_deviceID, timeout)
	print \
		"Stopped Recording Streamed Data"


def isothermal_start (TCon_deviceID, setpoint):
	runMode = 1 # 0:IDLE, 1:ISOTHERMAL, 2:LINEAR RAMP
	timeout = 1.0
	libxtcon.setIsothermal(TCon_deviceID, setpoint, timeout)
	print ("Isothermal is set on : ", str (setpoint)+ '\n')

	timeout = 1.0
	libxtcon.startRun(TCon_deviceID, runMode, timeout)
	print ("Starting Isothermal Run.. \n")


def isothermal_stop (TCon_deviceID, setpoint):
	timeout = 1.0
	libxtcon.stopRun(TCon_deviceID, timeout)
	raw_input ("Isothermal Finished. Press Enter to Exit\n")


def stabilize_temp (deviceID, sensorID, tolerance, monitoring_period):
    
	history = []
    
	print ("Stabilizing .. \n")
    
	while True :
		timeout = 5.0
		sensor, T, timeout = libxtcon.getSensorTemperature (deviceID, sensorID, timeout)
		history.append(T)

		if (len(history)<monitoring_period):
			continue
		else :
			fluctuation = max(history[-monitoring_period:-1]) - min(history[-monitoring_period:-1])
			print "Max : " + str (max(history[-monitoring_period:-1])) + "\tMin : " + str(min(history[-monitoring_period:-1]))

			if (np.abs(fluctuation) < tolerance):
				print ("Fluctuation : " + str(fluctuation))
				print ("Stable ..\n")
				break

    
def main():
	##########################################################################
    # User input parameters
    run_time          = int  (raw_input ("Enter Time For This Run (sec)     : "))
    setpoint          = float(raw_input ("Enter Setpoint (K)                : "))
    tolerance         = float(raw_input ("Tempereature Tolerance  (K)       : "))
    monitoring_period = int  (raw_input ("Enter the monitoring period (int) : "))

    ##########################################################################
    # Scans USB bus for Xplore SMU.

    N = libxsmu.scan()
    print "Total device:", N

    if N == 0:
        print 'No Xplore SMU device found.'
        exit (-1)

    ##########################################################################
    # Queries serial number of the first device.
    # This should be sufficient if only a single device is present.

    SMU_serialNo = 'XSMU012A'
    print "Serial number:", SMU_serialNo

    timeout = 1.0
    SMU_deviceID, SMU_goodID, timeout = libxsmu.open_device (SMU_serialNo, timeout)
    print \
        "Device ID     :", SMU_deviceID, "\n" \
        "SMU_goodID        :", SMU_goodID, "\n" \
        "Remaining time:", timeout, "sec", "\n"

    if (timeout == 0.0) or (not SMU_goodID):
        print 'Communication timeout in open_device.'
        exit (-2)

    
    ##########################################################################
    # Scans USB bus for Xplore TCon.

    N = libxtcon.scan()
    print "Total device:", N

    if N == 0:
        print 'No Xplore TCon device found.'
        exit (-1)

    ##########################################################################
    # Queries serial number of the first device.
    # This should be sufficient if only a single device is present.

    TCon_serialNo = 'XTCON012A'
    print "Serial number:", TCon_serialNo


    timeout = 1.0
    TCon_deviceID, TCon_goodID, timeout = libxtcon.open_device (TCon_serialNo, timeout)
    print \
        "Device ID     :", TCon_deviceID, "\n" \
        "goodID        :", TCon_goodID, "\n" \
        "Remaining time:", timeout, "sec", "\n"

    if (timeout == 0.0) or (not TCon_goodID):
        print 'Communication timeout in open_device.'
        exit (-2)

    sensorID =  1# 0:RTD1, 1:RTD2(Sample Temperature), 2:TC1
    isothermal_start (TCon_deviceID, setpoint)
    stabilize_temp (TCon_deviceID, sensorID, tolerance, monitoring_period)
    ##########################################################################
    voltage        = 0.0
    current        = 0.01
    filterLength = 1

    set_VM_range (SMU_deviceID)
    set_DC_current (SMU_deviceID, current)
    measureV (SMU_deviceID, TCon_deviceID, sensorID, run_time)

    set_DC_voltage (SMU_deviceID, voltage)
    raw_input ("Run Finished. Press Enter to Exit\n")

    ##########################################################################
    # closes the device.
    libxsmu.close_device(SMU_deviceID)
    libxtcon.close_device(TCon_deviceID)

main()
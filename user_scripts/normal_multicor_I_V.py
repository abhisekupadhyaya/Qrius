import sys, time
import libxsmu
import libxtcon
import csv
import numpy as np
from multiprocessing import Process

def set_VM_range (SMU_deviceID):
	timeout = 15.0
	voltageMeterRange = 4 # 0: 1mV, 1: 10mV, 2: 100mV, 3: 1V, 4: 10V, 5: 100V
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

def set_CM_Range(deviceID):
    
    ############################
    # Set CM range
    
    timeout = 1.0
    currentMeterRange = 1# 0: 10uA, 1: 100uA, 2: 1mA, 3: 10mA, 4: 100mA
    
    currentMeterRange, timeout = \
            libxsmu.CM_setRange (deviceID, currentMeterRange, timeout)
    
    print \
            "currentMeterRange    :", currentMeterRange, "\n" \
            "Remaining time        :", timeout, "sec", "\n"

    if (timeout == 0.0):
        print 'Communication timeout in CM_setRange.'
        exit (-2)


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


def measureV (SMU_deviceID,run_time, filename):
	##########################################################################
	# Start recording streamed data from the XSMU
	set_VM_range (SMU_deviceID)
	
	print \
		"Getting Data"

	logfile = open (filename, 'w')

	t0 = time.time()
	_time_ = 0
	time_now = time.time() - t0
	while (time_now < run_time):
		print "Remaining time: ", (run_time - (time_now)) / 60.0, " minutes"

		filter_length = 1
		timeout = 1 + 0.03 * filter_length
		voltage, timeout    = libxsmu.VM_getReading (SMU_deviceID, filter_length, timeout)
		time_now = time.time() - t0
		_time_ = _time_ + 1

		logfile.write (str (_time_)+ ", " + str (time_now) + ", " + str (voltage)  + '\n')
		print _time_, ',\t', time_now, ',\t', voltage,  ' ADC'

		logfile.flush()

	logfile.close()
	print \
		"Stopped Recording Data"

def measureI (SMU_deviceID,run_time, filename):
	##########################################################################
	# Start recording streamed data from the XSMU
	set_CM_Range(SMU_deviceID)
	
	print \
		"Getting Data"

	logfile = open (filename, 'w')

	t0 = time.time()
	_time_ = 0
	time_now = time.time() - t0
	while (time_now < run_time):
		print "Remaining time: ", (run_time - (time_now)) / 60.0, " minutes"

		filter_length = 1
		timeout = 1 + 0.03 * filter_length
		current, timeout    = libxsmu.CM_getReading (SMU_deviceID, filter_length, timeout)
		time_now = time.time() - t0
		_time_ = _time_ + 1

		logfile.write (str (_time_)+ ", " + str (time_now) + ", " + str (current)  + '\n')
		print _time_, ',\t', time_now, ',\t', current,  ' ADC'

		logfile.flush()

	logfile.close()
	print \
		"Stopped Recording Data"

def measureT (TCon_deviceID, sensorID, run_time, filename):
    logfile = open (filename, 'w')
    t0 = time.time()
    data_no = 0
    while (time.time() - t0 < run_time):
        timeout = 1.0
        sensor, T, timeout = libxtcon.getSensorTemperature (TCon_deviceID, sensorID, timeout)
        time_now = time.time() - t0
        logfile.write (str (time_now) + ", " + str (T)  + '\n')
        print T, ',\t'
        logfile.flush()

        time.sleep (5)

    logfile.close()

def isothermal_start (TCon_deviceID, setpoint):
    runMode = 1 # 0:IDLE, 1:ISOTHERMAL, 2:LINEAR RAMP
    timeout = 1.0
    libxtcon.setIsothermal(TCon_deviceID, setpoint, timeout)
    print ("Isothermal is set on : ", str (setpoint)+ '\n')

    timeout = 1.0
    libxtcon.startRun(TCon_deviceID, runMode, timeout)
    print ("Starting Isothermal Run.. \n")


def isothermal_stop (TCon_deviceID):
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
    start_temp        = float(raw_input ("Enter starting setpoint (K)       : "))
    #ending_temp       = float(raw_input ("Enter ending setpoint (K)         : "))
    #step_size         = float(raw_input ("Enter step_size (K)               : "))    
    tolerance         = float(raw_input ("Tempereature Tolerance  (K)       : "))
    monitoring_period = int  (raw_input ("Enter the monitoring period (int) : "))
    run_time          = int  (raw_input ("Enter Time For This Run (sec)     : "))

    setpoints = []
    setpoints.append(start_temp)


    response = raw_input("Press y to add more setpoint? : y \n")
    while (response == 'y'):
    	next_setpoint = float(raw_input ("Enter next setpoint (K)       : "))
    	setpoints.append(next_setpoint)
        response = raw_input("Press y to add more setpoint? : y/n \n")


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
    ##########################################################################
    voltage_initial = 5.0
    voltage        = 0.0
    current        = 0.002
    set_VM_range (SMU_deviceID)
    #set_DC_current(SMU_deviceID, current)
    set_DC_voltage (SMU_deviceID, voltage_initial)

    for setpoint in setpoints:
    	#response = raw_input("Press y to continue? : y \n")
    	#while (response != 'y'):
    		#response = raw_input("Press y to continue?: y \n")

        isothermal_start (TCon_deviceID, setpoint)
        stabilize_temp (TCon_deviceID, sensorID, tolerance, monitoring_period)

        ##########################################################################
        voltage_filename = "V_" + str(setpoint) + ".csv"
        temperature_filename = "T_" + str(setpoint) + ".csv"
        current_filename = "I_" + str(setpoint) + ".csv"

        if __name__=='__main__':
            #I_V_data            = Process(target = measureV, args = (SMU_deviceID, run_time, voltage_filename))
            temperature_measure = Process(target = measureT, args = (TCon_deviceID, sensorID, run_time, temperature_filename))

            #I_V_data.start()
            temperature_measure.start()
            measureI(SMU_deviceID, run_time, current_filename)

            #I_V_data.join()
            temperature_measure.join()

    set_DC_voltage (SMU_deviceID, voltage)

    raw_input ("Run Finished. Press Enter to Exit\n")

    ##########################################################################
    # closes the device.
    libxsmu.close_device(SMU_deviceID)
    libxtcon.close_device(TCon_deviceID)

main()
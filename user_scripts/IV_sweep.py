#-------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#
# ALGORITHM FOR IV MEASUREMENTS
#
# Set voltage source to 0
# Call function to measure IV
# Print out the (voltage, current, time) values
# Change voltage source to (value + step_size)
#
# measure current, if (current_new - current_old) > current_step -> switch mode to current
# 	Set current source to (last measured current value + current_step) 
# 	Call function to measure current
# 	Call function to measure voltage
# 	Loop over the measuring functions
# 	Print out the (voltage, current, time) values
#
# measure current, if (current_new - current_old) < current_step -> keep the new voltage value
# 	Call function to measure current
# 	Call function to measure voltage
# 	Loop over the measuring functions
# 	Print out the (voltage, current, time) values
#
#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------

import sys, time
import libxsmu
import csv
import numpy as np

logfile = open("histogram_data.txt", "w")
logfile.close ()

def set_DC_voltage (deviceID, value):
    
    ############################
    # Set VS range

    timeout = 1.0
    voltageSourceRange = 0 # 0: 10V, 1: 100V

    print \
    "voltageSourceRange    :", voltageSourceRange, "\n" \
    "Remaining time        :", timeout, "sec", "\n"

    voltageSourceRange, timeout = \
        libxsmu.VS_setRange (deviceID, voltageSourceRange, timeout)

    if (timeout == 0.0):
        print 'Communication timeout in VS_setRange.'
        exit (-2)
        
    ############################
    # Set VS voltage

    timeout = 1.0
    voltage = value
    voltage, timeout = libxsmu.VS_setVoltage (deviceID, voltage, timeout)
    print \
            "Voltage: ", voltage, "\n" \
            "Timeout: ", timeout

    if (timeout == 0.0):
        print 'Communication timeout in VS_setVoltage'
        exit (-2)

    ############################
    time.sleep(1)
    

def set_DC_current (deviceID, value):

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
	libxsmu.CS_setRange (deviceID, currentSourceRange, timeout)
    
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
    current, timeout = libxsmu.CS_setCurrent (deviceID, current, timeout)
    
    print \
            "Current: ", current, "\n" \
            "Timeout: ", timeout

    if (timeout == 0.0):
        print 'Communication timeout in CS_setCurrent'
        exit (-2)

    ############################
    time.sleep(1)
    
def set_CM_Range(deviceID, range):
    
    ############################
    # Set CM range
    
    timeout = 1.0
    currentMeterRange = range # 0: 10uA, 1: 100uA, 2: 1mA, 3: 10mA, 4: 100mA
    
    currentMeterRange, timeout = \
            libxsmu.CM_setRange (deviceID, currentMeterRange, timeout)
    
    print \
            "currentMeterRange    :", currentMeterRange, "\n" \
            "Remaining time        :", timeout, "sec", "\n"

    if (timeout == 0.0):
        print 'Communication timeout in CM_setRange.'
        exit (-2)
    
def measureI (deviceID, filterLength):

    ############################
    # Set CM Range to 10mA
    set_CM_Range(deviceID, 3)
    
    ############################
    # Get CM Current
    
    filter_length = filterLength
    timeout = 1 + 0.022 * filter_length
    
    current, timeout = libxsmu.CM_getReading (deviceID, filter_length, timeout)
    
    print '**** Current : ' + str(current) + ' ****'
    
    if (timeout == 0.0):
	print 'Communication timeout in CM_getReading.'
	exit (-2)
	
    ############################
    
    if (np.abs(current) < 0.0001):
        # Set CM Range to 100uA
        set_CM_Range(deviceID, 1)
        print 'Range : 100 uA'
        
    elif (np.abs(current) < 0.001):
        # Set CM Range to 1mA
        set_CM_Range(deviceID, 2)
        print 'Range : 1 mA'
    
    elif (np.abs(current) < 0.01):
        print 'Range : 10 mA'
    
    else :
        print 'Out of Range'
        
    ############################
    
    timeout = 1 + 0.022 * filter_length
    current, timeout = libxsmu.CM_getReading (deviceID, filter_length, timeout)
    
    print \
	"current               :", current, "\n" \
	"Remaining time        :", timeout, "sec", "\n"

    if (timeout == 0.0):
	print 'Communication timeout in CM_getReading.'
	exit (-2)
    
    return current


def set_VM_Range(deviceID, range):
    
    ############################
    # Set VM range
    
    timeout = 1.0
    voltageMeterRange = range # 0: 1mV, 1: 10mV, 2: 100mV, 3: 1V, 4: 10V, 5: 100V
    
    voltageMeterRange, timeout = \
            libxsmu.VM2_setRange (deviceID, voltageMeterRange, timeout)
    print \
            "voltageMeterRange    :", voltageMeterRange, "\n" \
            "Remaining time        :", timeout, "sec", "\n"

    if (timeout == 0.0):
        print 'Communication timeout in VM_setRange.'
	exit (-2)


def measureV (deviceID, filterLength):
      
    ############################
    # Set VM Range to 10V
    
    set_VM_Range(deviceID, 4)

    ############################
    # Get VM Voltage
    
    filter_length = filterLength
    timeout = 1 + 0.03 * filter_length
    
    voltage, timeout = libxsmu.VM2_getReading (deviceID, filter_length, timeout)
    
    print '**** Voltage : ' + str(voltage) + ' ****'
    
    if (timeout == 0.0):
        print 'Communication timeout in VM_getReading.'
	exit (-2)
    
    ############################
    
    if (np.abs(voltage) < 0.01):
        ############################
        # Set VM Range to 100mV
        set_VM_Range(deviceID, 2)
        print 'VM Range : 100 mV'
    
    elif (np.abs(voltage) < 1):
        ############################
        # Set VM Range to 1V
        set_VM_Range(deviceID, 3)
        print 'VM Range : 1 V'
        
    elif (np.abs(voltage < 10)):
        print 'VM Range : 10 V'
        
    else :
        print 'Out of Range'
        
    ############################
    
    timeout = 1 + 0.03 * filter_length
    
    voltage, timeout = libxsmu.VM2_getReading (deviceID, filter_length, timeout)

    print \
            "voltage               :", voltage, "\n" \
            "Remaining time        :", timeout, "sec", "\n"
	
    if (timeout == 0.0):
        print 'Communication timeout in VM_getReading.'
	exit (-2)
	
    return voltage


def measure_IV (deviceID, iteration, mode, filterLength):
			
    logfile = open("histogram_data.txt", "a")
    
    for index in range(iteration):
        
        current = measureI(deviceID, filterLength)
        voltage = measureV(deviceID, filterLength)

        logfile.write(str(voltage) + "," + str(current) + "," + str(time.time()) + "," + mode + "\n")
    
    
    logfile.write ('Next Source Value...\n')
    logfile.close ()
    
    print current, voltage
    
    return current, voltage

def sourceMode (deviceID, mode):
    
    timeout = 10.0
    sourceMode, timeout = libxsmu.setSourceMode (deviceID, mode, timeout)
    print \
	"sourceMode    :", sourceMode, "\n" \
	"Remaining time:", timeout, "sec", "\n"

    if (timeout == 0.0):
	print 'Communication timeout in setSourceMode.'
	exit (-2)


def sourceSwitching (deviceID, voltage, current, voltage_step, current_step, mode, filterLength):
            
    if (mode == "VOLTAGE"):
    
        set_DC_voltage (deviceID, (voltage + voltage_step))
        current_new = measureI(deviceID, filterLength)
        set_DC_voltage (deviceID, voltage)
        
        if (np.abs(current_new - current) >= current_step):
            sourceMode (deviceID, 1)  # source mode : 0 = Voltage, 1 = Current
            return "CURRENT"
        
        else:
            return "VOLTAGE"
    
    else :
        set_DC_current (deviceID, current + current_step)
	voltage_new = measureV(deviceID, filterLength)
	set_DC_current (deviceID, current)
	
	if (np.abs(voltage_new - voltage) >= voltage_step):
		sourceMode (deviceID, 0)  # source mode : 0 = Voltage, 1 = Current
		return "VOLTAGE"
	
	else:
		return "CURRENT"

    
def main():
    
    
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

        serialNo = 'XSMU012A'
        print "Serial number:", serialNo

        timeout = 1.0
        deviceID, goodID, timeout = libxsmu.open_device (serialNo, timeout)
        print \
                "Device ID     :", deviceID, "\n" \
                "goodID        :", goodID, "\n" \
                "Remaining time:", timeout, "sec", "\n"

        if (timeout == 0.0) or (not goodID):
                print 'Communication timeout in open_device.'
                exit (-2)

        ##########################################################################
	# User input parameters
	
	Voltage_Range = float (raw_input ("Enter Voltage Range     (V) : "))    # V
	Current_Range = float (raw_input ("Enter Current Range     (A) : "))    # I
	Voltage_Step  = float (raw_input ("Enter Voltage Step Size (V) : "))    # Delta_V
	Current_Step  = float (raw_input ("Enter Current Step Size (A) : "))    # Delta_V
	iteration     = int   (raw_input ("Enter number of iterations  : "))    # no. of measurements at each (I,V) point
	
	##########################################################################
	#Intelligent Switching algorithm
	
	voltage        = 0.0
	current        = 0.0
	mode    = "VOLTAGE"
	
        filterLength = 1
	
	set_DC_voltage(deviceID, voltage)
	
	while ((voltage <= Voltage_Range) and (current <= Current_Range)):
		
		if (mode == "VOLTAGE"):
			
			set_DC_voltage (deviceID, voltage)
			current, voltage = measure_IV      (deviceID, iteration, mode, filterLength)
			mode             = sourceSwitching (deviceID, voltage, current, Voltage_Step, Current_Step, mode, filterLength)
			
			if (mode == "VOLTAGE"):
				voltage = voltage + Voltage_Step
			
			else:
				current = current + Current_Step
		
		elif (mode == "CURRENT"):
			
			set_DC_current (deviceID, current)
			current, voltage = measure_IV      (deviceID, iteration, mode, filterLength)
			mode             = sourceSwitching (deviceID, voltage, current, Voltage_Step, Current_Step, mode, filterLength) 

			if (mode == "VOLTAGE"):
				voltage = voltage + Voltage_Step
			
			else:
				current = current + Current_Step
		
		print mode   

	set_DC_voltage    (deviceID, 0.0)
	
	raw_input ("Run Finished. Press Enter to Exit\n")
	
	##########################################################################
        # closes the device.

        libxsmu.close_device(deviceID)

main()

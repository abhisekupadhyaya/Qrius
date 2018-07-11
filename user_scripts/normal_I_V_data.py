import sys, time
import libxsmu
import csv
import numpy as np

logfile = open ('V-Measurement.txt', 'w')
logfile.close()


def set_VM_range (SMU_deviceID):
	timeout = 15.0
	voltageMeterRange = 2 # 0: 1mV, 1: 10mV, 2: 100mV, 3: 1V, 4: 10V, 5: 100V
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


def measureV (SMU_deviceID,run_time):
	##########################################################################
	# Start recording streamed data from the XSMU
	
	print \
		"Getting Data"

	logfile = open ('V-Measurement.txt', 'w')

	t0 = time.time()
	_time_ = 0
	while (time.time() - t0 < run_time):
		print "Remaining time: ", 60 - (time.time() - t0) / 60.0, " minutes"
		filter_length = 1
		timeout = 1 + 0.03 * filter_length
		voltage, timeout    = libxsmu.VM_getReading (SMU_deviceID, filter_length, timeout)
		time_now = time.time() - t0
		_time_ = _time_ + 1
		logfile.write (str (_time_)+ ", " + str (time_now) + ", " + str (voltage)  + '\n')
		print _time_, ',\t', time_now, ',\t', voltage,  ' ADC'
		logfile.flush()

	logfile.close()
	timeout = set_DC_voltage (SMU_deviceID, voltage)
	print \
		"Stopped Recording Streamed Data"

    
def main():
	##########################################################################
    # User input parameters
    run_time          = int  (raw_input ("Enter Time For This Run (sec)     : "))

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

    voltage        = 0.0
    current        = 0.01

    set_VM_range (SMU_deviceID)
    #set_DC_current(SMU_deviceID, current )
    set_DC_voltage (SMU_deviceID, voltage)

    measureV(SMU_deviceID, run_time)
    set_DC_voltage (SMU_deviceID, voltage)

    raw_input ("Run Finished. Press Enter to Exit\n")

    ##########################################################################
    # closes the device.
    libxsmu.close_device(SMU_deviceID)

main()
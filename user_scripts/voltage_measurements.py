import sys, time

sys.path.insert(0,"../modules/xsmu")
sys.path.insert(0,"../modules/xtcon")
sys.path.insert(0,"../apps")
sys.path.insert(0,"../apps/widgets")
sys.path.insert(0,"../lib")

import xsmu
import tcon
import numpy as np
from XSMU_Constants import *

f = open("V-Data.txt", "w")
f.close()

# Set current source to some value
# Call function to measure voltage
# Loop over the measuring function
# Print out the voltage values

def set_DC_current (xsmu_driver, value, source_range):

    mode       = SOURCE_MODE_CS
    autorange  = AUTORANGE_ON
    range      = source_range

    xsmu_driver.setSourceParameters (mode, autorange, range, value)

def measure_voltage (xsmu_driver, xtcon_driver, iterations):
    
    f = open("V-Data.txt", "a")
    for index in range(iterations):
        voltage     = xsmu_driver.VM_getReading( filterLength = 1 )
        temperature = xtcon_driver.getSampleTemperature()
        f.write(str(voltage) + "," + str(temperature) + '\n')
    f.close() 	

def stabilize_temp (xtcon_driver, tolerance, monitoring_period):
    
    history = []
    
    print ("Stabilizing .. \n")
    
    while True :
        history.append(xtcon_driver.getSampleTemperature())
        
        if (len(history) < monitoring_period):
            continue
        else :
            fluctuation = max(history[-monitoring_period:-1]) - min(history[-monitoring_period:-1])
            print "Max : " + str (max(history[-monitoring_period:-1])) + "\tMin : " + str(min(history[-monitoring_period:-1]))
            
            if (np.abs(fluctuation) < tolerance):
                print ("Fluctuation : " + str(fluctuation))
                print ("Stable ..\n")
                break

def main():
	
	xtcon_driver  = tcon.Driver      ()
        xtcon_devices = xtcon_driver.scan()
	xtcon_driver.open(xtcon_devices[0])
	
	setpoint           = float(raw_input ("Enter isothermal setpoint                                 (K) : "))
	tolerance          = float(raw_input ("Tempereature Tolerance      (over 10 successive readings) (K) : "))
	monitoring_period  = int  (raw_input ("Enter the monitoring_period (      Positive Integer     )     : "))
	
	print ("Starting Isothermal Run.. \n")
	xtcon_driver.setIsothermalSetpoint (setpoint)
	xtcon_driver.startIsothermalControl()
	
	# Stabilizes the temperature and waits for user to take an IV run from Qrius GUI
	stabilize_temp (xtcon_driver, tolerance, monitoring_period)
	raw_input      ("Press Enter when IV from Qrius GUI is complete")
	
	response = raw_input("Press y to continue? : y \n")
	while (response != 'y'):
            response = raw_input("Press y to continue? : y/n \n")

	xsmu_driver  = xsmu.Driver()
	xsmu_driver.open("XSMU012A")
	
	Amplitudes   = [0.005, 0.0005, 0.00005]
	ranges       = [CM_RANGE_10mA, CM_RANGE_1mA, CM_RANGE_100uA]
	time_stamps  = []
	
	iterations     = int(raw_input("Enter Number of iterations : "))
	
	for i in range(len(Amplitudes)):
            
            time_stamps.append(time.time())
            
            DC_amplitude   = Amplitudes[i]    # A
            DC_range       = ranges[i]
	
            print ("Setting DC Current.. \n")
	
            set_DC_current  (xsmu_driver, DC_amplitude, DC_range)
            measure_voltage (xsmu_driver, xtcon_driver, iterations)
	
	xtcon_driver.stopIsothermalControl()
	set_DC_current (xsmu_driver, 0.0, ranges[0])
	
        filename = open("TimeStamps.txt", "w")
        
        for item in time_stamps:
            filename.write(str(item) + "\n")
        
        filename.close()
	
	xtcon_driver.close()
        xsmu_driver.close()

main()

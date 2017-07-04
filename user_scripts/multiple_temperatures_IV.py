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

f = open("I-T-Data.txt", "w")
f.close()

# Set voltage source to some value
# Call function to measure current
# Loop over the measuring function
# Print out the current values

def set_DC_voltage (xsmu_driver, value):

    mode       = SOURCE_MODE_VS
    autorange  = AUTORANGE_ON
    range      = VS_RANGE_10V

    xsmu_driver.setSourceParameters (mode, autorange, range, value)

def measure_current(xsmu_driver, xtcon_driver, iterations):
    
    f = open("I-Data.txt", "a")
    for index in range(iterations):
        current = xsmu_driver.CM_getReading( filterLength = 1 )
        temperature = xtcon_driver.getSampleTemperature()
        f.write(str(current) + "," + str(temperature) + '\n')
    f.close() 	
   
def stabilize_temp (xtcon_driver, tolerance, monitoring_period):
    
    history = []
    
    print ("Stabilizing .. \n")
    
    while True :
        history.append(xtcon_driver.getSampleTemperature())
        
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
	
	xtcon_driver = tcon.Driver()
	xtcon_devices = xtcon_driver.scan()
	xtcon_driver.open(xtcon_devices[0])

	setpoint          = float(raw_input ("Enter starting setpoint (K)       : "))
	ending            = float(raw_input ("Enter ending setpoint (K)         : "))
	step_size         = float(raw_input ("Enter step_size (K)               : "))    
	tolerance         = float(raw_input ("Tempereature Tolerance  (K)       : "))
	monitoring_period = int  (raw_input ("Enter the monitoring period (int) : "))
	iterations        = int  (raw_input ("Enter Number of iterations  (int) : "))

	response = raw_input("Press y to continue? : y \n")
	while (response != 'y'):
	    response = raw_input("Press y to continue? : y/n \n")
	
	while (setpoint < ending):
	    xtcon_driver.setIsothermalSetpoint (setpoint)
	    print ("Starting Isothermal Run.. \n")
	    xtcon_driver.startIsothermalControl()
	    
	    stabilize_temp (xtcon_driver, tolerance, monitoring_period)
	    # Stabilizes the temperature and waits for user to take an IV run from Qrius GUI
	    raw_input ("Press Enter when IV from Qrius GUI is complete")
	    

	    xsmu_driver  = xsmu.Driver()
	    xsmu_devices = xsmu_driver.scan()
	    xsmu_driver.open(xsmu_devices[0])
	    
	    Amplitudes          = [0.67, 0.74]
	    time_stamps         = []
	    
	    for i in range(len(Amplitudes)):
		
		time_stamps.append(time.time())
		
		DC_amplitude   = Amplitudes[i]    # V
	    
		print ("Setting DC Voltage.. \n")
	    
		set_DC_voltage (xsmu_driver, DC_amplitude)
		measure_current(xsmu_driver, xtcon_driver, iterations)
	    
	    
	    set_DC_voltage (xsmu_driver, 0.0)
	    
	    filename = open("TimeStamps.txt", "w")
	    
	    for item in time_stamps:
		filename.write(str(item) + "\n")
	    
	    filename.close()
	    xsmu_driver .close()
	    setpoint = setpoint + step_size
	
	xtcon_driver.stopIsothermalControl()
	xtcon_driver.close()
        

main()
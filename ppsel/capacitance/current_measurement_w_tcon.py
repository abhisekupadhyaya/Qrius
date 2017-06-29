import sys, time

sys.path.insert(0,"../../modules/xsmu")
sys.path.insert(0,"../../modules/xtcon")
sys.path.insert(0,"../../apps")
sys.path.insert(0,"../../apps/widgets")
sys.path.insert(0,"../../lib")

import math
import xsmu
import tcon
import numpy as np
from XSMU_Constants import *

# Set voltage source to some value
# Call function to measure current
# Loop over the measuring function
# Print out the current values

def set_DC_voltage (xsmu_driver, value):

	mode       = SOURCE_MODE_VS
	autorange  = AUTORANGE_ON
	range      = VS_RANGE_10V
	
	xsmu_driver.setSourceParameters (mode, autorange, range, values)

def measure_current(xsmu_driver):
    
    for index in range(100):
        current = xsmu_driver.CM_getReading()
        print ("The value of current is " + current + " and the time is " + time.strftime('%H:%M:%S') + '\n') 	
   
def stabilize_temp (xtcon_driver, tolerance):
    
    sample_temperature = xtcon_driver.getSampleTemperature()
    history = []
    
    print ("Stabilizing .. \n")
    
    while True :
        history.append(sample_temperature)
        
        if (len(history)<10):
            continue
        else :
            fluctuation = max(history[-10:-1]) - min(history[-10:-1])
        
        if (np.abs(fluctuation) < tolerance):
            print ("Stable ..\n")
            break
        
        

def main():
	
	xsmu_driver = xsmu.Driver()
	xtcon_driver = tcon.Driver()
	
	xsmu_devices = xsmu_driver.scan()
	xsmu_driver.open(xsmu_devices[0])
	
	DC_amplitude   = float(raw_input ("Enter DC Voltage (V) : "))    # V
	setpoint       = float(raw_input ("Enter isothermal setpoint (K) :"))
	
	xtcon_driver.setIsothermalSetpoint (setpoint)
	print ("Starting Isothermal Run.. \n")
	xtcon_driver.startIsothermalControl()
	
	stabilize_temp (xtcon_driver, tolerance)
	
	print ("Setting DC Voltage.. \n")
	set_DC_voltage (xsmu_driver, DC_amplitude)
	measure_current()
	
	xtcon_driver.stopIsothermalControl()
	set_DC_voltage (xsmu_driver, 0.0)
	xlia_driver.close()
	xsmu_driver.close()

main()

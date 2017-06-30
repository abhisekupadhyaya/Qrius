import sys, time

sys.path.insert(0,"../../modules/xsmu")
sys.path.insert(0,"../../modules/xtcon")
sys.path.insert(0,"../../apps")
sys.path.insert(0,"../../apps/widgets")
sys.path.insert(0,"../../lib")

import xsmu
import tcon
import numpy as np
from XSMU_Constants import *

f = open("I-Data.txt", "w")
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

def measure_current(xsmu_driver, iterations):
    
    f = open("I-Data.txt", "a")
    for index in range(iterations):
        current = xsmu_driver.CM_getReading( filterLength = 1 )
        f.write(str(current) + '\n')
    f.close() 	
   
def stabilize_temp (xtcon_driver, tolerance):
    
    history = []
    
    print ("Stabilizing .. \n")
    
    while True :
        history.append(xtcon_driver.getSampleTemperature())
        
        if (len(history)<100):
            continue
        else :
            fluctuation = max(history[-100:-1]) - min(history[-100:-1])
            print ("Max : ", max(history[-100:-1]), "\tMin : ", min(history[-100:-1]))
            
            if (np.abs(fluctuation) < tolerance):
                print ("Fluctuation : " + str(fluctuation))
                print ("Stable ..\n")
                break
        
        

def main():
	
	xsmu_driver = xsmu.Driver()
	xtcon_driver = tcon.Driver()
	
	xsmu_devices = xsmu_driver.scan()
	xsmu_driver.open(xsmu_devices[0])
	
	xtcon_devices = xtcon_driver.scan()
	xtcon_driver.open(xtcon_devices[0])
	
	DC_amplitude   = float(raw_input ("Enter DC Voltage (V) : "))    # V
	setpoint       = float(raw_input ("Enter isothermal setpoint (K) :"))
	tolerance      = float(raw_input ("Tempereature Tolerance (over 10 successive readings) (K) : "))
	iterations     = int  (raw_input ("Iterations : "))
	
	xtcon_driver.setIsothermalSetpoint (setpoint)
	print ("Starting Isothermal Run.. \n")
	xtcon_driver.startIsothermalControl()
	
	stabilize_temp (xtcon_driver, tolerance)
	
	print ("Setting DC Voltage.. \n")
	set_DC_voltage (xsmu_driver, DC_amplitude)
	measure_current(xsmu_driver, iterations)
	
	xtcon_driver.stopIsothermalControl()
	set_DC_voltage (xsmu_driver, 0.0)
	
	xtcon_driver.close()
        xsmu_driver.close()

main()

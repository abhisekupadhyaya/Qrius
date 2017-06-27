import sys, time

sys.path.insert(0,"../../modules/xlia")
sys.path.insert(0,"../../modules/xsmu")
sys.path.insert(0,"../../apps")
sys.path.insert(0,"../../apps/widgets")
sys.path.insert(0,"../../lib")

import xlia
import xsmu
from XSMU_Constants import *
import math

def set_DC_voltage (xsmu_driver, value):
    
    mode = SOURCE_MODE_VS
    autorange = AUTORANGE_ON
    range = VS_RANGE_10V
    
    xsmu_driver.setSourceParameters(mode, autorange, range, value)
    
def set_AC_voltage (xlia_driver, amplitude, frequency, phase):
    
    xlia_driver.setReferenceParameters (amplitude, frequency, phase)

def main():
    
	xlia_driver = xlia.Driver()
	xlia_devices = xlia_driver.scan()
	xlia_driver.open(xlia_devices[0])
	
	xsmu_driver = xsmu.Driver()
	xsmu_devices = xsmu_driver.scan()
	xsmu_driver.open(xsmu_devices[0])
	
	DC_amplitude   = float(raw_input ("Enter DC Voltage (V) : "))    # V
	AC_amplitude   = float(raw_input ("Enter AC Voltage (mV) : "))   # mV
        AC_frequency   = float(raw_input ("Enter freq (Hz) : "))             # Hz
        AC_phase       = float(raw_input ("Enter phase (deg) : "))           #  Degrees
	
	set_DC_voltage (xsmu_driver, DC_amplitude)
	set_AC_voltage (xlia_driver, AC_amplitude, AC_frequency, AC_phase)
	
	raw_input ("Measure the signals. Press Enter to disconnect xsmu and xlia.")
	set_DC_voltage (xsmu_driver, 0.0)
	set_AC_voltage (xsmu_driver, 0.0, 0.0, 0.0) #This line throws an error (even if I set arguments (xlia_driver, 10.0, 10.0, 10.0))
	
	xlia_driver.close()
	xsmu_driver.close()

main()


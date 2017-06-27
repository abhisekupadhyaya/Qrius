import sys, time

sys.path.insert(0,"../../modules/xlia")
sys.path.insert(0,"../../apps")
sys.path.insert(0,"../../apps/widgets")
sys.path.insert(0,"../../lib")

import xlia
import math

freqList = [ 10, 25, 75, 175, 425, 975, 1775, 3775, 8775]
ampl = 0.1
phase = 0
Rl = 101080
preAmpGain = 2
postAmpGain = 0

def freqSweep(liaDriver):

	fd = open('freqSweepOutput.csv', 'w')
	fd.write('# Reference frequency, Rl, V1, A1, V2, A2, Capacitance')
	fd.write('# Hz, ohm, V, deg, V, deg, SI')


	for freq in freqList:
		liaDriver.setReferenceParameters (ampl, freq, phase)

		raw_input("Put the switch down and press Enter to continue...")
		data1 = liaDriver.doMeasurement (16)
		line = str(freq) + ', ' + str(Rl) + ', ' + str(data1[2]) + ', ' + str(data1[3]) + ', '
		raw_input("Put the switch up and press Enter to continue...")
		data2 = liaDriver.doMeasurement (16)
		cap = data2[2] / ( data1[2] * 2 * math.pi * freq * Rl * math.sin(data2[3] - data1[3]))
		line = line + str(data2[2]) + ', ' + str(data2[3]) + ', ' + str(cap)
		print line
		fd.write(line)
	fd.close()

def freqCalib(liaDriver):

	fd = open('freqCalibOutput.csv', 'w')
	fd.write('# Reference frequency, Set Amplitude, Set Phase, Output Voltage, Output Phase')
	fd.write('# Hz, V, deg, V, deg')

	for freq in freqList:
		liaDriver.setReferenceParameters (ampl, freq, phase)
		data = liaDriver.doMeasurement (16)
		line = str(freq) + ', ' + str(ampl) + ', ' + str(phase) + ', ' + str(data[2]) + ', ' + str(data[3])
		print line
		fd.write(line)
		#raw_input("Press Enter to continue...")


def main():
	liaDriver = xlia.Driver()
	devices = liaDriver.scan()
	liaDriver.open(devices[0])
	liaDriver.setMeasurementSettings (preAmpGain = preAmpGain,
									postAmpGain = postAmpGain)
	freqCalib (liaDriver)
	liaDriver.close()

main()

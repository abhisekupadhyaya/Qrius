import functools, string
from Tkinter import *
import libxsmu
import app_calib_vm

VOLTAGE_UNITS            = [0.001, 0.001, 0.001,   1.0,   1.0,    1.0]    #units in which voltage is measured for each range
VOLTAGE_FULL_SCALE_UNITS = [0.001,  0.01,   0.1,   1.0,  10.0,  100.0]
SCALING_FACTORS          = [ -1.0,  -0.9,   0.0,   0.9,   1.0]

PRECISION = 5
SUCCESS = 0
FAIL = 1
TIMEOUT_INTERVAL = 1.0

"""
Usage:
How to calibrate Voltage Measurement Module?
* From main menu select {\tt Utilities -> Calibration -> Voltage Measure}
* On the Voltage Measure Calibration Window:
    - Connect to XSMU module from the menu option {\tt File -> Connect Device}
    - Since each range has its specific calibration table,
      select a particular voltage measurement range which needs to be calibrated.
    - As the voltage range is selected, a five-point calibration table
      corresponding to that range is populated in the window.
    - On selecting any one of the calibration point, voltage calibration value stored
      inside the XSMU module is updated in the {\tt Measured Voltage} column.
    - The {\tt Measured Voltage} value can be modified to match against a reference voltage measurement
      device connected. Press {\tt Return} or {\tt Tab} key to register this modified value in the
      XSMU module memory.
    - Similarly, rest of the points in the calibration table can be modified.
    - Click {\tt Save Calibration Table} button to store the entire revised table in the XSMU module memory.
      Please ensure that before changing to a different voltage range, the presently modified table is
      saved, otherwise the modified values will be lost.
    - Click {\tt Load Default Calibration} button to load the default calibration settings from the XSMU module memory.

"""

def calib_vm(root):
    """
    Adds menubar to the main app. window
    """
    oAppCalibVM = app_calib_vm.app_calib_vm(root)
    oCalibVM = CalibVM(oAppCalibVM)
    return oCalibVM


class CalibVM:
    def __init__(self, oAppCalibVM = None):
        """
        Initialize module
        """
        self.deviceID = None
        self.adcValues = []
        self.actualVoltageValues = []
        self.voltageMeasureRange = 0 #possible values: (0, 1,) 2, 3, 4 and 5
        self.voltageMeasureRangeLabel = app_calib_vm.VOLTAGE_RANGE_LABELS
        self.voltageUnitLabel = app_calib_vm.VOLTAGE_RANGE_UNIT_LABELS
        self.voltageUnit = VOLTAGE_UNITS
        self.calibFactors = [[val1*val2 for val1 in VOLTAGE_FULL_SCALE_UNITS] for val2 in SCALING_FACTORS]
        #self.calibFactors = [-10, -9, 0, 9, 10]
        self.timeout_occured = False
        if (oAppCalibVM != None):
            #if GUI is required
            self.oAppCalibVM = oAppCalibVM
            self.ConfigureCB()
        return

    def __del__(self):
        """
        Make sure that the device connection has been
        closed before the class destructs
        """
        if (self.deviceID != None):
            libxsmu.close_device(self.deviceID)
            print 'Device Disconnected\n'
        del self.deviceID
        return

    def ConfigureCB(self):
        """
        Configure callbacks for widgets
        """
        self.oAppCalibVM.filemenu.add_command(label='Connect to Device', underline=0, command=self.vConnectDeviceCB)
        for voltagerange in range(app_calib_vm.VOLTAGE_RANGE):
            self.oAppCalibVM.RBVMRange[voltagerange].config(command = functools.partial(self.vRBVMRangeCB,voltagerange))
        for channel in range(app_calib_vm.NO_OF_POINTS):
            self.oAppCalibVM.EntryVoltage[channel].bind('<Return>', functools.partial(self.vEntryVoltageCB,channel))
            self.oAppCalibVM.EntryVoltage[channel].bind('<Tab>', functools.partial(self.vEntryVoltageCB,channel))
            self.oAppCalibVM.EntryVoltage[channel].bind('<Key>', functools.partial(self.vClearHighlight,channel))
            self.oAppCalibVM.EntryVoltage[channel].bind('<Button-1>', functools.partial(self.vEntryVoltageOnFocus,channel))
            self.oAppCalibVM.RBEntry[channel].config(command = functools.partial(self.vRBEntryCB,channel))
        self.oAppCalibVM.RBEntry[0].bind('<Tab>', self.vRBEntryOnTab) #For consistency in tabbing
        self.oAppCalibVM.BtnSaveCalibTable.config(command = self.vBtnSaveCalibTableCB)
        self.oAppCalibVM.BtnLoadDefaultCalib.config(command = self.vBtnLoadDefaultCalibCB)
        self.oAppCalibVM.message.config(text = '')
        self.oAppCalibVM.EntryTestVoltage.bind('<Return>', self.vEntryTestVoltageCB)
        self.oAppCalibVM.EntryTestVoltage.bind('<Button-1>', self.vEntryTestVoltageOnFocus)
        return

    def vConnectDeviceCB(self):
        """
        Callback for Connect To Device Menu Entry
        """
        self.oAppCalibVM.filemenu.entryconfig(0,state = DISABLED)
        if (self.scanDevice() == SUCCESS):
            if (self.selectDevice() == SUCCESS):
                self.vEnableCalibration()
                self.entryModified = [0,0,0,0,0]
                self.oAppCalibVM.message.config(text = 'Communication Established.')
                self.vInvokeFirstRBVMRangeCB()
        else:
            self.vDeviceNotFound()
        return

    def vDisconnectDeviceCB(self):
        """
        Callback for Disconnect Device Menu Entry
        """
        self.oAppCalibVM.filemenu.entryconfig(0,state = DISABLED)
        self.deviceDisconnect()
        self.vDisableCalibration()
        self.oAppCalibVM.message.config(text = 'Device Disconnected.')
        return

    def vEntryTestVoltageCB(self, event=None):
        """
        Callback for Test Calibration Entry
        """
        try:
            self.oAppCalibVM.RBEntry[self.oAppCalibVM.data_point.get()].deselect()
        except:
            pass
        if(self.setVoltage(self.oAppCalibVM.EntryTestVoltage.get()) == FAIL):
            self.oAppCalibVM.TestVoltageValue.set(0.0)
        else:
            self.oAppCalibVM.message.config(text = 'Test Voltage Set.')
        self.vCheckTimeout()
        return

    def vEntryVoltageOnFocus(self, index, event=None):
        try:
            self.oAppCalibVM.data_point.get()
        except:
            self.oAppCalibVM.RBEntry[index].invoke()
        self.vCheckTimeout()
        return

    def vEntryTestVoltageOnFocus(self, event=None):
        try:
            self.oAppCalibVM.RBEntry[self.oAppCalibVM.data_point.get()].deselect()
        except:
            pass
        if(self.deviceID != None):
            #Update message only if device is turned on
            self.oAppCalibVM.message.config(text = 'Enter Test Voltage.')
        self.vCheckTimeout()
        return

    def vRBVMRangeCB(self,index):
        """
        Callback for Voltage Range Selector
        """
        if(len(self.adcValues)!=0):
            #If calibration table has already
            #been populated for some other range
            self.vConfirmation(index)
            return

        if (self.setVoltageMeasureRange(index) == SUCCESS):
            self.oAppCalibVM.vUpdateVoltageUnit()
            if(self.getCalibration() == SUCCESS):
                self.vFillTable()
                self.vInvokeFirstRBEntryCB()
            if (self.voltageMeasureRangeLabel[index] == '100V'):
                self.setVoltageSourceRange(1) #For 100V Measure range set Source Range to 100V
            else:
                self.setVoltageSourceRange(0) #For lower Measure ranges set Source Range to 10V
        self.vCheckTimeout()
        return

    def vInvokeFirstRBVMRangeCB(self):
        """
        """
        try:
            #1mV and 10mV ranges are disabled
            lowest_range = min([_range  for _range in range(app_calib_vm.VOLTAGE_RANGE) if _range not in app_calib_vm.DISABLED_RANGE])
            self.oAppCalibVM.RBVMRange[lowest_range].invoke()
        except:
            pass
        return

    def vInvokeFirstRBEntryCB(self):
        """
        """
        try:
            self.oAppCalibVM.RBEntry[0].invoke()
        except:
            pass
        return

    def vEntryVoltageCB(self, index, event):
        """
        Callback after the voltage value has been entered
        """
        if(self.setCalibration(index,(self.oAppCalibVM.EntryVoltage[index].get())) == SUCCESS):
            self.oAppCalibVM.entryADCValues[index].set(self.adcValues[index])
            self.vHighlightVoltage(index)
            self.oAppCalibVM.message.config(text = 'Voltage Set.')
        else:
            self.oAppCalibVM.entryVoltageValues[index].set(0.0)
        if event.keysym=='Tab':
            if index < (app_calib_vm.NO_OF_POINTS - 1):
                self.oAppCalibVM.RBEntry[index+1].invoke()
        self.vCheckTimeout()
        return

    def vRBEntryCB(self,index):
        """
        Selects the point at which Calibration
        requires verification
        """
        self.oAppCalibVM.EntryVoltage[index].focus()
        if(self.setVoltageAtIndex(index) == SUCCESS):
            self.oAppCalibVM.message.config(text = 'Measure voltage at point ('+str(index)+')')
        self.vCheckTimeout()
        return

    def vRBEntryOnTab(self,event):
        '''
        On tabbing through the first data point it will be activated
        '''
        self.oAppCalibVM.RBEntry[0].invoke()
        return

    def vBtnSaveCalibTableCB(self):
        """
        Callback for Save Calibration button
        """
        for index in range(app_calib_vm.NO_OF_POINTS):
            try:
                float(self.oAppCalibVM.EntryVoltage[index].get())
            except:
                self.oAppCalibVM.message.config(text = 'Invalid Voltage Value!')
                return

        if(self.saveCalibration() == SUCCESS):
            self.oAppCalibVM.message.config(text = 'Calibration Saved.')
            self.entryModified = [0,0,0,0,0]
        self.vCheckTimeout()
        return

    def vBtnLoadDefaultCalibCB(self):
        """
        Callback for Load Calibration button
        """
        if(len(self.adcValues)!=0):
            #If calibration table has already been
            #populated for some other range
            self.vConfirmation()
            return

        if (self.loadDefaultCalibration() == SUCCESS):
            if (self.getCalibration() == SUCCESS):
                self.vFillTable()
                self.vInvokeFirstRBEntryCB()
                self.oAppCalibVM.message.config(text = 'Default Calibration Loaded.')
        self.vCheckTimeout()
        return

    def vHighlightVoltage(self, index):
        """
        Highlight entered voltage values
        """
        self.oAppCalibVM.EntryVoltage[index].configure(bg='yellow')
        self.entryModified[index] = 1
        return

    def vClearHighlight(self, index, event = None):
        """
        Clear highlight if entered voltage values are modified
        """
        self.oAppCalibVM.EntryVoltage[index].configure(bg='white')
        self.entryModified[index] = 0
        return

    def vEnableCalibration(self):
        """
        Enable calibration table widgets
        """
        self.oAppCalibVM.filemenu.entryconfig(0,command = self.vDisconnectDeviceCB,label='Disconnect Device')
        self.oAppCalibVM.filemenu.entryconfig(0,state = NORMAL)
        self.oAppCalibVM.vEnableVMRangeSelect()
        self.oAppCalibVM.vEnableCalibTable()
        self.oAppCalibVM.vEnableCalibTest()
        return

    def vDisableCalibration(self):
        """
        Disable calibration table widgets
        """
        self.oAppCalibVM.filemenu.entryconfig(0,command = self.vConnectDeviceCB,label='Connect To Device')
        self.oAppCalibVM.filemenu.entryconfig(0,state = NORMAL)
        self.oAppCalibVM.vDisableCalibTest()
        self.oAppCalibVM.vDisableCalibTable()
        self.oAppCalibVM.vDisableVMRangeSelect()
        return

    def vConfirmation(self, index = None):
        """
        Checks if entries have been modified
        """
        if(max(self.entryModified) == 0):
            self.adcValues = []
            self.actualVoltageValues = []
            if (index != None):
                self.oAppCalibVM.RBVMRange[index].invoke()
            else:
                self.oAppCalibVM.BtnLoadDefaultCalib.invoke()
            return
        else:
            if (self.oAppCalibVM.vConfimationPopup() == True):
                self.adcValues = []
                self.actualVoltageValues = []
                self.entryModified = [0,0,0,0,0]
                if (index != None):
                    self.oAppCalibVM.RBVMRange[index].invoke()
                else:
                    self.oAppCalibVM.BtnLoadDefaultCalib.invoke()
            else:
                self.oAppCalibVM.RBVMRange[self.voltageMeasureRange].select()
            return

    def vDeviceNotFound(self):
        """
        Reset widget if device is not found
        """
        self.vDisableCalibration()
        self.oAppCalibVM.message.config(text = 'Device Not Found.')
        return

    def vCheckTimeout(self):
        """
        Check for connection timeout
        """
        if (self.timeout_occured == True):
            self.vDisableCalibration()
            self.oAppCalibVM.message.config(text = 'Communication Timeout!')
        return

    def vFillTable(self):
        """
        Fill the calibration table with the obtained adc and voltage values
        """
        for index in range(app_calib_vm.NO_OF_POINTS):
            self.oAppCalibVM.entryADCValues[index].set(self.adcValues[index])
            self.oAppCalibVM.entryVoltageValues[index].set(round(self.actualVoltageValues[index]/self.voltageUnit[self.voltageMeasureRange],PRECISION))
            self.vClearHighlight(index)
        self.oAppCalibVM.vMakeADCreadonly()
        return

    def scanDevice(self):
        """
        Scan for available devices
        """
        self.number_of_devices = libxsmu.scan()
        if self.number_of_devices == 0:
            print 'No Device Found!\n'
            return FAIL
        else:
            print str(self.number_of_devices)+' XSMU Device(s) Found\n'
            return SUCCESS

    def selectDevice(self,device_number = 0):
        """
        Select the device specified by the device_number, otherwise select the first device available and get the deviceID
        """
        self.device_serial_No = libxsmu.serialNo(device_number)
        self.timeout_occured = False
        timeout = TIMEOUT_INTERVAL
        self.deviceID, goodID, timeout = libxsmu.open_device (self.device_serial_No, timeout)
        if (timeout == 0.0) or (not goodID):
            self._vOnDeviceTimeout()
            return FAIL
        print "Device "+str(device_number)+" selected\n"
        print "Device ID :", self.deviceID, "\n", "goodID :", goodID, "\n", "Device reply in :", (TIMEOUT_INTERVAL-timeout), "sec", "\n"
        timeout = TIMEOUT_INTERVAL
        self.sourceMode, timeout = libxsmu.setSourceMode (self.deviceID, 1, timeout)#Set to voltage source mode
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Source Mode set to : Voltage Source\n"
        self.voltageMeasureRange = 0
        return SUCCESS

    def _vOnDeviceTimeout(self):
        """
        Disconnect when device fails to respond
        """
        print 'Communication timeout in open device!\n'
        self.timeout_occured = True
        self.deviceDisconnect()
        return

    def deviceDisconnect(self):
        """
        Disconnect device
        """
        if (self.deviceID != None):
            libxsmu.close_device(self.deviceID)
            self.deviceID = None
            self.adcValues = []
            self.actualVoltageValues = []
            self.voltageMeasureRange = 0
            print 'Device Disconnected!\n'
            return SUCCESS
        else:
            print 'No Connection Present!\n'
            return FAIL

    def setVoltageMeasureRange(self,voltage_range):
        """
        Set the voltage range near which calibration needs to be performed
        """
        timeout = TIMEOUT_INTERVAL
        voltageMeasureRange, timeout = libxsmu.VM_setRange(self.deviceID, voltage_range, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        self.voltageMeasureRange = voltage_range
        print "Voltage measure range set to : "+str(self.voltageMeasureRangeLabel[self.voltageMeasureRange])+"\n"
        return SUCCESS

    def setVoltageSourceRange(self,voltage_range):
        """
        Set the voltage source range
        """
        timeout = TIMEOUT_INTERVAL
        voltageSourceRange, timeout = libxsmu.VS_setRange(self.deviceID, voltage_range, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Voltage source range set to : ",
        if (voltage_range == 0):
            print '10V\n'
        else:
            print '100V\n'
        return SUCCESS

    def getCalibration(self):
        """
        Get the adc and voltage values from device at different points
        """
        for index in range(app_calib_vm.NO_OF_POINTS):
            timeout = TIMEOUT_INTERVAL
            i, adc, voltage, timeout = libxsmu.VM_getCalibration (self.deviceID, index, timeout)
            if (timeout == 0.0):
                self._vOnDeviceTimeout()
                return FAIL
            self.adcValues.append(adc)
            self.actualVoltageValues.append(voltage)
        print "ADC and voltage values obtained successfully : "
        print "Index | ADC Values | Actual Voltage ("+str(self.voltageUnitLabel[self.voltageMeasureRange])+")"
        for index in range(app_calib_vm.NO_OF_POINTS):
            print '  '+string.rjust(str(index), 2)+'  | '+string.rjust(str(self.adcValues[index]),8)+'   | '+string.rjust(str(round((self.actualVoltageValues[index]/self.voltageUnit[self.voltageMeasureRange]),PRECISION)),10)
        print "\n"
        return SUCCESS

    def setCalibration(self, index, voltage_value):
        """
        Use the entered Voltage value to set calibration at specified point(index)
        """
        try:
            voltage_input = float(voltage_value)*self.voltageUnit[self.voltageMeasureRange]
        except:
            print "Invalid voltage value!\n"
            voltage_input = 0.0
            return FAIL

        if (libxsmu.firmware_version (self.deviceID)
                  >= libxsmu.make_version (2, 2, 0)):
            timeout = 10 * TIMEOUT_INTERVAL
        else:
            timeout = TIMEOUT_INTERVAL

        i, adc, voltage, timeout = libxsmu.VM_setCalibration(self.deviceID, index, voltage_input, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        self.adcValues[index] = adc
        self.actualVoltageValues[index] = voltage_input
        print 'Voltage Calibration Set : '+str(round((self.actualVoltageValues[index]/self.voltageUnit[self.voltageMeasureRange]),PRECISION))+str(self.voltageUnitLabel[self.voltageMeasureRange])+' at data point '+str(index)+"\n"
        return SUCCESS

    def setVoltageAtIndex(self, index):
        """
        Set voltage at specified point(index)
        """
        if(self.setVoltage(self.calibFactors[index][self.voltageMeasureRange]) == SUCCESS):
        #if(self.setVoltage(self.calibFactors[index]) == SUCCESS):
            print "User may now verify the measured voltage for data point : "+str(index)+"\n"
            return SUCCESS
        else:
            return FAIL

    def setVoltage(self, voltage_value):
        try:
            voltage_input = float(voltage_value)
        except:
            print "Invalid voltage value!\n"
            voltage_input = 0.0
            return FAIL
        timeout = TIMEOUT_INTERVAL
        voltage, timeout = libxsmu.VS_setVoltage (self.deviceID, voltage_input, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Voltage set : "+str(voltage_input)+" Volts \n"
        return SUCCESS

    def saveCalibration(self):
        """
        Save calibration to device
        """
        timeout = TIMEOUT_INTERVAL
        timeout = libxsmu.VM_saveCalibration (self.deviceID, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Calibration saved to device memory\n"
        return SUCCESS

    def loadDefaultCalibration(self):
        """
        Load default calibration from device
        """
        timeout = TIMEOUT_INTERVAL
        timeout = libxsmu.VM_loadDefaultCalibration (self.deviceID, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Default calibration loaded successfully\n"
        return SUCCESS

if __name__ == '__main__':
    root = Tk()
    calib_vm(root)
    root.mainloop()

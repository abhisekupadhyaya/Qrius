import functools, string
from Tkinter import *
import libxsmu
import app_calib_vs

VOLTAGE_UNITS            = [  1.0,    1.0]    #units in which voltage is measured for each range
VOLTAGE_FULL_SCALE_UNITS = [ 10.0,  100.0]
SCALING_FACTORS          = [ -1.0,   -0.1,   0.0,   0.1,   1.0]

PRECISION = 5
SUCCESS = 0
FAIL = 1
TIMEOUT_INTERVAL = 1.0

"""
Usage:
How to calibrate Voltage Source Module?
* From main menu select {\tt Utilities -> Calibration -> Voltage Source}
* On the Voltage Source Calibration Window:
    - Connect to XSMU module from the menu option {\tt File -> Connect Device}
    - Since each range has its specific calibration table,
      select a particular voltage source range which needs to be calibrated.
    - As the voltage range is selected, a five-point calibration table
      corresponding to that range is populated in the window.
    - On selecting any one of the calibration point, voltage calibration value stored
      inside the XSMU module is updated in the {\tt Actual Voltage} column.
    - The {\tt Actual Voltage} value can be modified to match against a reference voltage measurement
      device connected. Press {\tt Return} or {\tt Tab} key to register this modified value in the
      XSMU module memory.
    - Similarly, rest of the points in the calibration table can be modified.
    - Click {\tt Save Calibration Table} button to store the entire revised table in the XSMU module memory.
      Please ensure that before changing to a different voltage range, the presently modified table is
      saved, otherwise the modified values will be lost.
    - Click {\tt Load Default Calibration} button to load the default calibration settings from the XSMU module memory.

"""

def calib_vs(root):
    """
    Adds menubar to the main app. window
    """
    oAppCalibVS = app_calib_vs.app_calib_vs(root)
    oCalibVS = CalibVS(oAppCalibVS)
    return oCalibVS


class CalibVS:
    def __init__(self, oAppCalibVS = None):
        """
        Initialize module
        """
        self.deviceID = None
        self.dacValues = []
        self.actualVoltageValues = []
        self.voltageSourceRange = 0 #possible values: 0 and 1
        self.voltageSourceRangeLabel = app_calib_vs.VOLTAGE_RANGE_LABELS
        self.voltageUnitLabel = app_calib_vs.VOLTAGE_RANGE_UNIT_LABELS
        self.voltageUnit = VOLTAGE_UNITS
        self.timeout_occured = False
        if (oAppCalibVS != None):
            #if GUI is required
            self.oAppCalibVS = oAppCalibVS
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
        self.oAppCalibVS.filemenu.add_command(label='Connect to Device', underline=0, command=self.vConnectDeviceCB)
        for voltagerange in range(app_calib_vs.VOLTAGE_RANGE):
            self.oAppCalibVS.RBVSRange[voltagerange].config(command = functools.partial(self.vRBVSRangeCB,voltagerange))
        for channel in range(app_calib_vs.NO_OF_POINTS):
            self.oAppCalibVS.EntryVoltage[channel].bind('<Return>', functools.partial(self.vEntryVoltageCB,channel))
            self.oAppCalibVS.EntryVoltage[channel].bind('<Tab>', functools.partial(self.vEntryVoltageCB,channel))
            self.oAppCalibVS.EntryVoltage[channel].bind('<Key>', functools.partial(self.vClearHighlight,channel))
            self.oAppCalibVS.EntryVoltage[channel].bind('<Button-1>', functools.partial(self.vEntryVoltageOnFocus,channel))
            self.oAppCalibVS.RBEntry[channel].config(command = functools.partial(self.vRBEntryCB,channel))
        self.oAppCalibVS.RBEntry[0].bind('<Tab>', self.vRBEntryOnTab) #For consistency in tabbing
        self.oAppCalibVS.BtnSaveCalibTable.config(command = self.vBtnSaveCalibTableCB)
        self.oAppCalibVS.BtnLoadDefaultCalib.config(command = self.vBtnLoadDefaultCalibCB)
        self.oAppCalibVS.message.config(text = '')
        self.oAppCalibVS.EntryTestVoltage.bind('<Return>', self.vEntryTestVoltageCB)
        self.oAppCalibVS.EntryTestVoltage.bind('<Button-1>', self.vEntryTestVoltageOnFocus)
        return

    def vConnectDeviceCB(self):
        """
        Callback for Connect To Device Menu Entry
        """
        self.oAppCalibVS.filemenu.entryconfig(0,state = DISABLED)
        if (self.scanDevice() == SUCCESS):
            if (self.selectDevice() == SUCCESS):
                self.vEnableCalibration()
                self.entryModified = [0,0,0,0,0]
                self.oAppCalibVS.message.config(text = 'Communication Established.')
                self.vInvokeFirstRBVSRangeCB()
        else:
            self.vDeviceNotFound()
        return

    def vDisconnectDeviceCB(self):
        """
        Callback for Disconnect Device Menu Entry
        """
        self.oAppCalibVS.filemenu.entryconfig(0,state = DISABLED)
        self.deviceDisconnect()
        self.vDisableCalibration()
        self.oAppCalibVS.message.config(text = 'Device Disconnected.')
        return

    def vEntryTestVoltageCB(self, event=None):
        """
        Callback for Test Calibration Entry
        """
        try:
            self.oAppCalibVS.RBEntry[self.oAppCalibVS.data_point.get()].deselect()
        except:
            pass
        if(self.setVoltage(self.oAppCalibVS.EntryTestVoltage.get()) == FAIL):
            self.oAppCalibVS.TestVoltageValue.set(0.0)
        else:
            self.oAppCalibVS.message.config(text = 'Test Voltage Set.')
        self.vCheckTimeout()
        return

    def vEntryVoltageOnFocus(self, index, event=None):
        try:
            self.oAppCalibVS.data_point.get()
        except:
            self.oAppCalibVS.RBEntry[index].invoke()
        self.vCheckTimeout()
        return

    def vEntryTestVoltageOnFocus(self, event=None):
        try:
            self.oAppCalibVS.RBEntry[self.oAppCalibVS.data_point.get()].deselect()
        except:
            pass
        if(self.deviceID != None):
            #Update message only if device is turned on
            self.oAppCalibVS.message.config(text = 'Enter Test Voltage.')
        self.vCheckTimeout()
        return

    def vRBVSRangeCB(self,index):
        """
        Callback for Voltage Range Selector
        """
        if(len(self.dacValues)!=0):
            #If calibration table has already
            #been populated for some other range
            self.vConfirmation(index)
            return

        if (self.setVoltageSourceRange(index) == SUCCESS):
            self.oAppCalibVS.vUpdateVoltageUnit()
            if(self.getCalibration() == SUCCESS):
                self.vFillTable()
                self.vInvokeFirstRBEntryCB()
        self.vCheckTimeout()
        return

    def vInvokeFirstRBVSRangeCB(self):
        """
        """
        try:
            #All ranges are enabled
            lowest_range = min([_range  for _range in range(app_calib_vs.VOLTAGE_RANGE) if _range not in app_calib_vs.DISABLED_RANGE])
            self.oAppCalibVS.RBVSRange[lowest_range].invoke()
        except:
            pass
        return

    def vInvokeFirstRBEntryCB(self):
        """
        """
        try:
            self.oAppCalibVS.RBEntry[0].invoke()
        except:
            pass
        return

    def vEntryVoltageCB(self, index, event):
        """
        Callback after the voltage value has been entered
        """
        if(self.setCalibration(index,(self.oAppCalibVS.EntryVoltage[index].get())) == SUCCESS):
            self.oAppCalibVS.entryDACValues[index].set(self.dacValues[index])
            self.vHighlightVoltage(index)
            self.oAppCalibVS.message.config(text = 'Voltage Set.')
        else:
            self.oAppCalibVS.entryVoltageValues[index].set(0.0)
        if event.keysym=='Tab':
            if index < (app_calib_vs.NO_OF_POINTS - 1):
                self.oAppCalibVS.RBEntry[index+1].invoke()
        self.vCheckTimeout()
        return

    def vRBEntryCB(self,index):
        """
        Selects the point at which Calibration
        requires verification
        """
        self.oAppCalibVS.EntryVoltage[index].focus()
        if(self.verifyCalibration(index) == SUCCESS):
            self.oAppCalibVS.message.config(text = 'Verify Calibration at point ('+str(index)+')')
        self.vCheckTimeout()
        return

    def vRBEntryOnTab(self,event):
        '''
        On tabbing through the first data point it will be activated
        '''
        self.oAppCalibVS.RBEntry[0].invoke()
        return

    def vBtnSaveCalibTableCB(self):
        """
        Callback for Save Calibration button
        """
        for index in range(app_calib_vs.NO_OF_POINTS):
            try:
                float(self.oAppCalibVS.EntryVoltage[index].get())
            except:
                self.oAppCalibVS.message.config(text = 'Invalid Voltage Value!')
                return

        if(self.saveCalibration() == SUCCESS):
            self.oAppCalibVS.message.config(text = 'Calibration Saved.')
            self.entryModified = [0,0,0,0,0]
        self.vCheckTimeout()
        return

    def vBtnLoadDefaultCalibCB(self):
        """
        Callback for Load Calibration button
        """
        if(len(self.dacValues)!=0):
            #If calibration table has already been
            #populated for some other range
            self.vConfirmation()
            return

        if (self.loadDefaultCalibration() == SUCCESS):
            if (self.getCalibration() == SUCCESS):
                self.vFillTable()
                self.vInvokeFirstRBEntryCB()
                self.oAppCalibVS.message.config(text = 'Default Calibration Loaded.')
        self.vCheckTimeout()
        return

    def vHighlightVoltage(self, index):
        """
        Highlight entered voltage values
        """
        self.oAppCalibVS.EntryVoltage[index].configure(bg='yellow')
        self.entryModified[index] = 1
        return

    def vClearHighlight(self, index, event = None):
        """
        Clear highlight if entered voltage values are modified
        """
        self.oAppCalibVS.EntryVoltage[index].configure(bg='white')
        self.entryModified[index] = 0
        return

    def vEnableCalibration(self):
        """
        Enable calibration table widgets
        """
        self.oAppCalibVS.filemenu.entryconfig(0,command = self.vDisconnectDeviceCB,label='Disconnect Device')
        self.oAppCalibVS.filemenu.entryconfig(0,state = NORMAL)
        self.oAppCalibVS.vEnableVSRangeSelect()
        self.oAppCalibVS.vEnableCalibTable()
        self.oAppCalibVS.vEnableCalibTest()
        return

    def vDisableCalibration(self):
        """
        Disable calibration table widgets
        """
        self.oAppCalibVS.filemenu.entryconfig(0,command = self.vConnectDeviceCB,label='Connect To Device')
        self.oAppCalibVS.filemenu.entryconfig(0,state = NORMAL)
        self.oAppCalibVS.vDisableCalibTest()
        self.oAppCalibVS.vDisableCalibTable()
        self.oAppCalibVS.vDisableVSRangeSelect()
        return

    def vConfirmation(self, index = None):
        """
        Checks if entries have been modified
        """
        if(max(self.entryModified) == 0):
            self.dacValues = []
            self.actualVoltageValues = []
            if (index != None):
                self.oAppCalibVS.RBVSRange[index].invoke()
            else:
                self.oAppCalibVS.BtnLoadDefaultCalib.invoke()
            return
        else:
            if (self.oAppCalibVS.vConfimationPopup() == True):
                self.dacValues = []
                self.actualVoltageValues = []
                self.entryModified = [0,0,0,0,0]
                if (index != None):
                    self.oAppCalibVS.RBVSRange[index].invoke()
                else:
                    self.oAppCalibVS.BtnLoadDefaultCalib.invoke()
            else:
                self.oAppCalibVS.RBVSRange[self.voltageSourceRange].select()
            return

    def vDeviceNotFound(self):
        """
        Reset widget if device is not found
        """
        self.vDisableCalibration()
        self.oAppCalibVS.message.config(text = 'Device Not Found.')
        return

    def vCheckTimeout(self):
        """
        Check for connection timeout
        """
        if (self.timeout_occured == True):
            self.vDisableCalibration()
            self.oAppCalibVS.message.config(text = 'Communication Timeout!')
        return

    def vFillTable(self):
        """
        Fill the calibration table with the obtained dac and voltage values
        """
        for index in range(app_calib_vs.NO_OF_POINTS):
            self.oAppCalibVS.entryDACValues[index].set(self.dacValues[index])
            self.oAppCalibVS.entryVoltageValues[index].set(round(self.actualVoltageValues[index]/self.voltageUnit[self.voltageSourceRange],PRECISION))
            self.vClearHighlight(index)
        self.oAppCalibVS.vMakeDACreadonly()
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
        self.voltageSourceRange = 0
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
            self.dacValues = []
            self.actualVoltageValues = []
            self.voltageSourceRange = 0
            print 'Device Disconnected!\n'
            return SUCCESS
        else:
            print 'No Connection Present!\n'
            return FAIL

    def setVoltageSourceRange(self,voltage_range):
        """
        Set the voltage range near which calibration needs to be performed
        """
        timeout = TIMEOUT_INTERVAL
        voltageSourceRange, timeout = libxsmu.VS_setRange(self.deviceID, voltage_range, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        self.voltageSourceRange = voltage_range
        print "Voltage source range set at : "+str(self.voltageSourceRangeLabel[self.voltageSourceRange])+"\n"
        return SUCCESS

    def getCalibration(self):
        """
        Get the dac and voltage values from device at different points
        """
        for index in range(app_calib_vs.NO_OF_POINTS):
            timeout = TIMEOUT_INTERVAL
            i, dac, voltage, timeout = libxsmu.VS_getCalibration (self.deviceID, index, timeout)
            if (timeout == 0.0):
                self._vOnDeviceTimeout()
                return FAIL
            self.dacValues.append(dac)
            self.actualVoltageValues.append(voltage)
        print "DAC and voltage values obtained successfully : "
        print "Index | DAC Values | Actual Voltage ("+str(self.voltageUnitLabel[self.voltageSourceRange])+")"
        for index in range(app_calib_vs.NO_OF_POINTS):
            print '  '+string.rjust(str(index), 2)+'  | '+string.rjust(str(self.dacValues[index]),8)+'   | '+string.rjust(str(round((self.actualVoltageValues[index]/self.voltageUnit[self.voltageSourceRange]),PRECISION)),10)
        print "\n"
        return SUCCESS

    def setCalibration(self, index, voltage_value):
        """
        Use the entered Voltage value to set calibration at specified point(index)
        """
        try:
            voltage_input = float(voltage_value)*self.voltageUnit[self.voltageSourceRange]
        except:
            print "Invalid voltage value!\n"
            voltage_input = 0.0
            return FAIL
        timeout = TIMEOUT_INTERVAL
        i, dac, voltage, timeout = libxsmu.VS_setCalibration(self.deviceID, index, voltage_input, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        self.dacValues[index] = dac
        self.actualVoltageValues[index] = voltage_input
        print 'Voltage Calibration Set : '+str(round((self.actualVoltageValues[index]/self.voltageUnit[self.voltageSourceRange]),PRECISION))+str(self.voltageUnitLabel[self.voltageSourceRange])+' at data point '+str(index)+"\n"
        return SUCCESS

    def verifyCalibration(self, index):
        """
        Verify calibration at specified point(index)
        """
        timeout = TIMEOUT_INTERVAL
        i, dac, voltage, timeout = libxsmu.VS_verifyCalibration (self.deviceID, index, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "User may now verify the voltage calibration for data point : "+str(index)+"\n"
        return SUCCESS

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
        print "Voltage set : "+str(voltage_input)+" Volts"
        return SUCCESS

    def saveCalibration(self):
        """
        Save calibration to device
        """
        timeout = TIMEOUT_INTERVAL
        timeout = libxsmu.VS_saveCalibration (self.deviceID, timeout)
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
        timeout = libxsmu.VS_loadDefaultCalibration (self.deviceID, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Default calibration loaded successfully\n"
        return SUCCESS

if __name__ == '__main__':
    root = Tk()
    calib_vs(root)
    root.mainloop()

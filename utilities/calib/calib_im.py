import functools, string
from Tkinter import *
import libxsmu
import app_calib_im

CURRENT_UNITS            = [ 1e-6,  1e-6,  1e-3,  1e-3,  1e-3]    #units in which current is measured for each range
CURRENT_FULL_SCALE_UNITS = [ 1e-5,  1e-4,  1e-3,  1e-2,  1e-1]
SCALING_FACTORS          = [ -1.0,  -0.9,   0.0,   0.9,   1.0]

PRECISION = 5
SUCCESS = 0
FAIL = 1
TIMEOUT_INTERVAL = 1.0

"""
Usage:
How to calibrate Current Measurement Module?
* From main menu select {\tt Utilities -> Calibration -> Current Measure}
* On the Current Measure Calibration Window:
    - Connect to XSMU module from the menu option {\tt File -> Connect Device}
    - Since each range has its specific calibration table,
      select a particular current measurement range which needs to be calibrated.
    - As the current range is selected, a five-point calibration table
      corresponding to that range is populated in the window.
    - On selecting any one of the calibration point, current calibration value stored
      inside the XSMU module is updated in the {\tt Measured Current} column.
    - The {\tt Measured Current} value can be modified to match against a reference current measurement
      device connected. Press {\tt Return} or {\tt Tab} key to register this modified value in the
      XSMU module memory.
    - Similarly, rest of the points in the calibration table can be modified.
    - Click {\tt Save Calibration Table} button to store the entire revised table in the XSMU module memory.
      Please ensure that before changing to a different current range, the presently modified table is
      saved, otherwise the modified values will be lost.
    - Click {\tt Load Default Calibration} button to load the default calibration settings from the XSMU module memory.

"""

def calib_im(root):
    """
    Adds menubar to the main app. window
    """
    oAppCalibIM = app_calib_im.app_calib_im(root)
    oCalibIM = CalibIM(oAppCalibIM)
    return oCalibIM


class CalibIM:
    def __init__(self, oAppCalibIM = None):
        """
        Initialize module
        """
        self.deviceID = None
        self.adcValues = []
        self.actualCurrentValues = []
        self.currentMeasureRange = 0 #possible values: (0,) 1, 2, 3 (and 4)
        self.currentMeasureRangeLabel = app_calib_im.CURRENT_RANGE_LABELS
        self.currentUnitLabel = app_calib_im.CURRENT_RANGE_UNIT_LABELS
        self.currentUnit = CURRENT_UNITS
        self.calibFactors = [[val1*val2 for val1 in CURRENT_FULL_SCALE_UNITS] for val2 in SCALING_FACTORS]
        self.timeout_occured = False
        if (oAppCalibIM != None):
            #if GUI is required
            self.oAppCalibIM = oAppCalibIM
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
        self.oAppCalibIM.filemenu.add_command(label='Connect to Device', underline=0, command=self.vConnectDeviceCB)
        for currentrange in range(app_calib_im.CURRENT_RANGE):
            self.oAppCalibIM.RBCMRange[currentrange].config(command = functools.partial(self.vRBCMRangeCB,currentrange))
        for channel in range(app_calib_im.NO_OF_POINTS):
            self.oAppCalibIM.EntryCurrent[channel].bind('<Return>', functools.partial(self.vEntryCurrentCB,channel))
            self.oAppCalibIM.EntryCurrent[channel].bind('<Tab>', functools.partial(self.vEntryCurrentCB,channel))
            self.oAppCalibIM.EntryCurrent[channel].bind('<Key>', functools.partial(self.vClearHighlight,channel))
            self.oAppCalibIM.EntryCurrent[channel].bind('<Button-1>', functools.partial(self.vEntryCurrentOnFocus,channel))
            self.oAppCalibIM.RBEntry[channel].config(command = functools.partial(self.vRBEntryCB,channel))
        self.oAppCalibIM.RBEntry[0].bind('<Tab>', self.vRBEntryOnTab) #For consistency in tabbing
        self.oAppCalibIM.BtnSaveCalibTable.config(command = self.vBtnSaveCalibTableCB)
        self.oAppCalibIM.BtnLoadDefaultCalib.config(command = self.vBtnLoadDefaultCalibCB)
        self.oAppCalibIM.message.config(text = '')
        self.oAppCalibIM.EntryTestCurrent.bind('<Return>', self.vEntryTestCurrentCB)
        self.oAppCalibIM.EntryTestCurrent.bind('<Button-1>', self.vEntryTestCurrentOnFocus)
        return

    def vConnectDeviceCB(self):
        """
        Callback for Connect To Device Menu Entry
        """
        self.oAppCalibIM.filemenu.entryconfig(0,state = DISABLED)
        if (self.scanDevice() == SUCCESS):
            if (self.selectDevice() == SUCCESS):
                self.vEnableCalibration()
                self.entryModified = [0,0,0,0,0]
                self.oAppCalibIM.message.config(text = 'Communication Established.')
                self.vInvokeFirstRBCMRangeCB()
        else:
            self.vDeviceNotFound()
        return

    def vDisconnectDeviceCB(self):
        """
        Callback for Disconnect Device Menu Entry
        """
        self.oAppCalibIM.filemenu.entryconfig(0,state = DISABLED)
        self.deviceDisconnect()
        self.vDisableCalibration()
        self.oAppCalibIM.message.config(text = 'Device Disconnected.')
        return

    def vEntryTestCurrentCB(self, event=None):
        """
        Callback for Test Calibration Entry
        """
        try:
            self.oAppCalibIM.RBEntry[self.oAppCalibIM.data_point.get()].deselect()
        except:
            pass
        if(self.setCurrent(self.oAppCalibIM.EntryTestCurrent.get()) == FAIL):
            self.oAppCalibIM.TestCurrentValue.set(0.0)
        else:
            self.oAppCalibIM.message.config(text = 'Test Current Set.')
        self.vCheckTimeout()
        return

    def vEntryTestCurrentOnFocus(self, event=None):
        try:
            self.oAppCalibIM.RBEntry[self.oAppCalibIM.data_point.get()].deselect()
        except:
            pass
        if(self.deviceID != None):
            #Update message only if device is turned on
            self.oAppCalibIM.message.config(text = 'Enter Test Current.')
        self.vCheckTimeout()
        return

    def vEntryCurrentOnFocus(self, index, event=None):
        try:
            self.oAppCalibIM.data_point.get()
        except:
            self.oAppCalibIM.RBEntry[index].invoke()
        self.vCheckTimeout()
        return

    def vRBCMRangeCB(self,index):
        """
        Callback for Current Range Selector
        """
        if(len(self.adcValues)!=0):
            #If calibration table has already
            #been populated for some other range
            self.vConfirmation(index)
            return

        if (self.setCurrentMeasureRange(index) == SUCCESS):
            self.oAppCalibIM.vUpdateCurrentUnit()
            if(self.getCalibration() == SUCCESS):
                self.vFillTable()
                self.vInvokeFirstRBEntryCB()
        self.vCheckTimeout()
        return

    def vInvokeFirstRBCMRangeCB(self):
        """
        """
        try:
            #10uA and 100mA ranges are disabled
            lowest_range = min([_range  for _range in range(app_calib_im.CURRENT_RANGE) if _range not in app_calib_im.DISABLED_RANGE])
            self.oAppCalibIM.RBCMRange[lowest_range].invoke()
        except:
            pass
        return

    def vInvokeFirstRBEntryCB(self):
        """
        """
        try:
            self.oAppCalibIM.RBEntry[0].invoke()
        except:
            pass
        return

    def vEntryCurrentCB(self, index, event):
        """
        Callback after the current value has been entered
        """
        if(self.setCalibration(index,(self.oAppCalibIM.EntryCurrent[index].get())) == SUCCESS):
            self.oAppCalibIM.entryADCValues[index].set(self.adcValues[index])
            self.vHighlightCurrent(index)
            self.oAppCalibIM.message.config(text = 'Current Set.')
        else:
            self.oAppCalibIM.entryCurrentValues[index].set(0.0)
        if event.keysym=='Tab':
            if index < (app_calib_im.NO_OF_POINTS - 1):
                self.oAppCalibIM.RBEntry[index+1].invoke()
        self.vCheckTimeout()
        return

    def vRBEntryCB(self,index):
        """
        Selects the point at which Calibration
        requires verification
        """
        self.oAppCalibIM.EntryCurrent[index].focus()
        if(self.setCurrentAtIndex(index) == SUCCESS):
            self.oAppCalibIM.message.config(text = 'Measure current at point ('+str(index)+')')
        self.vCheckTimeout()
        return

    def vRBEntryOnTab(self,event):
        '''
        On tabbing through the first data point it will be activated
        '''
        self.oAppCalibIM.RBEntry[0].invoke()
        return

    def vBtnSaveCalibTableCB(self):
        """
        Callback for Save Calibration button
        """
        for index in range(app_calib_im.NO_OF_POINTS):
            try:
                float(self.oAppCalibIM.EntryCurrent[index].get())
            except:
                self.oAppCalibIM.message.config(text = 'Invalid Current Value!')
                return

        if(self.saveCalibration() == SUCCESS):
            self.oAppCalibIM.message.config(text = 'Calibration Saved.')
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
                self.oAppCalibIM.message.config(text = 'Default Calibration Loaded.')
        self.vCheckTimeout()
        return

    def vHighlightCurrent(self, index):
        """
        Highlight entered current values
        """
        self.oAppCalibIM.EntryCurrent[index].configure(bg='yellow')
        self.entryModified[index] = 1
        return

    def vClearHighlight(self, index, event = None):
        """
        Clear highlight if entered current values are modified
        """
        self.oAppCalibIM.EntryCurrent[index].configure(bg='white')
        self.entryModified[index] = 0
        return

    def vEnableCalibration(self):
        """
        Enable calibration table widgets
        """
        self.oAppCalibIM.filemenu.entryconfig(0,command = self.vDisconnectDeviceCB,label='Disconnect Device')
        self.oAppCalibIM.filemenu.entryconfig(0,state = NORMAL)
        self.oAppCalibIM.vEnableCMRangeSelect()
        self.oAppCalibIM.vEnableCalibTable()
        self.oAppCalibIM.vEnableCalibTest()
        return

    def vDisableCalibration(self):
        """
        Disable calibration table widgets
        """
        self.oAppCalibIM.filemenu.entryconfig(0,command = self.vConnectDeviceCB,label='Connect To Device')
        self.oAppCalibIM.filemenu.entryconfig(0,state = NORMAL)
        self.oAppCalibIM.vDisableCalibTest()
        self.oAppCalibIM.vDisableCalibTable()
        self.oAppCalibIM.vDisableCMRangeSelect()
        return

    def vConfirmation(self, index = None):
        """
        Checks if entries have been modified
        """
        if(max(self.entryModified) == 0):
            self.adcValues = []
            self.actualCurrentValues = []
            if (index != None):
                self.oAppCalibIM.RBCMRange[index].invoke()
            else:
                self.oAppCalibIM.BtnLoadDefaultCalib.invoke()
            return
        else:
            if (self.oAppCalibIM.vConfimationPopup() == True):
                self.adcValues = []
                self.actualCurrentValues = []
                self.entryModified = [0,0,0,0,0]
                if (index != None):
                    self.oAppCalibIM.RBCMRange[index].invoke()
                else:
                    self.oAppCalibIM.BtnLoadDefaultCalib.invoke()
            else:
                self.oAppCalibIM.RBCMRange[self.currentMeasureRange].select()
            return

    def vDeviceNotFound(self):
        """
        Reset widget if device is not found
        """
        self.vDisableCalibration()
        self.oAppCalibIM.message.config(text = 'Device Not Found.')
        return

    def vCheckTimeout(self):
        """
        Check for connection timeout
        """
        if (self.timeout_occured == True):
            self.vDisableCalibration()
            self.oAppCalibIM.message.config(text = 'Communication Timeout!')
        return

    def vFillTable(self):
        """
        Fill the calibration table with the obtained adc and current values
        """
        for index in range(app_calib_im.NO_OF_POINTS):
            self.oAppCalibIM.entryADCValues[index].set(self.adcValues[index])
            self.oAppCalibIM.entryCurrentValues[index].set(round(self.actualCurrentValues[index]/self.currentUnit[self.currentMeasureRange],PRECISION))
            self.vClearHighlight(index)
        self.oAppCalibIM.vMakeADCreadonly()
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
        self.sourceMode, timeout = libxsmu.setSourceMode (self.deviceID, 0, timeout)#Set to current source mode
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Source Mode set to : Current Source\n"
        self.currentMeasureRange = 0
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
            self.actualCurrentValues = []
            self.currentMeasureRange = 0
            print 'Device Disconnected!\n'
            return SUCCESS
        else:
            print 'No Connection Present!\n'
            return FAIL

    def setCurrentMeasureRange(self,current_range):
        """
        Set the current range near which calibration needs to be performed
        """
        timeout = TIMEOUT_INTERVAL
        currentMeasureRange, timeout = libxsmu.CM_setRange(self.deviceID, current_range, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        self.currentMeasureRange = current_range
        print "Current measure range set at : "+str(self.currentMeasureRangeLabel[self.currentMeasureRange])+"\n"
        return SUCCESS

    def getCalibration(self):
        """
        Get the adc and current values from device at different points
        """
        for index in range(app_calib_im.NO_OF_POINTS):
            timeout = TIMEOUT_INTERVAL
            i, adc, current, timeout = libxsmu.CM_getCalibration (self.deviceID, index, timeout)
            if (timeout == 0.0):
                self._vOnDeviceTimeout()
                return FAIL
            self.adcValues.append(adc)
            self.actualCurrentValues.append(current)
        print "ADC and current values obtained successfully : "
        print "Index | ADC Values | Actual Current ("+str(self.currentUnitLabel[self.currentMeasureRange])+")"
        for index in range(app_calib_im.NO_OF_POINTS):
            print '  '+string.rjust(str(index), 2)+'  | '+string.rjust(str(self.adcValues[index]),8)+'   | '+string.rjust(str(round((self.actualCurrentValues[index]/self.currentUnit[self.currentMeasureRange]),PRECISION)),10)
        print "\n"
        return SUCCESS

    def setCalibration(self, index, current_value):
        """
        Use the entered Current value to set calibration at specified point(index)
        """
        try:
            current_input = float(current_value)*self.currentUnit[self.currentMeasureRange]
        except:
            print "Invalid current value!\n"
            current_input = 0.0
            return FAIL

        if (libxsmu.firmware_version (self.deviceID)
                  >= libxsmu.make_version (2, 2, 0)):
            timeout = 10 * TIMEOUT_INTERVAL
        else:
            timeout = TIMEOUT_INTERVAL

        i, adc, current, timeout = libxsmu.CM_setCalibration(self.deviceID, index, current_input, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        self.adcValues[index] = adc
        self.actualCurrentValues[index] = current_input
        print 'Current Calibration Set : '+str(round((self.actualCurrentValues[index]/self.currentUnit[self.currentMeasureRange]),PRECISION))+str(self.currentUnitLabel[self.currentMeasureRange])+' at data point '+str(index)+"\n"
        return SUCCESS

    def setCurrentAtIndex(self, index):
        """
        Set current at specified point(index)
        """
        if(self.setCurrent(self.calibFactors[index][self.currentMeasureRange]) == SUCCESS):
            print "User may now verify the measured current for data point : "+str(index)+"\n"
            return SUCCESS
        else:
            return FAIL

    def setCurrent(self, current_value):
        try:
            current_input = float(current_value)
        except:
            print "Invalid current value!\n"
            current_input = 0.0
            return FAIL
        timeout = TIMEOUT_INTERVAL
        current, timeout = libxsmu.CS_setCurrent (self.deviceID, current_input, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Current set : "+str(current_input)+" Ampere \n"
        return SUCCESS

    def saveCalibration(self):
        """
        Save calibration to device
        """
        timeout = TIMEOUT_INTERVAL
        timeout = libxsmu.CM_saveCalibration (self.deviceID, timeout)
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
        timeout = libxsmu.CM_loadDefaultCalibration (self.deviceID, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Default calibration loaded successfully\n"
        return SUCCESS

if __name__ == '__main__':
    root = Tk()
    calib_im(root)
    root.mainloop()

import functools, string
from Tkinter import *
import libxsmu
import app_calib_is

CURRENT_UNITS            = [ 1e-6,  1e-6,  1e-3,  1e-3,  1e-3]    #units in which current is measured for each range
CURRENT_FULL_SCALE_UNITS = [ 1e-5,  1e-4,  1e-3,  1e-2,  1e-1]
SCALING_FACTORS          = [ -1.0,  -0.1,   0.0,   0.1,   1.0]

PRECISION = 5
SUCCESS = 0
FAIL = 1
TIMEOUT_INTERVAL = 1.0

"""
Usage:
How to calibrate Current Source Module?
* From main menu select {\tt Utilities -> Calibration -> Current Source}
* On the Current Source Calibration Window:
    - Connect to XSMU module from the menu option {\tt File -> Connect Device}
    - Since each range has its specific calibration table,
      select a particular current source range which needs to be calibrated.
    - As the current range is selected, a five-point calibration table
      corresponding to that range is populated in the window.
    - On selecting any one of the calibration point, current calibration value stored
      inside the XSMU module is updated in the {\tt Actual Current} column.
    - The {\tt Actual Current} value can be modified to match against a reference current measurement
      device connected. Press {\tt Return} or {\tt Tab} key to register this modified value in the
      XSMU module memory.
    - Similarly, rest of the points in the calibration table can be modified.
    - Click {\tt Save Calibration Table} button to store the entire revised table in the XSMU module memory.
      Please ensure that before changing to a different current range, the presently modified table is
      saved, otherwise the modified values will be lost.
    - Click {\tt Load Default Calibration} button to load the default calibration settings from the XSMU module memory.

"""

def calib_is(root):
    """
    Adds menubar to the main app. window
    """
    oAppCalibIS = app_calib_is.app_calib_is(root)
    oCalibIS = CalibIS(oAppCalibIS)
    return oCalibIS


class CalibIS:
    def __init__(self, oAppCalibIS = None):
        """
        Initialize module
        """
        self.deviceID = None
        self.dacValues = []
        self.actualCurrentValues = []
        self.currentSourceRange = 0 #possible values: (0,) 1, 2, 3 (and 4)
        self.currentSourceRangeLabel = app_calib_is.CURRENT_RANGE_LABELS
        self.currentUnitLabel = app_calib_is.CURRENT_RANGE_UNIT_LABELS
        self.currentUnit = CURRENT_UNITS
        self.timeout_occured = False
        if (oAppCalibIS != None):
            #if GUI is required
            self.oAppCalibIS = oAppCalibIS
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
        self.oAppCalibIS.filemenu.add_command(label='Connect to Device', underline=0, command=self.vConnectDeviceCB)
        for currentrange in range(app_calib_is.CURRENT_RANGE):
            self.oAppCalibIS.RBCSRange[currentrange].config(command = functools.partial(self.vRBCSRangeCB,currentrange))
        for channel in range(app_calib_is.NO_OF_POINTS):
            self.oAppCalibIS.EntryCurrent[channel].bind('<Return>', functools.partial(self.vEntryCurrentCB,channel))
            self.oAppCalibIS.EntryCurrent[channel].bind('<Tab>', functools.partial(self.vEntryCurrentCB,channel))
            self.oAppCalibIS.EntryCurrent[channel].bind('<Key>', functools.partial(self.vClearHighlight,channel))
            self.oAppCalibIS.EntryCurrent[channel].bind('<Button-1>', functools.partial(self.vEntryCurrentOnFocus,channel))
            self.oAppCalibIS.RBEntry[channel].config(command = functools.partial(self.vRBEntryCB,channel))
        self.oAppCalibIS.RBEntry[0].bind('<Tab>', self.vRBEntryOnTab) #For consistency in tabbing
        self.oAppCalibIS.BtnSaveCalibTable.config(command = self.vBtnSaveCalibTableCB)
        self.oAppCalibIS.BtnLoadDefaultCalib.config(command = self.vBtnLoadDefaultCalibCB)
        self.oAppCalibIS.message.config(text = '')
        self.oAppCalibIS.EntryTestCurrent.bind('<Return>', self.vEntryTestCurrentCB)
        self.oAppCalibIS.EntryTestCurrent.bind('<Button-1>', self.vEntryTestCurrentOnFocus)
        return

    def vConnectDeviceCB(self):
        """
        Callback for Connect To Device Menu Entry
        """
        self.oAppCalibIS.filemenu.entryconfig(0,state = DISABLED)
        if (self.scanDevice() == SUCCESS):
            if (self.selectDevice() == SUCCESS):
                self.vEnableCalibration()
                self.entryModified = [0,0,0,0,0]
                self.oAppCalibIS.message.config(text = 'Communication Established.')
                self.vInvokeFirstRBCSRangeCB()
        else:
            self.vDeviceNotFound()
        return

    def vDisconnectDeviceCB(self):
        """
        Callback for Disconnect Device Menu Entry
        """
        self.oAppCalibIS.filemenu.entryconfig(0,state = DISABLED)
        self.deviceDisconnect()
        self.vDisableCalibration()
        self.oAppCalibIS.message.config(text = 'Device Disconnected.')
        return

    def vEntryTestCurrentCB(self, event=None):
        """
        Callback for Test Calibration Entry
        """
        try:
            self.oAppCalibIS.RBEntry[self.oAppCalibIS.data_point.get()].deselect()
        except:
            pass
        if(self.setCurrent(self.oAppCalibIS.EntryTestCurrent.get()) == FAIL):
            self.oAppCalibIS.TestCurrentValue.set(0.0)
        else:
            self.oAppCalibIS.message.config(text = 'Test Current Set.')
        self.vCheckTimeout()
        return

    def vEntryTestCurrentOnFocus(self, event=None):
        try:
            self.oAppCalibIS.RBEntry[self.oAppCalibIS.data_point.get()].deselect()
        except:
            pass
        if(self.deviceID != None):
            #Update message only if device is turned on
            self.oAppCalibIS.message.config(text = 'Enter Test Current.')
        self.vCheckTimeout()
        return

    def vEntryCurrentOnFocus(self, index, event=None):
        try:
            self.oAppCalibIS.data_point.get()
        except:
            self.oAppCalibIS.RBEntry[index].invoke()
        self.vCheckTimeout()
        return

    def vRBCSRangeCB(self,index):
        """
        Callback for Current Range Selector
        """
        if(len(self.dacValues)!=0):
            #If calibration table has already
            #been populated for some other range
            self.vConfirmation(index)
            return

        if (self.setCurrentSourceRange(index) == SUCCESS):
            self.oAppCalibIS.vUpdateCurrentUnit()
            if(self.getCalibration() == SUCCESS):
                self.vFillTable()
                self.vInvokeFirstRBEntryCB()
        self.vCheckTimeout()
        return

    def vInvokeFirstRBCSRangeCB(self):
        """
        """
        try:
            #10uA and 100mA ranges are disabled
            lowest_range = min([_range  for _range in range(app_calib_is.CURRENT_RANGE) if _range not in app_calib_is.DISABLED_RANGE])
            self.oAppCalibIS.RBCSRange[lowest_range].invoke()
        except:
            pass
        return

    def vInvokeFirstRBEntryCB(self):
        """
        """
        try:
            self.oAppCalibIS.RBEntry[0].invoke()
        except:
            pass
        return

    def vEntryCurrentCB(self, index, event):
        """
        Callback after the current value has been entered
        """
        if(self.setCalibration(index,(self.oAppCalibIS.EntryCurrent[index].get())) == SUCCESS):
            self.oAppCalibIS.entryDACValues[index].set(self.dacValues[index])
            self.vHighlightCurrent(index)
            self.oAppCalibIS.message.config(text = 'Current Set.')
        else:
            self.oAppCalibIS.entryCurrentValues[index].set(0.0)
        if event.keysym=='Tab':
            if index < (app_calib_is.NO_OF_POINTS - 1):
                self.oAppCalibIS.RBEntry[index+1].invoke()
        self.vCheckTimeout()
        return

    def vRBEntryCB(self,index):
        """
        Selects the point at which Calibration
        requires verification
        """
        self.oAppCalibIS.EntryCurrent[index].focus()
        if(self.verifyCalibration(index) == SUCCESS):
            self.oAppCalibIS.message.config(text = 'Verify Calibration at point ('+str(index)+')')
        self.vCheckTimeout()
        return

    def vRBEntryOnTab(self,event):
        '''
        On tabbing through the first data point it will be activated
        '''
        self.oAppCalibIS.RBEntry[0].invoke()
        return

    def vBtnSaveCalibTableCB(self):
        """
        Callback for Save Calibration button
        """
        for index in range(app_calib_is.NO_OF_POINTS):
            try:
                float(self.oAppCalibIS.EntryCurrent[index].get())
            except:
                self.oAppCalibIS.message.config(text = 'Invalid Current Value!')
                return

        if(self.saveCalibration() == SUCCESS):
            self.oAppCalibIS.message.config(text = 'Calibration Saved.')
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
                self.oAppCalibIS.message.config(text = 'Default Calibration Loaded.')
        self.vCheckTimeout()
        return

    def vHighlightCurrent(self, index):
        """
        Highlight entered current values
        """
        self.oAppCalibIS.EntryCurrent[index].configure(bg='yellow')
        self.entryModified[index] = 1
        return

    def vClearHighlight(self, index, event = None):
        """
        Clear highlight if entered current values are modified
        """
        self.oAppCalibIS.EntryCurrent[index].configure(bg='white')
        self.entryModified[index] = 0
        return

    def vEnableCalibration(self):
        """
        Enable calibration table widgets
        """
        self.oAppCalibIS.filemenu.entryconfig(0,command = self.vDisconnectDeviceCB,label='Disconnect Device')
        self.oAppCalibIS.filemenu.entryconfig(0,state = NORMAL)
        self.oAppCalibIS.vEnableCSRangeSelect()
        self.oAppCalibIS.vEnableCalibTable()
        self.oAppCalibIS.vEnableCalibTest()
        return

    def vDisableCalibration(self):
        """
        Disable calibration table widgets
        """
        self.oAppCalibIS.filemenu.entryconfig(0,command = self.vConnectDeviceCB,label='Connect To Device')
        self.oAppCalibIS.filemenu.entryconfig(0,state = NORMAL)
        self.oAppCalibIS.vDisableCalibTest()
        self.oAppCalibIS.vDisableCalibTable()
        self.oAppCalibIS.vDisableCSRangeSelect()
        return

    def vConfirmation(self, index = None):
        """
        Checks if entries have been modified
        """
        if(max(self.entryModified) == 0):
            self.dacValues = []
            self.actualCurrentValues = []
            if (index != None):
                self.oAppCalibIS.RBCSRange[index].invoke()
            else:
                self.oAppCalibIS.BtnLoadDefaultCalib.invoke()
            return
        else:
            if (self.oAppCalibIS.vConfimationPopup() == True):
                self.dacValues = []
                self.actualCurrentValues = []
                self.entryModified = [0,0,0,0,0]
                if (index != None):
                    self.oAppCalibIS.RBCSRange[index].invoke()
                else:
                    self.oAppCalibIS.BtnLoadDefaultCalib.invoke()
            else:
                self.oAppCalibIS.RBCSRange[self.currentSourceRange].select()
            return

    def vDeviceNotFound(self):
        """
        Reset widget if device is not found
        """
        self.vDisableCalibration()
        self.oAppCalibIS.message.config(text = 'Device Not Found.')
        return

    def vCheckTimeout(self):
        """
        Check for connection timeout
        """
        if (self.timeout_occured == True):
            self.vDisableCalibration()
            self.oAppCalibIS.message.config(text = 'Communication Timeout!')
        return

    def vFillTable(self):
        """
        Fill the calibration table with the obtained dac and current values
        """
        for index in range(app_calib_is.NO_OF_POINTS):
            self.oAppCalibIS.entryDACValues[index].set(self.dacValues[index])
            self.oAppCalibIS.entryCurrentValues[index].set(round(self.actualCurrentValues[index]/self.currentUnit[self.currentSourceRange],PRECISION))
            self.vClearHighlight(index)
        self.oAppCalibIS.vMakeDACreadonly()
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
        self.currentSourceRange = 0
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
            self.actualCurrentValues = []
            self.currentSourceRange = 0
            print 'Device Disconnected!\n'
            return SUCCESS
        else:
            print 'No Connection Present!\n'
            return FAIL

    def setCurrentSourceRange(self,current_range):
        """
        Set the current range near which calibration needs to be performed
        """
        timeout = TIMEOUT_INTERVAL
        currentSourceRange, timeout = libxsmu.CS_setRange(self.deviceID, current_range, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        self.currentSourceRange = current_range
        print "Current source range set at : "+str(self.currentSourceRangeLabel[self.currentSourceRange])+"\n"
        return SUCCESS

    def getCalibration(self):
        """
        Get the dac and current values from device at different points
        """
        for index in range(app_calib_is.NO_OF_POINTS):
            timeout = TIMEOUT_INTERVAL
            i, dac, current, timeout = libxsmu.CS_getCalibration (self.deviceID, index, timeout)
            if (timeout == 0.0):
                self._vOnDeviceTimeout()
                return FAIL
            self.dacValues.append(dac)
            self.actualCurrentValues.append(current)
        print "DAC and current values obtained successfully : "
        print "Index | DAC Values | Actual Current ("+str(self.currentUnitLabel[self.currentSourceRange])+")"
        for index in range(app_calib_is.NO_OF_POINTS):
            print '  '+string.rjust(str(index), 2)+'  | '+string.rjust(str(self.dacValues[index]),8)+'   | '+string.rjust(str(round((self.actualCurrentValues[index]/self.currentUnit[self.currentSourceRange]),PRECISION)),10)
        print "\n"
        return SUCCESS

    def setCalibration(self, index, current_value):
        """
        Use the entered Current value to set calibration at specified point(index)
        """
        try:
            current_input = float(current_value)*self.currentUnit[self.currentSourceRange]
        except:
            print "Invalid current value!\n"
            current_input = 0.0
            return FAIL
        timeout = TIMEOUT_INTERVAL
        i, dac, current, timeout = libxsmu.CS_setCalibration(self.deviceID, index, current_input, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        self.dacValues[index] = dac
        self.actualCurrentValues[index] = current_input
        print 'Current Calibration Set : '+str(round((self.actualCurrentValues[index]/self.currentUnit[self.currentSourceRange]),PRECISION))+str(self.currentUnitLabel[self.currentSourceRange])+' at data point '+str(index)+"\n"
        return SUCCESS

    def verifyCalibration(self, index):
        """
        Verify calibration at specified point(index)
        """
        timeout = TIMEOUT_INTERVAL
        i, dac, current, timeout = libxsmu.CS_verifyCalibration (self.deviceID, index, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "User may now verify the current calibration for data point : "+str(index)+"\n"
        return SUCCESS

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
        print "Current set : "+str(current_input)+" Ampere"
        return SUCCESS

    def saveCalibration(self):
        """
        Save calibration to device
        """
        timeout = TIMEOUT_INTERVAL
        timeout = libxsmu.CS_saveCalibration (self.deviceID, timeout)
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
        timeout = libxsmu.CS_loadDefaultCalibration (self.deviceID, timeout)
        if (timeout == 0.0):
            self._vOnDeviceTimeout()
            return FAIL
        print "Default calibration loaded successfully\n"
        return SUCCESS

if __name__ == '__main__':
    root = Tk()
    calib_is(root)
    root.mainloop()

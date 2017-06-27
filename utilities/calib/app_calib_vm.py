from Tkinter import *
import tkMessageBox

#menu_font_type = ("Verdana", 12, 'normal')	# font description
menu_font_type = ("Helvetica", 11, 'normal')	# font description

VOLTAGE_RANGE              = 6
VOLTAGE_RANGE_LABELS       = ['1mV', '10mV', '100mV', '1V', '10V', '100V']
VOLTAGE_RANGE_UNIT_LABELS  = [ 'mV',   'mV',    'mV',  'V',   'V',    'V']
DISABLED_RANGE             = [    0,      1]
NO_OF_POINTS               = 5

def app_calib_vm(master):
    oAppCalibVM = AppCalibVM(master)
    return oAppCalibVM

class AppCalibVM:
    def __init__(self, master):
        self.master = master
        self.master.title('Voltage Measure Calibration')
        self.VMRange = VOLTAGE_RANGE_LABELS
        self.VoltageUnit = VOLTAGE_RANGE_UNIT_LABELS
        self.RBVMRange = []
        self.EntryADC = []
        self.RBEntry = []
        self.EntryVoltage = []
        self.Frames = []
        self.entryADCValues = []
        self.entryVoltageValues = []
        self.Voltage_labels = []
        self.VMRange_selected = IntVar()
        self.data_point = IntVar()
        self._vCreateWidgets()
        self.vDisableVMRangeSelect()
        self.vDisableCalibTable()
        return

        return

    def _vCreateWidgets(self):

        self.mainmenu = Menu(self.master, font=menu_font_type)
        self.mainmenu.config(borderwidth=1)
        self.master.config(menu=self.mainmenu)

        self.filemenu = Menu(self.mainmenu, font=menu_font_type)
        self.filemenu.config(tearoff=0)
        self.mainmenu.add_cascade(label='File', menu=self.filemenu, underline=0)

        self.Frames.append(LabelFrame(self.master,text='Test Calibration'))
        self.Frames[0].grid(row=0,column=0,sticky=N+E+W+S)
        Label(self.Frames[0], text='Test Voltage (V) :', justify=CENTER, fg='blue').grid(row=0,column=0)
        self.TestVoltageValue = DoubleVar()
        self.EntryTestVoltage = Entry(self.Frames[0], bg='white', justify=LEFT, width=12, textvariable=self.TestVoltageValue)
        self.EntryTestVoltage.grid(row=0,column=1,sticky=N+E+W+S,pady=5)
        self.EntryTestVoltage.config(state = DISABLED)

        self.Frames.append(LabelFrame(self.master,text='Voltage Range'))
        self.Frames[1].grid(row=1,column=0,sticky=N+E+W+S)

        max_columns = 2
        max_rows = (VOLTAGE_RANGE/max_columns) + (VOLTAGE_RANGE%max_columns)
        max_range = VOLTAGE_RANGE
        column_separation_length = 8
        shift = 0

        for rows in range(max_rows):
            for columns in range(max_columns):
                if (rows*max_columns + columns <= max_range-1):
                    self.RBVMRange.append(Radiobutton(self.Frames[1],variable = self.VMRange_selected,value=(columns + rows*max_columns)))
                    if ((columns + rows*max_columns) not in DISABLED_RANGE):
                        shifted_columns = (rows*max_columns + columns + shift)%max_columns
                        shifted_rows = (rows*max_columns + columns +  shift)/max_columns
                        self.RBVMRange[columns + rows*max_columns].grid(row=shifted_rows,column=shifted_columns*3)
                        self.RBVMRange[columns + rows*max_columns].deselect()
                        Label(self.Frames[1], text=self.VMRange[columns + rows*max_columns], fg='blue').grid(row=shifted_rows,column=(shifted_columns*3)+1, sticky=W)
                        Label(self.Frames[1], text=' '*column_separation_length).grid(row=shifted_rows,column=(shifted_columns*3)+2)
                    else:
                        shift -= 1

        self.Frames.append(LabelFrame(self.master,text='Calibration Table'))
        self.Frames[2].grid(row=2,column=0)
        Label(self.Frames[2], text='Data\nPoints', fg='blue').grid(row=0, column=0)
        Label(self.Frames[2], text='ADC\nValues', fg='blue').grid(row=0, column=2)
        Label(self.Frames[2], text='Measured\nVoltage', fg='blue').grid(row=0, column=3)
        for row in range(NO_OF_POINTS):
            RBFrame = Frame(self.Frames[2])
            RBFrame.grid(row=row+1,column=0)
            self.RBEntry.append(Radiobutton(RBFrame,value=row,variable = self.data_point))
            self.RBEntry[row].grid(row=row, column=0, sticky=E)
            Label(RBFrame, text=" "+str(row)+" ",fg='blue',relief=RIDGE).grid(row=row, column=1, sticky=W)
            self.RBEntry[row].deselect()
            ## Pre-filled ADC Values ##
            self.entryADCValues.append(IntVar())
            self.EntryADC.append(Entry(self.Frames[2],bg='white',justify=RIGHT,width=8,textvariable=self.entryADCValues[row],readonlybackground='grey',takefocus=False))
            self.EntryADC[row].grid(row=row+1, column=2, sticky=W)
            ## Actual Voltage ##
            self.entryVoltageValues.append(DoubleVar())
            self.EntryVoltage.append(Entry(self.Frames[2], bg='white', justify=RIGHT, width=8, textvariable=self.entryVoltageValues[row]))
            self.EntryVoltage[row].grid(row=row+1, column=3, sticky=W)
            self.Voltage_labels.append(Label(self.Frames[2], text='',width=3, relief=RIDGE))
            self.Voltage_labels[row].grid(row=row+1, column=4 ,sticky=W)

        self.BtnLoadDefaultCalib = Button(self.Frames[2], text='Load Default Calibration', fg='red')
        self.BtnLoadDefaultCalib.grid(row=NO_OF_POINTS+1, column=0, columnspan=5, sticky=N+E+W+S)
        self.BtnLoadDefaultCalib.config(state = DISABLED)
        self.BtnSaveCalibTable = Button(self.Frames[2], text='Save Calibration Table', fg='blue')
        self.BtnSaveCalibTable.grid(row=NO_OF_POINTS+2, column=0, columnspan=5, sticky=N+E+W+S)
        self.BtnSaveCalibTable.config(state = DISABLED)
        self.message = Label(self.Frames[2], text='', relief=RIDGE)
        self.message.grid(row=NO_OF_POINTS+3, column=0, columnspan=5, sticky=N+E+W+S)
        return

    def vEnableVMRangeSelect(self):
        '''
        Enables Range Selection
        '''
        for column in range(VOLTAGE_RANGE):
            self.RBVMRange[column].config(state = NORMAL)
            self.RBVMRange[column].deselect()
        return

    def vDisableVMRangeSelect(self):
        '''
        Disables Range Selection
        '''
        for column in range(VOLTAGE_RANGE):
            self.RBVMRange[column].config(state = DISABLED)
            self.RBVMRange[column].deselect()
        return

    def vEnableCalibTable(self):
        '''
        Enables Calibration Table
        '''
        for row in range(NO_OF_POINTS):
           self.RBEntry[row].config(state = NORMAL)
           self.EntryADC[row].config(state = NORMAL)
           self.EntryVoltage[row].config(state = NORMAL)
        self.BtnSaveCalibTable.config(state = NORMAL)
        self.BtnLoadDefaultCalib.config(state = NORMAL)
        return

    def vDisableCalibTable(self):
        '''
        Disables Calibration Table
        '''
        for row in range(NO_OF_POINTS):
           self.RBEntry[row].config(state = DISABLED)
           self.RBEntry[row].deselect()
           self.EntryADC[row].config(state = DISABLED)
           self.EntryVoltage[row].config(state = DISABLED)
        self.BtnSaveCalibTable.config(state = DISABLED)
        self.BtnLoadDefaultCalib.config(state = DISABLED)
        return

    def vEnableCalibTest(self):
        '''
        Enable Calibration Testing
        '''
        self.TestVoltageValue.set(0.0)
        self.EntryTestVoltage.config(state = NORMAL)
        return

    def vDisableCalibTest(self):
        '''
        Disable Calibration Testing
        '''
        self.EntryTestVoltage.config(state = DISABLED)
        return

    def vMakeADCreadonly(self):
        '''
        Makes ADC Entry Values Readonly
        '''
        for index in range(NO_OF_POINTS):
            self.EntryADC[index].config(state="readonly")
        return

    def vUpdateVoltageUnit(self):
        '''
        Updates the Unit in which voltage is displayed (V)
        '''
        for row in range(NO_OF_POINTS):
            self.Voltage_labels[row].config(text=self.VoltageUnit[self.VMRange_selected.get()])
        return

    def vConfimationPopup(self):
        return tkMessageBox.askyesno('Changes not Saved', 'Modified calibration\n values will be lost!\n    Continue?', default=tkMessageBox.NO, parent = self.master)


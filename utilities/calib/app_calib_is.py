from Tkinter import *
import tkMessageBox
import tkSimpleDialog
#menu_font_type = ("Verdana", 12, 'normal')	# font description
menu_font_type = ("Helvetica", 11, 'normal')	# font description

CURRENT_RANGE              = 5
CURRENT_RANGE_LABELS       = ['10uA', '100uA', '1mA', '10mA', '100mA']
CURRENT_RANGE_UNIT_LABELS  = [  'uA',    'uA',  'mA',   'mA',    'mA']
DISABLED_RANGE             = [     0,       4]
NO_OF_POINTS               = 5

def app_calib_is(master):
    oAppCalibIS = AppCalibIS(master)
    return oAppCalibIS

class AppCalibIS:
    def __init__(self, master):
        self.master = master
        self.master.title('Current Source Calibration')
        self.CSRange = CURRENT_RANGE_LABELS
        self.CurrentUnit = CURRENT_RANGE_UNIT_LABELS
        self.RBCSRange = []
        self.EntryDAC = []
        self.RBEntry = []
        self.EntryCurrent = []
        self.Frames = []
        self.entryDACValues = []
        self.entryCurrentValues = []
        self.Current_labels = []
        self.CSRange_selected = IntVar()
        self.data_point = IntVar()
        self._vCreateWidgets()
        self.vDisableCSRangeSelect()
        self.vDisableCalibTable()
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
        Label(self.Frames[0], text='Test Current (A) :', justify=CENTER, fg='blue').grid(row=0,column=0)
        self.TestCurrentValue = DoubleVar()
        self.EntryTestCurrent = Entry(self.Frames[0], bg='white', justify=LEFT, width=12, textvariable=self.TestCurrentValue)
        self.EntryTestCurrent.grid(row=0,column=1,sticky=N+E+W+S,pady=5)
        self.EntryTestCurrent.config(state = DISABLED)

        self.Frames.append(LabelFrame(self.master,text='Current Range'))
        self.Frames[1].grid(row=1,column=0,sticky=N+E+W+S)

        max_columns = 2
        max_rows = (CURRENT_RANGE/max_columns) + (CURRENT_RANGE%max_columns)
        max_range = CURRENT_RANGE
        column_separation_length = 8
        shift = 0

        for rows in range(max_rows):
            for columns in range(max_columns):
                if (rows*max_columns + columns <= max_range-1):
                    self.RBCSRange.append(Radiobutton(self.Frames[1],variable = self.CSRange_selected,value=(columns + rows*max_columns)))
                    if ((columns + rows*max_columns) not in DISABLED_RANGE):
                        shifted_columns = (rows*max_columns + columns + shift)%max_columns
                        shifted_rows = (rows*max_columns + columns +  shift)/max_columns
                        self.RBCSRange[columns + rows*max_columns].grid(row=shifted_rows,column=shifted_columns*3)
                        self.RBCSRange[columns + rows*max_columns].deselect()
                        Label(self.Frames[1], text=self.CSRange[columns + rows*max_columns], fg='blue').grid(row=shifted_rows,column=(shifted_columns*3)+1, sticky=W)
                        Label(self.Frames[1], text=' '*column_separation_length).grid(row=shifted_rows,column=(shifted_columns*3)+2)
                    else:
                        shift -= 1

        self.Frames.append(LabelFrame(self.master,text='Calibration Table'))
        self.Frames[2].grid(row=2,column=0)
        Label(self.Frames[2], text='Data\nPoints', fg='blue').grid(row=0, column=0)
        Label(self.Frames[2], text='DAC\nValues', fg='blue').grid(row=0, column=2)
        Label(self.Frames[2], text='Actual\nCurrent', fg='blue').grid(row=0, column=3)
        for row in range(NO_OF_POINTS):
            RBFrame = Frame(self.Frames[2])
            RBFrame.grid(row=row+1,column=0)
            self.RBEntry.append(Radiobutton(RBFrame,value=row,variable = self.data_point))
            self.RBEntry[row].grid(row=row, column=0, sticky=E)
            Label(RBFrame, text=" "+str(row)+" ",fg='blue',relief=RIDGE).grid(row=row, column=1, sticky=W)
            self.RBEntry[row].deselect()
            ## Pre-filled DAC Values ##
            self.entryDACValues.append(IntVar())
            self.EntryDAC.append(Entry(self.Frames[2],bg='white',justify=RIGHT,width=8,textvariable=self.entryDACValues[row],readonlybackground='grey',takefocus=False))
            self.EntryDAC[row].grid(row=row+1, column=2, sticky=W)
            ## Actual Current ##
            self.entryCurrentValues.append(DoubleVar())
            self.EntryCurrent.append(Entry(self.Frames[2], bg='white', justify=RIGHT, width=8, textvariable=self.entryCurrentValues[row]))
            self.EntryCurrent[row].grid(row=row+1, column=3, sticky=W)
            self.Current_labels.append(Label(self.Frames[2], text='',width=3, relief=RIDGE))
            self.Current_labels[row].grid(row=row+1, column=4 ,sticky=W)

        self.BtnLoadDefaultCalib = Button(self.Frames[2], text='Load Default Calibration', fg='red')
        self.BtnLoadDefaultCalib.grid(row=NO_OF_POINTS+1, column=0, columnspan=5, sticky=N+E+W+S)
        self.BtnLoadDefaultCalib.config(state = DISABLED)
        self.BtnSaveCalibTable = Button(self.Frames[2], text='Save Calibration Table', fg='blue')
        self.BtnSaveCalibTable.grid(row=NO_OF_POINTS+2, column=0, columnspan=5, sticky=N+E+W+S)
        self.BtnSaveCalibTable.config(state = DISABLED)
        self.message = Label(self.Frames[2], text='', relief=RIDGE)
        self.message.grid(row=NO_OF_POINTS+3, column=0, columnspan=5, sticky=N+E+W+S)
        return

    def vEnableCSRangeSelect(self):
        '''
        Enables Range Selection
        '''
        for column in range(CURRENT_RANGE):
            self.RBCSRange[column].config(state = NORMAL)
            self.RBCSRange[column].deselect()
        return

    def vDisableCSRangeSelect(self):
        '''
        Disables Range Selection
        '''
        for column in range(CURRENT_RANGE):
            self.RBCSRange[column].config(state = DISABLED)
            self.RBCSRange[column].deselect()
        return

    def vEnableCalibTable(self):
        '''
        Enables Calibration Table
        '''
        for row in range(NO_OF_POINTS):
           self.RBEntry[row].config(state = NORMAL)
           self.EntryDAC[row].config(state = NORMAL)
           self.EntryCurrent[row].config(state = NORMAL)
        self.BtnSaveCalibTable.config(state = NORMAL)
        self.BtnLoadDefaultCalib.config(state = NORMAL)
        self.vMakeDACreadonly()
        return

    def vDisableCalibTable(self):
        '''
        Disables Calibration Table
        '''
        for row in range(NO_OF_POINTS):
           self.RBEntry[row].config(state = DISABLED)
           self.RBEntry[row].deselect()
           self.EntryDAC[row].config(state = DISABLED)
           self.EntryCurrent[row].config(state = DISABLED)
        self.BtnSaveCalibTable.config(state = DISABLED)
        self.BtnLoadDefaultCalib.config(state = DISABLED)
        return

    def vEnableCalibTest(self):
        '''
        Enable Calibration Testing
        '''
        self.TestCurrentValue.set(0.0)
        self.EntryTestCurrent.config(state = NORMAL)
        return

    def vDisableCalibTest(self):
        '''
        Disable Calibration Testing
        '''
        self.EntryTestCurrent.config(state = DISABLED)
        return

    def vMakeDACreadonly(self):
        '''
        Makes DAC Entry Values Readonly
        '''
        for index in range(NO_OF_POINTS):
            self.EntryDAC[index].config(state="readonly")
        return

    def vUpdateCurrentUnit(self):
        '''
        Updates the Unit in which current is displayed (mA/uA)
        '''
        for row in range(NO_OF_POINTS):
            self.Current_labels[row].config(text=self.CurrentUnit[self.CSRange_selected.get()])
        return

    def vConfimationPopup(self):
        return tkMessageBox.askyesno('Changes not Saved', 'Modified calibration\n values will be lost!\n    Continue?', default=tkMessageBox.NO, parent = self.master)


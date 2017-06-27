#####################
#   Menubar Class   #
#####################
import os
import tkSimpleDialog
import tkMessageBox

import app_menubar
import about
import kbsc
import calib_is
import calib_vs
import calib_im
import calib_vm

from AppGlobalSettings import AppGlobalSettings

VIDEO_PATH = os.path.join(os.curdir, 'videos')

from Tkinter import *

def menubar(root, oToolbar):
    """
    Adds menubar to the main app. window
    """
    oAppMenubar = app_menubar.app_menubar()
    oAppMenubar.createMenubar(root)
    oMenubar = Menubar(oAppMenubar, oToolbar)
    return oMenubar

class Menubar:

    def __init__(self, oAppMenubar, oToolbar):
        """
        Class Contructor : Menubar
        """
        self.oToolbar = oToolbar
        self.oAppMenubar = oAppMenubar
        self._configureCB()
        return

    def _configureCB(self):
        """
        Attaches Callbacks to MenubarGui widgets
        """
        self.oAppMenubar.filemenu.add_command(label='Open <Ctrl+o>', underline=0, command=self.oToolbar.oAppToolbar.BtnOpenFile.invoke)
        self.oAppMenubar.filemenu.add_command(label='Status <Ctrl+t>', underline=0, command=self.oToolbar.oAppToolbar.BtnInitXplore.invoke)
        self.oAppMenubar.filemenu.add_command(label='Quit', underline=0, command=self.oToolbar.oAppToolbar.BtnExit.invoke)
        self.oAppMenubar.settingsmenu.add_command(label='Global Settings', underline=0, command=self.wGlobSettingsCB)
        self.oAppMenubar.utilitiesmenu.add_command(label='More', underline=0, command=None)
        self.oAppMenubar.calibrationmenu.add_command(label='Current Source', underline=0, command=self.vCurrentSourceCalibCB)
        self.oAppMenubar.calibrationmenu.add_command(label='Voltage Source', underline=0, command=self.vVoltageSourceCalibCB)
        self.oAppMenubar.calibrationmenu.add_command(label='Current Measure', underline=0, command=self.vCurrentMeasureCalibCB)
        self.oAppMenubar.calibrationmenu.add_command(label='Voltage Measure', underline=0, command=self.vVoltageMeasureCalibCB)
        self.oAppMenubar.helpmenu.add_command(label='About', underline=0, command=self.vAboutInQCB)
        self.oAppMenubar.helpmenu.add_command(label='Keyboard Shortcuts', underline=0, command=self.vKBSCCB)
        self.oAppMenubar.helpmenu.add_command(label='Xplore User Manual<F1>', underline=0, command=self.vInQHelpCB)
        self.oAppMenubar.helpmenu.add_command(label='HowTO Videos', underline=0, command=self.vHowTOVideosCB)
        self.Export_Instance = 0
        self.About_Instance = 0
        self.KBSC_Instance = 0
        self.CalibIS_Instance = 0
        self.CalibVS_Instance = 0
        self.CalibIM_Instance = 0
        self.CalibVM_Instance = 0
        return

    def vGetMain(self, oMainMaster):
        print 'Unpacking main'
        self.oMainMaster = oMainMaster
        return

    def vLaunchExportCB(self):
        """
        Launches Export Utility
        """
        #oe = export.export()
        return

    def vDisableMbGroup(self):
        """
        Disables Menubar Window
        """
        self.vDisableFileMenu()
        return

    def vDisableFileMenu(self):
        """
        Disable Menubar widgets
        """
        self.oAppMenubar.mainmenu.entryconfig(0,state=DISABLED)
        self.oAppMenubar.mainmenu.entryconfig(1,state=DISABLED)
        self.oAppMenubar.mainmenu.entryconfig(2,state=DISABLED)
        self.oAppMenubar.mainmenu.entryconfig(3,state=DISABLED)
        self.oAppMenubar.mainmenu.entryconfig(4,state=DISABLED)
        return

    def vEnableMbGroup(self):
        """
        Enables Menubar window
        """
        self.vEnableFileMenu()
        return

    def vEnableFileMenu(self):
        """
        Enables Menubar widgets
        """
        self.oAppMenubar.mainmenu.entryconfig(0,state=NORMAL)
        self.oAppMenubar.mainmenu.entryconfig(1,state=NORMAL)
        self.oAppMenubar.mainmenu.entryconfig(2,state=NORMAL)
        self.oAppMenubar.mainmenu.entryconfig(3,state=NORMAL)
        self.oAppMenubar.mainmenu.entryconfig(4,state=NORMAL)
        self.oAppMenubar.mainmenu.entryconfig(5,state=NORMAL)
        return

    def wGlobSettingsCB (self):
		w = AppGlobalSettings (master = Toplevel (takefocus=True))
		w.callback (self.appGlobSettingsCB)

		# Makes it modal
		parent = self.oAppMenubar.master.winfo_toplevel()
		parent.lift()
		w.master.focus_set()
		w.master.grab_set()
		w.master.wm_attributes("-topmost", 1)
		w.master.transient (parent)

    def appGlobSettingsCB (self, caller, context):

		if context == caller.CB_CONTEXT_OK:
			caller.master.destroy()

		elif context == caller.CB_CONTEXT_CANCEL:
			caller.master.destroy()

    def vPortSettingsCB(self):
        """
        Adds a new port to the device search list
        """
        #self.oMainMaster.vAddNewPort()
        return

    def vCurrentSourceCalibCB(self):
        """
        Displays the Current Source Calibration Window
        """
        self.CalibIS_Instance += 1
        if self.CalibIS_Instance > 1:
            self.vHighlightWindow(self.winCalibIS)
            return
        if self.CalibIS_Instance == 1:
            self.winCalibIS = Toplevel(takefocus=True)
            self.winCalibIS.resizable(False, False)
            self.winCalibIS.protocol('WM_DELETE_WINDOW', self.vCloseCalibISWindow)
            oCalibIS = calib_is.calib_is(self.winCalibIS)
        return

    def vVoltageSourceCalibCB(self):
        """
        Displays the Voltage Source Calibration Window
        """
        self.CalibVS_Instance += 1
        if self.CalibVS_Instance > 1:
            self.vHighlightWindow(self.winCalibVS)
            return
        if self.CalibVS_Instance == 1:
            self.winCalibVS = Toplevel(takefocus=True)
            self.winCalibVS.resizable(False, False)
            self.winCalibVS.protocol('WM_DELETE_WINDOW', self.vCloseCalibVSWindow)
            oCalibVS = calib_vs.calib_vs(self.winCalibVS)
        return

    def vCurrentMeasureCalibCB(self):
        """
        Displays the Current Measure Calibration Window
        """
        self.CalibIM_Instance += 1
        if self.CalibIM_Instance > 1:
            self.vHighlightWindow(self.winCalibIM)
            return
        if self.CalibIM_Instance == 1:
            self.winCalibIM = Toplevel(takefocus=True)
            self.winCalibIM.resizable(False, False)
            self.winCalibIM.protocol('WM_DELETE_WINDOW', self.vCloseCalibIMWindow)
            oCalibIM = calib_im.calib_im(self.winCalibIM)
        return

    def vVoltageMeasureCalibCB(self):
        """
        Displays the Voltage Measure Calibration Window
        """
        self.CalibVM_Instance += 1
        if self.CalibVM_Instance > 1:
            self.vHighlightWindow(self.winCalibVM)
            return
        if self.CalibVM_Instance == 1:
            self.winCalibVM = Toplevel(takefocus=True)
            self.winCalibVM.resizable(False, False)
            self.winCalibVM.protocol('WM_DELETE_WINDOW', self.vCloseCalibVMWindow)
            oCalibVM = calib_vm.calib_vm(self.winCalibVM)
        return

    def vCloseCalibISWindow(self):
        self.CalibIS_Instance = 0
        self.winCalibIS.destroy()
        return

    def vCloseCalibVSWindow(self):
        self.CalibVS_Instance = 0
        self.winCalibVS.destroy()
        return

    def vCloseCalibIMWindow(self):
        self.CalibIM_Instance = 0
        self.winCalibIM.destroy()
        return

    def vCloseCalibVMWindow(self):
        self.CalibVM_Instance = 0
        self.winCalibVM.destroy()
        return

    def vAboutInQCB(self):
        """
        Acknowledgements About Qrius
        """
        self.About_Instance += 1
        if self.About_Instance > 1:
            self.vHighlightWindow(self.winAbout)
            return
        if self.About_Instance == 1:
            self.winAbout = Toplevel(takefocus=True)
            self.winAbout.resizable(False, False)
            self.winAbout.protocol('WM_DELETE_WINDOW', self.vCloseAboutWindow)
            oAbout = about.about(self.winAbout, self)
        return

    def vCloseAboutWindow(self):
        self.About_Instance = 0
        self.winAbout.destroy()
        return

    def vKBSCCB(self):
        """
        Displays the List of Keyboard Shortcuts
        """
        self.KBSC_Instance += 1
        if self.KBSC_Instance > 1:
            self.vHighlightWindow(self.winKBSC)
            return
        if self.KBSC_Instance == 1:
            self.winKBSC = Toplevel(takefocus=True)
            self.winKBSC.resizable(False, False)
            self.winKBSC.protocol('WM_DELETE_WINDOW', self.vCloseKBSCWindow)
            oKBSC = kbsc.kbsc(self.winKBSC, self)
        return

    def vCloseKBSCWindow(self):
        self.KBSC_Instance = 0
        self.winKBSC.destroy()
        return

    def vHighlightWindow(self, winObj):
        winObj.deiconify()
        winObj.lift()
        return

    def vInQHelpCB(self):
        """
        Launches SiM help
        """
        self.oToolbar.BtnHelpCB()
        return

    def vHowTOVideosCB(self):
        cmd = 'vlc ' + os.path.join(VIDEO_PATH) + ' 1> /dev/null 2> /dev/null &'
        try:
            os.system(cmd)
        except:
            print 'Player or video path not found'
        return

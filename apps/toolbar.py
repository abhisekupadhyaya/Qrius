#######################
#   Toolbar Class     #
#######################

__DEBUG__ = True

import os, sys, time
import tkMessageBox
import app_toolbar, AppAnalyzer
from Tkinter import Toplevel, NSEW
from modules import closeModules
from ppsel   import closePPSel

help_path = os.path.join(os.curdir, 'docs')
files = os.listdir(help_path)
files.sort()
help_files = []
for file in files:
	if os.path.splitext(file)[-1] == '.pdf':
		help_files.append(file)
if help_files == []:
	HELP_FILE = None
else:
	HELP_FILE = help_files[-1]

if __DEBUG__ == True:
	from Tkinter import *

def toolbar(Frame):
	"""
	Creates toolbar for the main app. window
	"""
	oAppToolbar = app_toolbar.app_toolbar()
	oAppToolbar.createTBwindow(Frame)
	oToolbar = Toolbar(oAppToolbar)
	return oToolbar

class Toolbar:

	def __init__(self, oAppToolbar):
		"""
		Class Contructor : Toolbar
		"""
		self.oAppToolbar = oAppToolbar
		self._configureCB()
		return

	def _configureCB(self):
		"""
		Attaches Callbacks to ToolbarGui widgets
		"""
		self.oAppToolbar.BtnInitXplore.config(command=self.BtnInitXploreCB)
		self.oAppToolbar.BtnOpenFile.config(command=self.BtnOpenFileCB)
		self.oAppToolbar.BtnHelp.config(command=self.BtnHelpCB)
		self.oAppToolbar.BtnExit.config(command=self.BtnExitCB)
		return

	def vGetMain(self, oMain, MainMaster):
		"""
		Links Main Window to Toolbar class
		"""
		self.MainMaster = MainMaster
		self.oMain = oMain
		self.__vConfigureKBShortCuts()
		return

	def BtnInitXploreCB(self, event=None):
		"""
		"""
		#self.oOffset.vInitialSTMSetup(self.MainMaster)
		return

	#def BtnOpenFileCB(self, event=None):
		#"""
		#Opens a run
		#"""
		#app = AppAnalyzer.AppAnalyzer (
			#Toplevel (takefocus=True), self.wAnalyzerCB)

	#def wAnalyzerCB (self, analyzer):
		#if analyzer.callbackContext() == AppAnalyzer.CALLBACK_CONTEXT_EXIT:
			#analyzer.win().destroy()

	def BtnOpenFileCB(self, event=None):
		app = AppAnalyzer.AppAnalyzer (Toplevel (takefocus=True))
		app.grid (row = 0, column = 0, sticky = NSEW)

	def vHighlightWindow(self, winObj):
		winObj.deiconify()
		winObj.lift()
		return

	def BtnHelpCB(self, event=None):
		"""
		Displays UserManual
		"""
		if HELP_FILE == None:
			print 'No help file found....'
			return
		cmd = 'evince ' + os.path.join(help_path, HELP_FILE) + " &"
		os.popen(cmd)
		return

	def BtnExitCB(self, event=None):
		"""
		Quits InQ
		"""
		#self.oInfoBox.vWriteLog(time.ctime())
		if tkMessageBox.askyesno (
				'Close', '"Yes" means point of no return !'):
			#self.oMain.vCloseAllWindows()
			closePPSel()
			closeModules()
			self.MainMaster.destroy()

	def vDisableTbGroup(self):
		"""
		Freezes ToolbarGui widgets
		--> This is essential for suppressing features espicially when scanning is taking place
		"""
		self.oAppToolbar.BtnInitXplore.config(state=DISABLED)
		self.oAppToolbar.BtnOpenFile.config(state=DISABLED)
		self.oAppToolbar.BtnHelp.config(state=DISABLED)
		self.oAppToolbar.BtnExit.config(state=DISABLED)
		return

	def vEnableTbGroup(self):
		"""
		Enables Toolbar widgets
		"""
		self.oAppToolbar.BtnInitXplore.config(state=NORMAL)
		self.oAppToolbar.BtnOpenFile.config(state=NORMAL)
		self.oAppToolbar.BtnHelp.config(state=NORMAL)
		self.oAppToolbar.BtnExit.config(state=NORMAL)
		return

	def __vConfigureKBShortCuts(self):
		"""
		Keyboard bindings for different functions
		"""
		self.MainMaster.bind('<Control-o>', self.BtnOpenFileCB)
		self.MainMaster.bind('<Control-t>', self.BtnInitXploreCB)
		self.MainMaster.bind('<Control-q>', self.BtnExitCB)
		self.MainMaster.bind('<F1>', self.BtnHelpCB)
		return


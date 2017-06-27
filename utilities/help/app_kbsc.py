from Tkinter import *
import os

def app_kbsc():
    """
    Create KeyBoard ShortCuts object
    """
    kbscObj = KBSCGui()
    return kbscObj

class KBSCGui:
    def __init__(self):
	"""
	"""
	pass
	return

    def createKBSCwindow(self, master):
	self.kbscGroup = master
	self.__createKBSCwidgets()
	return

    def __createKBSCwidgets(self):
	Label(self.kbscGroup, text='Functions:', fg='blue').grid(row=0, column=0, sticky=E)
	Label(self.kbscGroup, text='Keys:', fg='blue').grid(row=0, column=1, sticky=W)
	self.SBXRemBar = Scrollbar(self.kbscGroup, \
					orient=HORIZONTAL, \
					)
	self.SBXRemBar.grid(row=2,column=0, sticky=E+W)

	self.SBYRemBar = Scrollbar(self.kbscGroup, \
					orient=VERTICAL, \
					)
	self.SBYRemBar.grid(row=1,column=2, sticky=N+S)
	self.TBFunctions = Text(self.kbscGroup, \
					height=30, \
					width=28, \
					bg = 'light blue', \
					xscrollcommand=self.SBXRemBar.set, \
					yscrollcommand=self.SBYRemBar.set, \
					)
	self.TBFunctions.grid(row=1, column=0, sticky=N+S)
	self.TBKeys = Text(self.kbscGroup, \
					height=30, \
					width=18, \
					bg = 'light blue', \
					xscrollcommand=self.SBXRemBar.set, \
					yscrollcommand=self.SBYRemBar.set, \
					)
	self.TBKeys.grid(row=1, column=1, sticky=N+S)

	self.SBXRemBar.config(command=self.TBFunctions.xview)
	self.SBYRemBar.config(command=self.TBFunctions.yview)
	self.SBYRemBar.config(command=self.TBKeys.yview)
	return



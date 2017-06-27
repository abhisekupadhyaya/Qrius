from Tkinter import *
from PIL import Image
from PIL import ImageTk
import os

iconpath	 = os.path.join('apps', 'icons')		#  path for icons folder containing thumbimages for toolbar
init_iconfile	 = os.path.join(iconpath, 'settings.png')       #  Init Settings iconpath
open_iconfile	 = os.path.join(iconpath, 'open2.png')		#  Open File iconpath
help_iconfile	 = os.path.join(iconpath, 'help.png')		#  Help iconpath
exit_iconfile	 = os.path.join(iconpath, 'exit.png')		#  Quit iconpath

def app_toolbar():
	"""
	Returns ToolBarGui object
	"""
	tGuiObj = ToolBarGui()
	return tGuiObj

class ToolBarGui:

	def __init__(self):
		"""
		Class Contructor : ToolBarGui
		"""
		print 'Toolbar window created'
		return

	def createTBwindow(self, master):
		"""
		Method : createTBwindow
		"""
		self.tbarGroup = master
		self._createImages()
		self._createTBwidgets()
		return

	def _createTBwidgets(self):
		"""
		Loads Toolbar Widgets in Toolbar Window
		"""
		self.BtnInitXplore = Button(self.tbarGroup,\
						image=initim, \
						text='Init', \
						relief=FLAT, \
						overrelief=RAISED, \
						compound=TOP)
		self.BtnInitXplore.pack(side=LEFT, anchor=NW)

		self.BtnOpenFile = Button(self.tbarGroup,\
						image=openim, \
						text='Open', \
						relief=FLAT, \
						overrelief=RAISED, \
						compound=TOP)
		self.BtnOpenFile.pack(side=LEFT, anchor=NW)

		self.BtnHelp = Button(self.tbarGroup,\
						image=helpim, \
						text='Help', \
						relief=FLAT, \
						overrelief=RAISED, \
						compound=TOP)
		self.BtnHelp.pack(side=LEFT, anchor=NW)

		self.BtnExit = Button(self.tbarGroup,\
						image=exitim, \
						text='Exit', \
						relief=FLAT, \
						overrelief=RAISED, \
						compound=TOP)
		self.BtnExit.pack(side=LEFT, anchor=NW)
		return

	def _createImages(self):
		"""
		Attaches thumbnails to Toolbar buttons
		"""
		global initim, openim, \
                       helpim, exitim
		initim		= ImageTk.PhotoImage(file=init_iconfile)
		openim		= ImageTk.PhotoImage(file=open_iconfile)
		helpim		= ImageTk.PhotoImage(file=help_iconfile)
		exitim		= ImageTk.PhotoImage(file=exit_iconfile)
		return



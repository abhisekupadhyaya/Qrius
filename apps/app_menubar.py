from Tkinter import *

def app_menubar():
	"""
	Creates Menubar GUI
	"""
	oMenubarGui = MenubarGui()
	return oMenubarGui

class MenubarGui:

	def __init__(self):
		"""
		"""
		print 'Menubar created'
		return

	def createMenubar(self, master):
		"""
		"""
		self.master = master
		self._createMenuItems()
		return


	def _createMenuItems(self):
		"""
		Populate Menu Contents
		"""
		self.mainmenu = Menu(self.master)
		self.mainmenu.config(borderwidth=1)
		self.master.config(menu=self.mainmenu)

		self.filemenu = Menu(self.mainmenu)
		self.filemenu.config(tearoff=0)
		self.mainmenu.add_cascade(
			label='File', menu=self.filemenu, underline=0)

		self.settingsmenu = Menu(self.mainmenu)
		self.settingsmenu.config(tearoff=0)
		self.mainmenu.add_cascade(
			label='Settings', menu=self.settingsmenu, underline=0)

		self.utilitiesmenu = Menu(self.mainmenu)
		self.utilitiesmenu.config(tearoff=0)
		self.mainmenu.add_cascade(
			label='Utilities', menu=self.utilitiesmenu, underline=0)

		self.calibrationmenu = Menu(self.utilitiesmenu)
		self.calibrationmenu.config(tearoff=0)
		self.utilitiesmenu.add_cascade(
			label='Calibration', menu=self.calibrationmenu, underline=0)

		self.helpmenu = Menu(self.mainmenu)
		self.helpmenu.config(tearoff=0)
		self.mainmenu.add_cascade(
			label='Help', menu=self.helpmenu, underline=0)

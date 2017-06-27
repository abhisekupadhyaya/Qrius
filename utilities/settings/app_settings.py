from Tkinter import *

def app_settings():
	"""
	Returns ScannerGui object
	"""
	oSettingsGui = SettingsGui()
	return oSettingsGui

class SettingsGui:


	def __init__(self):
		"""
		"""
		print 'Settings Gui created'
		return

	def createSettingsWindow(self, master):
		"""
		Launched from outside provided a frame to create window is given
		"""
		self.sGroup = master
		self._createSettingswidgets()
		return

	def _createSettingswidgets(self):
		w = 30
		h = 3
		self.BtnSampleSettings = Button(self.sGroup, \
					width = w,\
					height = h, \
					text='Sample Settings')
                self.BtnSampleSettings.grid(row=0, column=0, sticky=W+E)

		self.BtnPPSelSettings = Button(self.sGroup, \
					width = w,\
					height = h, \
					text='Measurement Mode Settings')
                self.BtnPPSelSettings.grid(row=1, column=0, sticky=W+E)

		self.BtnModuleSettings = Button(self.sGroup, \
					width = w,\
					height = h, \
					text='Modules Manager')
                self.BtnModuleSettings.grid(row=2, column=0, sticky=W+E)

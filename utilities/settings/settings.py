from Tkinter import *

import app_settings
import ppsel, sample, modules

from sample  import Sample as openSample
from modules import Modules
from ppsel   import PPSel

def settings(Frame):
	"""
	Returns Scanner object
	"""
	oAppSettings = app_settings.app_settings()
	oAppSettings.createSettingsWindow(Frame)
	oSettings = Settings(oAppSettings)
	return oSettings

class Settings:
	def __init__(self, oAppSettings):
		self.oAppSettings = oAppSettings
		self._configureWidgets()

		self.ModuleSettingsInstance = 0
		self.winModuleSettings = None
		self.oModules = None

		self.PPSelSettingsInstance = 0
		self.winPPSelSettings = None
		self.oPPSel = None

		self.SampleSettingsInstance = 0
		self.winSampleSettings = None
		self.oSample = None

		return

	def _configureWidgets(self):
		self.oAppSettings.BtnSampleSettings.config(command=self.BtnSampleSettingsCB)
		self.oAppSettings.BtnPPSelSettings.config(command=self.BtnPPSelSettingsCB)
		self.oAppSettings.BtnModuleSettings.config(command=self.BtnModuleSettingsCB)

	def BtnSampleSettingsCB (self):
		sample = openSample (self)
		sample.show()

	def oGetSampleSettings(self, winSam=None):
		self.oSample = sample.sample(winSam)
		if self.SampleSettingsInstance == 0:
			self.SampleSettingsInstance += 1
		return self.oSample

	def vCloseSampleSettings(self):
		if self.SampleSettingsInstance == 0:
			return
		self.SampleSettingsInstance = 0
		if self.winSampleSettings != None:
			self.winSampleSettings.destroy()
		self.winSampleSettings = None
		return

	def BtnModuleSettingsCB(self):
		modules = Modules()
		modules.show()

	def oGetModules(self, winMod=None):
		self.oModules = modules.modules(winMod)
		self.ModuleSettingsInstance += 1
		return self.oModules

	def vCloseModuleSettings(self, killall=False):
		if self.ModuleSettingsInstance == 0:
			return
		if killall:
			self.ModuleSettingsInstance = 0
			self.oModules.vCloseAllWindows(killall)
			if self.winModuleSettings != None:
				self.winModuleSettings.destroy()
				self.winModuleSettings = None
		else:
			if self.winModuleSettings != None:
				self.vIconifyModuleSettings()
		return

	def vIconifyModuleSettings(self):
		self.oModules.vCloseAllWindows()
		self.winModuleSettings.iconify()
		return

	def BtnPPSelSettingsCB(self):
		ppsel = PPSel()
		ppsel.show()

	def oGetPPSel(self, winPPSel=None):
		self.oPPSel = ppsel.ppsel(winPPSel, self)
		if self.PPSelSettingsInstance == 0:
			self.PPSelSettingsInstance += 1
		return self.oPPSel

	def vClosePPSelSettings(self, killall=False):
		if self.PPSelSettingsInstance == 0:
			return
		self.oPPSel.vCloseAllWindows(killall)
		if killall == True:
			self.PPSelSettingsInstance = 0
			self.winPPSelSettings.destroy()
			self.winPPSelSettings = None
		else:
			self.vIconifyPPSel()
		return

	def vIconifyPPSel(self):
		self.oPPSel.vCloseAllWindows()
		self.winPPSel.iconify()
		return

	def vHighlightWindow(self, winObj):
		winObj.deiconify()
		winObj.lift()
		return

	def vCloseAllWindows(self, killall=False):
		self.vCloseSampleSettings()
		self.vClosePPSelSettings(killall)
		self.vCloseModuleSettings(killall)
		return

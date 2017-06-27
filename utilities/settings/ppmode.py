
import app_settings
import ppmode
import modmode

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
	self._configureSettingsWidgets()
	return

    def _configureSettingsWidgets(self):
	return

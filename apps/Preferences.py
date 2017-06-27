import cPickle
import os
import errno
import traceback
import sys
from threading import RLock

################################################################

class CPreferences:

	USER_SPACE_ROOT   = 0
	SYSTEM_SPACE_ROOT = 1

	def __init__ (self, root, appName):
		self._thlock = RLock()
		self._dirty = True
		self._dict = {}
		self._root = root
		self._appName = appName
		self.load()
		return

	################################################################

	def dirty (self):

		try:
			self._thlock.acquire()
			dirty = self._dirty

		finally:
			self._thlock.release()

		return dirty

	def root (self):
		try:
			self._thlock.acquire()
			root = self._root

		finally:
			self._thlock.release()

		return root

	def appName (self):
		try:
			self._thlock.acquire()
			appName = self._appName

		finally:
			self._thlock.release()

		return appName

	################################################################

	def set_entry (self, key, value):

		try:
			self._thlock.acquire()

			if ((not key in self._dict)
			or (self._dict[key] != value)):
				self._dirty = True
				self._dict[key] = value

		finally:
			self._thlock.release()

	def get_entry (self, key, defaultValue):

		try:
			self._thlock.acquire()

			if not key in self._dict:
				print ('Key "' + key + '" does not exist ... Adding.')
				self.set_entry (key, defaultValue)

			entry = self._dict[key]

		finally:
			self._thlock.release()

		return entry

	################################################################

	def flush (self):

		try:
			self._thlock.acquire()

			if self.dirty():

				# Creating folder
				if not os.path.exists (self.folder()):

					print (self.folder()
						+ ' does not exist ... trying to creating.')
					os.makedirs (self.folder())

				# Writing pref file
				fd = open (self.path(), 'w')
				cPickle.dump (self._dict, fd)
				fd.close()

				self._dirty = False

		except (IOError, OSError) as e:
			print e.filename + ': ' + e.strerror

		finally:
			self._thlock.release()

	################################################################

	def load (self):

		try:
			self._thlock.acquire()

			fd = open (self.path(), 'r')
			self._dict = cPickle.load (fd)
			fd.close()

			self._dirty = False

		except (IOError, OSError) as e:
			print e.filename + ': ' + e.strerror
			self.flush()

		finally:
			self._thlock.release()

	################################################################

	def path (self):

		try:
			self._thlock.acquire()
			path = os.path.join (self.folder(), self.appName() + '.pref')

		finally:
			self._thlock.release()

		return path

	def folder (self):

		try:
			self._thlock.acquire()

			roots = ['~/.quazar', '/etc/quazar']
			folder = os.path.expanduser (roots [self.root()])

		finally:
			self._thlock.release()

		return folder

################################################################

def usr_prefs():

	if usr_prefs.singleton == None:
		usr_prefs.singleton = \
			CPreferences (CPreferences.USER_SPACE_ROOT, 'Qrius')

	return usr_prefs.singleton

usr_prefs.singleton = None

def sys_prefs():

	if sys_prefs.singleton == None:
		sys_prefs.singleton = \
			CPreferences (CPreferences.SYSTEM_SPACE_ROOT, 'Qrius')

	return sys_prefs.singleton

sys_prefs.singleton = None

def flush():
	usr_prefs().flush()
	sys_prefs().flush()

################################################################
###### Add application specific set and get functions here #####
################################################################

KTYPE_TC = 0
PT100 = 1

def getSampleTemperatureSensor():
	return sys_prefs().get_entry ('SampleTemperatureSensors', PT100)

def setSampleTemperatureSensor (sens):
	sys_prefs().set_entry ('SampleTemperatureSensors', sens)

################################################################

def defaultDataFolder():
	return os.path.expanduser ('~/QriusData')

def getDataFolder():
	return usr_prefs().get_entry ('DataFolder', defaultDataFolder())

def setDataFolder (folder):
	usr_prefs().set_entry ('DataFolder', os.path.expanduser (folder))

################################################################

def setSampleDetails (*args):
	usr_prefs().set_entry ('SampleDetails', args)

def getSampleDetails():
	return usr_prefs().get_entry ('SampleDetails', None)

################################################################
################################################################

def get_XSMU_serialNo():
	s = sys_prefs().get_entry ('XSMU_serialNo', 'QTxxxxxxA')
	return usr_prefs().get_entry ('XSMU_serialNo', s)

def set_XSMU_serialNo (serialNo):
	usr_prefs().set_entry ('XSMU_serialNo', serialNo)
	sys_prefs().set_entry ('XSMU_serialNo', serialNo)

################################################################

def get_XTCON_serialNo():
	s = sys_prefs().get_entry ('XTCON_serialNo', 'QTxxxxxxA')
	return usr_prefs().get_entry ('XTCON_serialNo', s)

def set_XTCON_serialNo (serialNo):
	sys_prefs().set_entry ('XTCON_serialNo', serialNo)
	usr_prefs().set_entry ('XTCON_serialNo', serialNo)

################################################################

def get_XLIA_serialNo():
	s = sys_prefs().get_entry ('XLIA_serialNo', 'QTxxxxxxA')
	return usr_prefs().get_entry ('XLIA_serialNo', s)

def set_XLIA_serialNo (serialNo):
	sys_prefs().set_entry ('XLIA_serialNo', serialNo)
	usr_prefs().set_entry ('XLIA_serialNo', serialNo)

################################################################

def get_XLIA_currentSenseResistance():
	R = sys_prefs().get_entry ('XLIA_currentSenseResistance', 20.0)
	return usr_prefs().get_entry ('XLIA_currentSenseResistance', R)

def set_XLIA_currentSenseResistance (R):
	sys_prefs().set_entry ('XLIA_currentSenseResistance', R)
	usr_prefs().set_entry ('XLIA_currentSenseResistance', R)

################################################################

def get_XMC_serialNo():
	s = sys_prefs().get_entry ('XMC_serialNo', 'QTxxxxxxA')
	return usr_prefs().get_entry ('XMC_serialNo', s)

def set_XMC_serialNo (serialNo):
	sys_prefs().set_entry ('XMC_serialNo', serialNo)
	usr_prefs().set_entry ('XMC_serialNo', serialNo)

################################################################

def get_XMC_linacStrokeLength():
	s = sys_prefs().get_entry ('XMC_linacStrokeLength', 60.0e-3)
	return usr_prefs().get_entry ('XMC_linacStrokeLength', s)

def set_XMC_linacStrokeLength (length):
	sys_prefs().set_entry ('XMC_linacStrokeLength', length)
	usr_prefs().set_entry ('XMC_linacStrokeLength', length)

################################################################

def get_XMC_linacPitch():
	pitch = sys_prefs().get_entry ('XMC_linacPitch', 1.25e-3)
	return usr_prefs().get_entry ('XMC_linacPitch', pitch)

def set_XMC_linacPitch (pitch):
	sys_prefs().set_entry ('XMC_linacPitch', pitch)
	usr_prefs().set_entry ('XMC_linacPitch', pitch)

################################################################

def get_XHIRES_serialNo():
	s = sys_prefs().get_entry ('XHIRES_serialNo', 'QTxxxxxxA')
	return usr_prefs().get_entry ('XHIRES_serialNo', s)

def set_XHIRES_serialNo (serialNo):
	sys_prefs().set_entry ('XHIRES_serialNo', serialNo)
	usr_prefs().set_entry ('XHIRES_serialNo', serialNo)

################################################################

def get_MGPS_serialNo():
	s = sys_prefs().get_entry ('MGPS_serialNo', 'QTxxxxxxA')
	return usr_prefs().get_entry ('MGPS_serialNo', s)

def set_MGPS_serialNo (serialNo):
	sys_prefs().set_entry ('MGPS_serialNo', serialNo)
	usr_prefs().set_entry ('MGPS_serialNo', serialNo)

################################################################

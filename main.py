#!/usr/bin/python2
# coding: utf-8

from Tkinter import *

import tkMessageBox
import tkFont

def add_libs():
	"""
	Add apps's members  to system paths
	"""
	lib = os.path.join (os.getcwd(),'lib')
	sys.path.append (lib)
	return

def add_apps():
	"""
	Add apps's members  to system paths
	"""
	apps = os.path.join (os.getcwd(),'apps')
	sys.path.append (apps)
	widgets = os.path.join (os.getcwd(), 'apps', 'widgets')
	sys.path.append (widgets)
	return

def add_ppmodes():
	"""
	Add apps's members  to system paths
	"""
	modes_dir = os.path.join (os.getcwd(),'ppsel')
	sys.path.append (modes_dir)
	modes_list = os.listdir (modes_dir)
	for mode in modes_list:
		if mode[0] != '.' :		#skip hidden files
			mode_path = os.path.join (modes_dir, mode)
			if os.path.isdir (mode_path):
				sub_modes_list = os.listdir (mode_path)
				sys.path.append (mode_path)
			else:
				continue
			#print sub_modules_list
			for sub_mode in sub_modes_list:
				sub_mode_path = os.path.join (mode_path, sub_mode)
				#print sub_module_path
				if os.path.isdir (sub_mode_path):
					sys.path.append (sub_mode_path)
	return

def add_module_path():
	module_dir = os.path.join (os.getcwd(), 'modules')
	sys.path.append (module_dir)
	modules_list = os.listdir (module_dir)
	for module in modules_list:
		if module[0] != '.' :		#skip hidden files
			module_path = os.path.join (module_dir, module)
			if os.path.isdir (module_path):
				sub_modules_list = os.listdir (module_path)
				sys.path.append (module_path)
			else:
				continue
			#print sub_modules_list
			for sub_module in sub_modules_list:
				sub_module_path = os.path.join (module_path, sub_module)
				#print sub_module_path
				if os.path.isdir (sub_module_path):
					sys.path.append (sub_module_path)
	return

def add_utilities():
	"""
	Add utilities's members to system paths
	"""
	utilities_dir = os.path.join (os.getcwd(), 'utilities')
	utilities_list = os.listdir (utilities_dir)
	for utility in utilities_list:
		if utility[0] != '.':               #skip hidden files
			full_filename = os.path.join (utilities_dir, utility)
			sys.path.append (full_filename)
	return

def add_audio():
	sys.path.append (os.path.join (os.getcwd(), 'audios'))

def main():
	"""
	Kick starts the main application
	"""
	root = Tk()

	root.option_add ("*Font", "helvetica 11")

	if not os.path.exists (Preferences.getDataFolder ()):
		os.makedirs (Preferences.getDataFolder ())

	#with splash.SplashScreen(root):
	m = QuriousGui(root)
	root.mainloop()
	Preferences.flush()
	return

class QuriousGui:
	def __init__(self, master):
		self.master = master
		self.master.title('Qrius - Happy Xploring!')
		self.master.protocol('WM_DELETE_WINDOW', self.vCloseAllWindows)
		self._create_widgets()
		return

	def _create_widgets(self):
		self._createToolbar ()
		self._createMenubar ()
		self._createSettingsWindow()
		self._createLinks()
		return

	def vHighlightWindow(self, winObj):
		winObj.deiconify()
		winObj.lift()
		return

	def vCloseAllWindows(self):
		self.oSettings.vCloseAllWindows(killall=True)
		return

	def _createToolbar (self):
		self.FrameToolBar = Frame(self.master, relief=RAISED, borderwidth=1)
		self.FrameToolBar.grid(row=0, column=0, sticky=N+W+E+S)
		self.oToolBar = toolbar.toolbar (self.FrameToolBar)
		self.master.protocol('WM_DELETE_WINDOW',self.oToolBar.BtnExitCB)
		return

	def oToolBar (self):
		"""
		Returns toolbar object
		"""
		return self.oToolBar

	def _createMenubar (self):
		"""
		Packs MenuBar Window
		"""
		self.oMenubar = menubar.menubar (self.master, self.oToolBar)
		return

	def _createSettingsWindow(self):
		"""
		Loads Scanner widgets in Scanner Window
		"""
		self.SettingsFrame = Frame(self.master, borderwidth=3)
		self.SettingsFrame.grid(row=1, column=0, sticky=N+W)
		self.oSettings = settings.settings(self.SettingsFrame)
		return

	def _createLinks(self):
		self.oToolBar.vGetMain(self, self.master)
		self.oMenubar.vGetMain(self)
		return


if __name__ == '__main__':
	import os
	os.chdir (os.path.dirname (__file__))
	add_libs()
	add_apps()
	add_module_path()
	add_utilities()
	add_ppmodes()
	add_audio()
	import toolbar
	import menubar
	import settings
	import Preferences
	main()

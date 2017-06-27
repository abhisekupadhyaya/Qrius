from Tkinter import Toplevel
from modules_constants import *
from app_modules import GUI

from tcon     import TCON     as openTCON,      closeTCON
from xsmu     import XSMU     as openXSMU,      closeXSMU
from xlia     import XLIA     as openXLIA,      closeXLIA
from XMC      import XMC      as openXMC,       closeXMC
from xhires   import XHIRES   as openXHIRES,    closeXHIRES
from mgps     import MGPS     as openMGPS,      closeMGPS
from sample   import Sample   as openSample,    closeSample
from Cryostat import Cryostat as open_cryostat, close_cryostat

def Modules (close = False):

	if not Modules.singleton:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.resizable (width = False, height = False)
		win.withdraw()

		oApp = GUI (master = win)
		Modules.singleton = _Modules (oApp = oApp)

	return Modules.singleton

def closeModules():
	if Modules.singleton:
		Modules.singleton.close()
		Modules.singleton = None

Modules.singleton = None

class _Modules:

	def __init__ (self, oApp):
		self.oApp = oApp
		oApp.callback (self.oAppCB)

	def show (self):
		win = self.oApp.master
		win.deiconify()
		win.lift()

	def hide (self):
		win = self.oApp.master
		win.withdraw()

	def oAppCB (self, context, *args):

		if context == OPEN_DEVICE : self.openDevice (*args)
		else                      : raise ValueError (context)

	def openDevice (self, device):

		sample = openSample (self)

		if   device == XTCON    : dev = self.open_tcon (sample)
		elif device == XSMU     : dev = openXSMU   (self, sample)
		elif device == XLIA     : dev = openXLIA   (self, sample)
		elif device == XMC      : dev = openXMC    (self, sample)
		elif device == XHIRES   : dev = openXHIRES (self, sample)
		elif device == MGPS     : dev = openMGPS   (self, sample)
		elif device == CRYOSTAT : dev = open_cryostat (self)
		else                    : raise ValueError (device)

		dev.show()

	def open_tcon (self, sample):
		cryostat = open_cryostat (self)
		return openTCON (self, sample, cryostat)

	def close (self):
		closeTCON   (self)
		closeXSMU   (self)
		closeXLIA   (self)
		closeXMC    (self)
		closeXHIRES (self)
		closeMGPS   (self)
		closeSample (self)
		self.oApp.master.destroy()

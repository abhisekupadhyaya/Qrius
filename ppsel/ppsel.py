from Tkinter import Toplevel
from app_ppsel import GUI
from ppsel_constants import *

from res      import RES      as openRES,       closeRES
from hires    import HIRES    as openHIRES,     closeHIRES
from sus      import SUS      as openSUS,       closeSUS
from tcon     import TCON     as openTCON,      closeTCON
from xsmu     import XSMU     as openXSMU,      closeXSMU
from xlia     import XLIA     as openXLIA,      closeXLIA
from XMC      import XMC      as openXMC,       closeXMC
from xhires   import XHIRES   as openXHIRES,    closeXHIRES
from sample   import Sample   as openSample,    closeSample
from mgps     import MGPS     as openMGPS,      closeMGPS
from Cryostat import Cryostat as open_cryostat, close_cryostat

def PPSel():

	if PPSel.singleton == None:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.resizable (width = False, height = False)
		win.withdraw()

		oApp = GUI (master = win)
		PPSel.singleton = _PPSel (oApp = oApp)

	return PPSel.singleton

def closePPSel():
	if PPSel.singleton:
		PPSel.singleton.close()
		PPSel.singleton = None

PPSel.singleton = None

class _PPSel:

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

		if context == OPEN_MODULE : self.openModule (*args)
		else                      : raise ValueError (context)

	def openModule (self, module):

		if   module == RESISTIVITY      : self.openRES()
		elif module == HIGH_RESISTIVITY : self.openHIRES()
		elif module == SUSCEPTIBILITY   : self.openSUS()
		else                            : raise ValueError (module)

	def openRES (self):
		sample   = openSample (self)
		cryostat = open_cryostat (self)
		tcon     = openTCON (self, sample, cryostat)
		xsmu     = openXSMU (self, sample)
		mgps     = openMGPS (self, sample)
		res      = openRES  (self, tcon, xsmu, mgps, sample, cryostat)
		res.show()

	def openHIRES (self):
		sample   = openSample (self)
		cryostat = open_cryostat (self)
		tcon     = openTCON (self, sample, cryostat)
		xhires   = openXHIRES (self, sample)
		hires    = openHIRES  (self, tcon, xhires, sample, cryostat)
		hires.show()

	def openSUS (self):
		sample = openSample (self)
		cryostat = open_cryostat (self)
		tcon     = openTCON (self, sample, cryostat)
		xlia     = openXLIA   (self, sample)
		xmc      = openXMC    (self, sample)
		sus      = openSUS    (self, tcon, xlia, xmc, sample, cryostat)
		sus.show()

	def close (self):
		closeRES       (self)
		closeSUS       (self)
		closeTCON      (self)
		closeXSMU      (self)
		closeXLIA      (self)
		closeXMC       (self)
		closeXHIRES    (self)
		closeSample    (self)
		closeMGPS      (self)
		close_cryostat (self)
		self.oApp.master.destroy()

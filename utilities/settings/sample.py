from Tkinter          import Toplevel
from threading        import RLock
from app_sample       import GUI
from sample_constants import *
from Preferences      import setSampleDetails, getSampleDetails

def Sample (master):

	if not Sample.singleton:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.resizable (width = False, height = False)
		win.withdraw()

		oApp = GUI (master = win)
		Sample.singleton = _Sample (oApp)

	if master not in Sample.master:
		Sample.master.append (master)

	return Sample.singleton

def closeSample (master):

	if master in Sample.master:
		Sample.master.remove (master)

	if len (Sample.master) == 0 and Sample.singleton:
		Sample.singleton.close()
		Sample.singleton = None

Sample.singleton = None
Sample.master    = []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class SampleDetails:

	def __init__ (self):
		self.name        = 'Sample'
		self.ident       = '1'
		self.description = ''

	def set (self, name, ident, description):
		self.name        = name
		self.ident       = ident
		self.description = description

	def get (self):
		return (self.name,
				self.ident,
				self.description)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Sample:

	def __init__ (self, oApp):
		self.oApp    = oApp
		self._thlock = RLock()
		self.sampleDetails = SampleDetails()

		details = getSampleDetails()
		if type (details) == tuple: self.populateSampleDetails (*details)
		else                      : self.populateSampleDetails ()

		oApp.callback (self.oAppCB)
		self.oApp.set (*self.sampleDetails.get())

	def acquire_lock (self):
		self._thlock.acquire()

	def release_lock (self):
		self._thlock.release()

	def show (self):
		self.oApp.master.deiconify()

	def hide (self):
		self.oApp.master.withdraw()

	def close (self):
		self.oApp.master.destroy()

	# ++++ GUI callbacks ++++

	def oAppCB (self, context, *args):
		if   context == NEW    : self.newCB    ()
		elif context == APPLY  : self.applyCB  (*args)
		elif context == CANCEL : self.cancelCB ()
		else                   : raise ValueError (context)

	def newCB (self):
		self.oApp.set (*SampleDetails().get())

	def applyCB (self, *args):
		self.sampleDetails.set (*args)
		setSampleDetails (*self.sampleDetails.get())
		self.hide()

	def cancelCB (self):
		self.oApp.set (*self.sampleDetails.get())
		self.hide()

	# ++++ set/get/save/load ++++

	def populateSampleDetails (self, *args):

		(_name, _ident, _desc) = SampleDetails().get()

		# ++++ Sample name ++++
		try                          : name = str (args[0])
		except IndexError, TypeError : name = _name

		# ++++ Sample ID ++++
		try                          : ident = str (args[1])
		except IndexError, TypeError : ident = _ident

		# ++++ Sample description ++++
		try                          : desc = str (args[2])
		except IndexError, TypeError : desc = _desc

		self.sampleDetails.set (name, ident, desc)

	def get (self):
		self._thlock.acquire()
		sample = self.sampleDetails.get()
		self._thlock.release()
		return sample

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

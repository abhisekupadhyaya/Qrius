from Cryostat_Constants import *
from Cryostat_UI        import *
from Cryostat_Method    import Method, XMethodError

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def Cryostat (master):

	if not Cryostat.singleton:

		win = Toplevel (takefocus = True)
		win.protocol ('WM_DELETE_WINDOW', win.withdraw)
		win.withdraw()
		ui = UI (win)

		Cryostat.singleton = _Cryostat (ui)

	if master not in Cryostat.master:
		Cryostat.master.append (master)

	return Cryostat.singleton

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def close_cryostat (master):

	if master in Cryostat.master:
		Cryostat.master.remove (master)

	if len (Cryostat.master) == 0 and Cryostat.singleton:
		Cryostat.singleton.close()
		Cryostat.singleton = None

Cryostat.singleton = None
Cryostat.master    = []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class _Cryostat:

	def __init__ (self, ui):

		self.cryostat_type = CRYOSTAT_TYPE_GENERIC
		self.insert_type   = INSERT_TYPE_GENERIC

		ui.callback (self.ui_cb)
		self.ui = ui

	def show (self):
		win = self.ui.master
		win.deiconify()
		win.lift()

	def hide (self):
		win = self.ui.master
		win.withdraw()

	def close (self):
		self.ui.master.destroy()

	def ui_cb (self, context, *args):

		if context == REASON_CRYOSTAT_TYPE:
			self.cryostat_type = args[0]

		elif context == REASON_INSERT_TYPE:
			self.insert_type = args[0]

		else: raise ValueError (context)

	def set_cryostat_type (self, value):
		self.cryostat_type = value
		self.ui.set_cryostat_type (value)

	def set_insert_type (self, value):
		self.insert_type = value
		self.ui.set_insert_type (value)

	def temperature_remap (self, heater_temperature, sample_temperature):

		sensor_dict = {

			INSERT_TYPE_GENERIC   : (
				heater_temperature, sample_temperature),

			INSERT_TYPE_RT        : (
				heater_temperature, sample_temperature),

			INSERT_TYPE_XT        : (
				heater_temperature, sample_temperature),

			INSERT_TYPE_RT_HIRES  : (
				heater_temperature, sample_temperature),

			INSERT_TYPE_RT_HEATER : (
				heater_temperature, heater_temperature),

			INSERT_TYPE_RT_HEATER_PUCK : (
				heater_temperature, sample_temperature)
		}

		return sensor_dict.get (self.insert_type)

	def get_method (self):
		method = Method()
		method.set_cryostat_type (self.cryostat_type)
		method.set_insert_type   (self.insert_type)
		return method

	def apply_method (self, method):

		self.set_cryostat_type (
			method.get_cryostat_type (self.cryostat_type))

		self.set_insert_type (
			method.get_insert_type (self.insert_type))

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

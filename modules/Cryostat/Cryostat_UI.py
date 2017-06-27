# coding: utf-8
from Tkinter import *
from Cryostat_Constants import *

class UI:

	cryostat_type_menuitems = {

		CRYOSTAT_TYPE_GENERIC   :
			'Double walled steel cryostat',

		CRYOSTAT_TYPE_QUARTZ    :
			'Quartz cryostat with electro-magnet'
	}

	insert_type_menuitems = {

		INSERT_TYPE_GENERIC     : 'Generic insert',
		INSERT_TYPE_RT          : 'R-T insert',
		INSERT_TYPE_XT          : u'χ-T insert',
		INSERT_TYPE_RT_HIRES    : 'R-T high resistance insert',
#		INSERT_TYPE_RT_HEATER   : 'R-T insert with heater',
		INSERT_TYPE_RT_HEATER_PUCK :
			'R-T insert with heater and sample puck'
	}

	def __init__ (self, master):
		self.master = master
		self.master.title ('Cryostat configuration')
		self.create_widgets (master)
		self.set_cryostat_type (CRYOSTAT_TYPE_GENERIC)
		self.set_insert_type (INSERT_TYPE_GENERIC)

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def create_widgets (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 200)
		master.grid_rowconfigure    (0, weight = 1, minsize = 100)
		master.grid_rowconfigure    (1, weight = 1, minsize = 100)

		self.populate_menu (master)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Cryostat')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populate_cryostat_widgets (w)

		row += 1; col = 0
		w = LabelFrame (master, text = 'Insert')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populate_insert_widgets (w)

	def populate_menu (self, master):

		self.mainmenu = Menu (master)
		self.mainmenu.config (borderwidth = 1)
		master.config (menu = self.mainmenu)

		### File Menu
		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		# ++++ Populating file menu ++++

		self.filemenu.add_command (label = 'Hide', command = self.hide_cb);

	def populate_cryostat_widgets (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 100)
		master.grid_columnconfigure (1, weight = 0, minsize = 400)

		row = 0; col = 0
		w = Label (master, text = 'Type: ', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

		col += 1
		var = self.cryostat_type = StringVar()
		options = self.cryostat_type_menuitems.values()

		w = self.ui_cryostat_type = OptionMenu (
			master, var, *options, command = self.cryostat_type_cb)

		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

	def populate_insert_widgets (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 100)
		master.grid_columnconfigure (1, weight = 0, minsize = 400)

		row = 0; col = 0
		w = Label (master, text = 'Type: ', anchor = E)
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

		col += 1
		var = self.insert_type = StringVar()
		options = self.insert_type_menuitems.values()

		w = self.ui_insert_type = OptionMenu (
			master, var, *options, command = self.insert_type_cb)

		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)

	def set_cryostat_type (self, value):
		self.cryostat_type.set (
			self.cryostat_type_menuitems.get (value));

	def set_insert_type (self, value):
		self.insert_type.set (
			self.insert_type_menuitems.get (value));

	def hide_cb (self):
		self.master.withdraw()

	def cryostat_type_cb (self, *args):
		self.do_callback (REASON_CRYOSTAT_TYPE, self.get_cryostat_type())

	def insert_type_cb (self, *args):
		self.do_callback (REASON_INSERT_TYPE, self.get_insert_type())

	def get_cryostat_type (self):
		rdict = { v : k for k, v in self.cryostat_type_menuitems.items() }
		return rdict.get (self.cryostat_type.get())

	def get_insert_type (self):
		rdict = { v : k for k, v in self.insert_type_menuitems.items() }
		return rdict.get (self.insert_type.get())

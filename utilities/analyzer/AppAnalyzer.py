import os
import Preferences
from Tkinter      import Frame, W, E, NSEW, Button, Toplevel, Menu, Text
from Tkinter      import OptionMenu, StringVar, Label, LabelFrame
from Tkinter      import END, LEFT, DISABLED, NORMAL
from XWidget      import XScroll
from XDict        import XDict, XDictError
from Plot2D       import Plot2D
from tkFileDialog import askopenfile
from time         import time as systime, localtime

class AppAnalyzer (Frame):

	def __init__ (self, master):
		Frame.__init__ (self, master)

		self.run = None
		self.filename = None

		master.title ('Qrius: Analyzer')
		master.protocol ('WM_DELETE_WINDOW', self.wQuitCB)
		self.populateMenu (master)

		master.grid_columnconfigure (0, weight = 1)
		master.grid_rowconfigure    (0, weight = 1)
		self.createWidgets (self)

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 0, minsize = 250)
		master.grid_columnconfigure (1, weight = 1, minsize = 650)
		master.grid_rowconfigure    (0, weight = 1)
		master.grid_rowconfigure    (1, weight = 0)

		row = 0; col = 0
		w = XScroll (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populateAxisPanel (w.interior)

		col += 1
		w = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		self.populatePlotPanel (w)

		row += 1; col = 0
		w = Frame (master)
		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)
		self.populateStatusPanel (w)

	def populateMenu (self, master):

		### Main Menu
		self.mainmenu = Menu (master)
		self.mainmenu.config (borderwidth = 1)
		master.config (menu = self.mainmenu)

		# ++++++++++++++++++++++++++++++++++++++++++++++++++

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)

		self.filemenu.add_command (label = 'Open', command = self.wOpenFileCB)
		self.filemenu.add_command (label = 'Export', command = self.wExportCB)
		self.filemenu.add_separator()
		self.filemenu.add_command (label = 'Exit', command = self.wQuitCB)

	def populateAxisPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = LabelFrame (master, text = 'Axes')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateAxesFrame (w)

		row += 1
		w = LabelFrame (master, text = 'Available fields')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateFieldsFrame (w)

		row += 1
		w = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateButtonFrame (w)

		row += 1
		w = LabelFrame (master, text = 'Sample details')
		w.grid (row = row, column = col, sticky = NSEW, padx = 5, pady = 5)
		self.populateSampleFrame (w)

	def populateAxesFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = Label (master, text = 'X axis:', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1
		var = self.XAxis = StringVar (value = '...')
		w = self.wXAxes = OptionMenu (master, var, var.get())
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.rowXAxes = row
		self.colXAxes = col

		row += 1
		w = Label (master, text = 'Y axis:', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1
		var = self.YAxis = StringVar (value = '...')
		w = self.wYAxes = OptionMenu (master, var, var.get())
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)
		self.rowYAxes = row
		self.colYAxes = col

	def populateFieldsFrame (self, master):

		master.grid_columnconfigure (0, weight = 1)

		row = 0; col = 0
		w = self.wFields = Label (
			master, text = '...', anchor = W, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)

	def populateButtonFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 100)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)

		row = 0; col = 0
		w = Button (master, text = 'Clear', command = self.wClearPlotCB)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Button (master, text = 'Add', command = self.wPlotDataCB)
		w.grid (row = row, column = col, sticky = NSEW)

	def populateSampleFrame (self, master):

		master.grid_columnconfigure (0, weight = 1, minsize = 100)
		master.grid_columnconfigure (1, weight = 1, minsize = 100)

		# Sample name

		row = 0; col = 0
		w = Label (master, text = 'Name', anchor = W, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = '...', anchor = E, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)
		self.wSampleName = w

		# Sample ID

		row += 1; col = 0
		w = Label (master, text = 'ID', anchor = W, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)

		col += 1
		w = Label (master, text = '...', anchor = E, justify = LEFT)
		w.grid (row = row, column = col, sticky = NSEW)
		self.wSampleID = w

		# Sample description

		row += 1; col = 0
		w = Label (master, text = 'Description', anchor = W, justify = LEFT)
		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)

		row += 1; col = 0
		w = Text (master, width = 20, state = DISABLED)
		w.grid (row = row, column = col, columnspan = 2, sticky = NSEW)
		self.wSampleDescription = w

	def populatePlotPanel (self, master):

		master.grid_rowconfigure    (0, weight = 1)
		master.grid_columnconfigure (0, weight = 1)
		w = self.wPlot = Plot2D (master)

	def populateStatusPanel (self, master):

		master.grid_columnconfigure (0, weight = 1)
		row = 0; col = 0
		w = self.wStatus = Label (master, text = '...', anchor = W, width = 30)
		w.grid (row = row, column = col, sticky = NSEW)

	def wQuitCB (self):
		self.master.destroy()

	def wOpenFileCB (self):

		filetypes = [
			('XPLORE file', '*.xpl'),
			('Old XPLORE file', '*.xp*'),
			('All files', '*.*')
		]

		try:

			folder = (os.path.dirname (self.filename)
			   if self.filename != None else Preferences.getDataFolder())

			fd = askopenfile (
				parent     = self.master,
				initialdir = folder,
				filetypes  = filetypes)

			if fd != None:

				self.filename = fd.name
				self.run = XDict (fd)
				fd.close()

				self.master.title (self.filename)
				self.populateAxes (self.run.data_keys())

				sample = self.run.sample()
				if type (sample) == tuple : self.populateSample (*sample)
				else                      : self.populateSample ()

				#self.wPlot.clear()
				#self.wPlot.redraw()

		except (OSError, IOError) as e:
			text = 'Open failed: ' + str (e)
			self.set_status (text)

		except XDictError as e:
			text = 'Open failed: ' + str (e) + ' ' + str (e)
			self.set_status (text)

	def wExportCB (self):

		try:

			if self.run == None : return

			# +++++++ Generate table in RAM +++++++

			units     = []
			columns   = []
			data_keys = self.run.data_keys()

			for key in data_keys:
				(data, unit) = self.run.get_data (key)
				units.append (unit)
				columns.append (data)

			# +++++++ Open export file +++++++

			(filename, extension) = os.path.splitext (self.filename)
			filename = filename + os.extsep + 'csv'
			fd = open (filename, 'w')

			# +++++++ Save sample details +++++++

			sample = self.run.sample()
			if type (sample) == tuple:

				# ++++ Sample name ++++

				try                          : name = str (sample[0])
				except IndexError, TypeError : name = '...'
				fd.write ('#Sample name: ' + name + '\n')

				# ++++ Sample ID ++++

				try                          : ident = str (sample[1])
				except IndexError, TypeError : ident = '...'
				fd.write ('#Sample ID: ' + ident + '\n')

				# ++++ Sample description ++++

				try                          : desc = str (sample[2])
				except IndexError, TypeError : desc = '...'
				label = '#Sample description: '
				desc = desc.replace ('\n', '\n' + label)
				fd.write (label + desc + '\n')

			# +++++++ Save headers +++++++

			line = ''
			for key in data_keys:
				line += ',' if (len (line) > 0) else '#'
				line += key
			line += '\n'
			fd.write (line)

			# +++++++ Save Units +++++++

			line = ''
			for unit in units:
				line += ',' if (len (line) > 0) else '#'
				line += unit
			line += '\n'
			fd.write (line)

			# +++++++ Save data +++++++

			for row in range (0, len (columns[0])):
				line = ''
				for col in range (0, len (columns)):
					line += ',' if (len (line) > 0) else ''
					line += str (columns[col][row])
				line += '\n'
				fd.write (line)

			# +++++++ Pack up +++++++

			fd.close()
			self.set_status ('Exported to: ' + fd.name)

		except (OSError, IOError) as e:
			text = 'Export error: ' + str (e)
			set_status (text)

	def wPlotDataCB (self, *args):

		if self.run == None : return

		keyx = self.XAxis.get()
		keyy = self.YAxis.get()
		data_keys = self.run.data_keys (omit_zeros = True)

		if all (key in data_keys for key in (keyx, keyy)):

			datax, unitx = self.run.get_data (keyx)
			datay, unity = self.run.get_data (keyy)

			unitx = '' if unitx == None else unitx
			unity = '' if unity == None else unity

			self.wPlot.xlabel (keyx + ' (' + unitx + ')')
			self.wPlot.ylabel (keyy + ' (' + unity + ')')
			self.wPlot.add_dataset (self.wPlot.new_dataset(), datax, datay)
			self.wPlot.redraw()

	def wClearPlotCB (self, *args):
		self.wPlot.clear()
		self.wPlot.redraw()

	def populateAxes (self, fields):

		text = ''
		for field in fields:
			text += ('\n' if len (text) > 0 else '') + field

		self.wFields['text'] = text

		# +++++++++++++++++++++++++++++++++++++++++++

		old_menu  = self.wXAxes
		row = self.rowXAxes; col = self.colXAxes
		old_menu.grid_forget()

		var = self.XAxis = StringVar (value = '...')
		w = self.wXAxes = OptionMenu (old_menu.master, var, *fields)
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++++++++++++++

		old_menu  = self.wYAxes
		row = self.rowYAxes; col = self.colYAxes
		old_menu.grid_forget()

		var = self.YAxis = StringVar (value = '...')
		w = self.wYAxes = OptionMenu (old_menu.master, var, *fields)
		w.config (anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		# +++++++++++++++++++++++++++++++++++++++++++

	def set_status (self, text):

		lt = localtime (systime())
		time_stamp = (
			str ('%02d' % lt.tm_hour) + ':' +
			str ('%02d' % lt.tm_min)  + ':' +
			str ('%02d' % lt.tm_sec))

		old_text = self.wStatus['text']
		new_text = '<' + time_stamp + '> ' + text + '    .    ' + old_text
		new_text = new_text[:1024]
		self.wStatus.config (text = new_text)

	def populateSample (self, *args):

		# ++++ Sample name ++++
		try                          : name = str (args[0])
		except IndexError, TypeError : name = '...'
		self.wSampleName.config (text = name)

		# ++++ Sample ID ++++
		try                          : ident = str (args[1])
		except IndexError, TypeError : ident = '...'
		self.wSampleID.config (text = ident)

		# ++++ Sample description ++++
		try                          : desc = str (args[2])
		except IndexError, TypeError : desc = ''
		w = self.wSampleDescription
		w.config (state = NORMAL)
		w.delete (0.0, END)
		w.insert (0.0, desc)
		w.config (state = DISABLED)

from Tkinter import Menu, LabelFrame, Label, Entry, Text
from Tkinter import N, S, E, W, NSEW, LEFT, END, StringVar
from sample_constants import *

class GUI:

	def __init__(self, master):
		self.master = master
		self.master.title ('Sample details')
		self.createWidgets()

	def callback (self, cb):
		self._callback = cb

	def do_callback (self, context, *args):
		if hasattr (self, '_callback'):
			self._callback (context, *args)

	def createWidgets (self):

		### Main Menu
		self.mainmenu = Menu (self.master)
		self.mainmenu.config (borderwidth = 1)
		self.master.config (menu = self.mainmenu)

		self.filemenu = Menu (self.mainmenu)
		self.filemenu.config (tearoff = 0)
		self.mainmenu.add_cascade (
			label = 'File', menu = self.filemenu, underline = 0)
		self.filemenu.add_command (
			label = 'New', command = self.wNewCB)
		self.filemenu.add_command (
			label = 'Apply', command = self.wApplyCB)
		self.filemenu.add_command (
			label = 'Cancel', command = self.wCancelCB)

		self.master.grid_rowconfigure (0, weight = 1)
		self.master.grid_columnconfigure (0, weight = 1)

		# ++++ Temperature settings ++++
		w = wFrame = LabelFrame (self.master, text = 'Sample details')

		w.grid (row = 0, column = 0, sticky = NSEW, padx = 5, pady = 5)
		w.grid_columnconfigure (0, weight = 0)
		w.grid_columnconfigure (1, weight = 1)

		# ++++ Sample name ++++
		row = 0; col = 0
		w = Label (wFrame, text = 'Name:', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		self.sampleName = StringVar()
		w = self.wName = Entry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT,
				textvariable = self.sampleName)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++ Sample ID ++++
		row += 1; col = 0
		w = Label (wFrame, text = 'ID:', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		self.sampleID = StringVar()
		w = self.wIdent = Entry (
				wFrame, bg = 'white', width = 10,
				borderwidth = 2, justify = LEFT,
				textvariable = self.sampleID)
		w.grid (row = row, column = col, sticky = NSEW)

		# ++++ Sample description ++++
		row += 1; col = 0
		w = Label (wFrame, text = 'Description:', anchor = W)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = self.wDescription = Text (wFrame)
		w.grid (row = row, column = col, sticky = NSEW)

	def wNewCB (self):
		self.do_callback (NEW)

	def wApplyCB (self):
		self.do_callback (APPLY, self.sampleName.get(),
						  self.sampleID.get(), self.wDescription.get (1.0, END))

	def wCancelCB (self):
		self.do_callback (CANCEL)

	def set (self, *args):
		(name, ident, desc) = args
		self.sampleName.set (name)
		self.sampleID.set (ident)
		self.wDescription.delete (1.0, END)
		self.wDescription.insert (1.0, desc)

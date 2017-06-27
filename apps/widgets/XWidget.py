from Tkinter import END
from tkValidatingEntry import ValidatingEntry

class XEntry (ValidatingEntry):

	WHEN_NEVER = 0
	WHEN_CHANGED = 1
	WHEN_ALWAYS = 2

	def __init__ (self, master = None, value = '', **kw):
		ValidatingEntry.__init__ (self, master, value, **kw)
		self.bind ('<Key>',      self._keyCB)
		self.bind ('<Return>',   self._returnCB)
		self.bind ('<FocusOut>', self._focusOutCB)
		self._cb      = None
		self._value   = value
		self._colored = True
		self._fmt     = None
		self._when    = self.WHEN_CHANGED

	def callback (self, cb = None, when = WHEN_CHANGED):
		"""
		def cb (widget, event)
			widget: Returns a reference to current widget
			event:  Returns the event which caused the callback
		"""
		self._cb = cb
		self._when = when

	def do_callback (self, event = None):
		self.set (self.get())
		self.configure (bg = 'peach puff' if self._colored else self['bg'])
		if self._cb is not None:
			self._cb (self, event)

	def fmt (self, fmt):
		self._fmt = fmt

	def get (self):
		return self._value

	def set (self, value, successful = True):
		"""
		Sets widget text to the supplied value.
		If 'successful', sets background colour to yellow, else to red.
		"""
		self._set (value)
		bg = 'yellow' if successful else 'peach puff'
		self.configure (bg = bg if self._colored else self['bg'])

	def set_failed (self, value):
		"""
		Sets widget text to supplied value and background to red
		"""
		self._set (value)
		self.configure (bg = 'peach puff' if self._colored else self['bg'])

	def _set (self, value):
		self._value = (str (self._fmt % value)
			if self._fmt is not None else str (value)).strip()
		self.delete (0, END)
		self.insert (0, self._value)

	def enable_color (self, enable = True):
		"""
		Enable/disable colour changing feature
		"""
		self._colored = enable

	def _keyCB (self, event):
		self.configure (bg = 'white' if self._colored else self['bg'])

	def _returnCB (self, event):
		self._value = ValidatingEntry.get (self)

		if self._when == self.WHEN_NEVER:
			pass

		elif self._when == self.WHEN_CHANGED:
			self.do_callback (event)

		elif self._when == self.WHEN_ALWAYS:
			self.do_callback (event)

	def _focusOutCB (self, event):
		value = ValidatingEntry.get (self)

		if self._when == self.WHEN_NEVER:
			pass

		elif self._when == self.WHEN_CHANGED:
			if (value != self._value):
				self._value = value
				self.do_callback (event)

		elif self._when == self.WHEN_ALWAYS:
			self._value = value
			self.do_callback (event)

	def validate (self, value):
		return Value

class XFloatEntry (XEntry):

	def get (self):
		try:
			value = float (self._value)
		except ValueError:
			value = 0.0
		return value

	def validate (self, value):
		for c in value:
			if c not in '0123456789+-.e':
				return None
		return value

class XIntegerEntry (XEntry):

	def get (self):
		try:
			value = int (self._value)
		except ValueError:
			value = 0
		return value

	def validate (self, value):
		for c in value:
			if c not in '0123456789+-':
				return None
		return value

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from Tkinter import Scrollbar, Canvas, Frame
from Tkinter import VERTICAL, RIGHT, FALSE, LEFT, BOTH, TRUE, Y, NW

class XScroll (Frame):
	'''
		A pure Tkinter scrollable frame!
		Populate self.interior as a frame.

		Taken from:
		http://stackoverflow.com/questions/
			16188420/python-tkinter-scrollbar-for-frame
	'''

	def __init__ (self, parent, *args, **kw):
		Frame.__init__ (self, parent, *args, **kw)

		# create a canvas object and a vertical scrollbar for scrolling it
		vscrollbar = Scrollbar (self, orient = VERTICAL)
		vscrollbar.pack (fill = Y, side = RIGHT, expand = FALSE)

		canvas = Canvas (
			self, bd = 0, highlightthickness = 0,
			yscrollcommand = vscrollbar.set)

		canvas.pack (side = LEFT, fill = BOTH, expand = TRUE)

		vscrollbar.config (command = canvas.yview)

		# reset the view
		canvas.xview_moveto (0)
		canvas.yview_moveto (0)

		# create a frame inside the canvas which will be scrolled with it
		self.interior = interior = Frame (canvas)
		interior_id = canvas.create_window (
			0, 0, window = interior, anchor = NW)

		# track changes to the canvas and frame width and sync them,
		# also updating the scrollbar
		def _configure_interior (event):

			# update the scrollbars to match the size of the inner frame
			size =  (interior.winfo_reqwidth(), interior.winfo_reqheight())
			canvas.config (scrollregion = "0 0 %s %s" % size)
			if interior.winfo_reqwidth() !=  canvas.winfo_width():
				# update the canvas's width to fit the inner frame
				canvas.config (width = interior.winfo_reqwidth())

		interior.bind ('<Configure>', _configure_interior)

		def _configure_canvas (event):

			if interior.winfo_reqwidth() !=  canvas.winfo_width():
				# update the inner frame's width to fill the canvas
				canvas.itemconfigure (interior_id, width = canvas.winfo_width())

		canvas.bind ('<Configure>', _configure_canvas)

from Tkinter import Frame, Button, NSEW
import tkFont

class XTab (Frame):

	def __init__ (self, parent, *args, **kw):
		Frame.__init__ (self, parent, *args, **kw)
		self.createWidgets (self)
		self.tag_data = {}

	def createWidgets (self, master):

		master.grid_columnconfigure (0, weight = 1)
		master.grid_rowconfigure    (0, weight = 0)
		master.grid_rowconfigure    (1, weight = 1)

		row = 0; col = 0
		w = self.wTagFrame = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW)

		row += 1; col = 0
		w = self.wBodyFrame = Frame (master)
		w.grid (row = row, column = col, sticky = NSEW)
		w.grid_columnconfigure (0, weight = 1)
		w.grid_rowconfigure    (0, weight = 1)

	def add (self, name):

		row = 0; col = len (self.tag_data)
		wTag = Button (self.wTagFrame, text = name)
		wTag.config (command = lambda : self.wTagCB (wTag))
		wTag.grid (row = row, column = col, sticky = NSEW)

		wFrame = Frame (self.wBodyFrame)
		wFrame.grid_columnconfigure (0, weight = 1)
		wFrame.grid_rowconfigure    (0, weight = 1)
		self.tag_data[wTag] = wFrame

		self.select (wFrame)
		return wFrame

	def select (self, frame):

		for wTag in self.tag_data : self.update_font (wTag, style = 'normal')
		for wFrame in self.tag_data.values() : wFrame.grid_forget()

		frame_data = {v : k for (k, v) in self.tag_data.items()}
		wTag = frame_data.get (frame)

		self.update_font (wTag, style = 'bold')
		frame.grid (row = 0, column = 0, sticky = NSEW)

	def clear (self):
		for (wTag, wFrame) in self.tag_data.items():
			for w in (wTag, wFrame) : w.destroy()

		self.tag_data.clear()

	def wTagCB (self, wTag):
		self.select (self.tag_data.get (wTag))

	def update_font (self, widget, mul = 1, style = 'bold'):
		font = widget['font']
		(name, sep, font) = font.strip().partition (' ')
		(size, sep, font) = font.strip().partition (' ')
		widget['font'] = name + ' ' + size + ' ' + style

class XFrame (Frame):

	def __init__ (self, parent, *args, **kw):
		Frame.__init__ (self, parent, *args, **kw)
		self.grid()
		self._hidden = False

	def update_frame (self):

		slaves = self.grid_slaves()
		self._hidden = True if len (slaves) == 0 else False

		if self._hidden : self.grid_remove ()
		else            : self.grid ()

	def hidden (self):
		return self._hidden

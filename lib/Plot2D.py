import os
import numpy as np
from matplotlib import rc
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
from Tkinter import TOP, BOTH

class QNavigationToolbar2TkAgg (NavigationToolbar2TkAgg):

	def __init__ (self, canvas, window):

		logx_icon = os.path.join (os.getcwd(), 'lib', 'log_x')
		logy_icon = os.path.join (os.getcwd(), 'lib', 'log_y')
		grid_icon = os.path.join (os.getcwd(), 'lib', 'grid_xy')

		self.toolitems = (
			('Home', 'Reset original view', 'home', 'home'),
			('Back', 'Previous view', 'back', 'back'),
			('Forward', 'Next view', 'forward', 'forward'),
			(None, None, None, None),
			('Pan', 'Pan', 'move', 'pan'),
			('Zoom', 'Zoom', 'zoom_to_rect', 'zoom'),
			(None, None, None, None),
			('Subplots', 'Configure', 'subplots', 'configure_subplots'),
			('Save', 'Save figure', 'filesave', 'save_figure'),
			('Log X', 'Toggle log X', logx_icon, 'logx_cb'),
			('Log Y', 'Toggle log Y', logy_icon, 'logy_cb'),
			('Grid XY', 'Toggle grid', grid_icon, 'grid_cb'),
		)

		NavigationToolbar2TkAgg.__init__ (self, canvas, window)

		self._homeCB = self.defaultHomeCB
		self._panCB  = self.defaultPanCB
		self._zoomCB = self.defaultZoomCB
		self._logx_cb = None
		self._logy_cb = None
		self._grid_cb = None

	def home (self, *args):
		NavigationToolbar2TkAgg.home (self, args)
		self._homeCB()

	def pan (self, *args):
		NavigationToolbar2TkAgg.pan (self, args)
		self._panCB()

	def zoom (self, *args):
		NavigationToolbar2TkAgg.zoom (self, args)
		self._zoomCB()

	def homeCB (self, homeCB):
		self._homeCB = homeCB

	def panCB (self, panCB):
		self._panCB = panCB

	def zoomCB (self, zoomCB):
		self._zoomCB = zoomCB

	def defaultHomeCB (self):
		return

	def defaultPanCB (self):
		return

	def defaultZoomCB (self):
		return

	def set_logx_cb (self, value):
		self._logx_cb = value

	def logx_cb (self):
		if self._logx_cb: self._logx_cb()

	def set_logy_cb (self, value):
		self._logy_cb = value

	def logy_cb (self):
		if self._logy_cb: self._logy_cb()

	def set_grid_cb (self, value):
		self._grid_cb = value

	def grid_cb (self):
		if self._grid_cb: self._grid_cb()

class Plot2D:

	def __init__ (self, master):

		self.master  = master

		self.fig = Figure() # self.plt.figure()
		self.plt = self.fig.add_subplot (1, 1, 1)
		#self.plt.subplot (1, 1, 1)

		canvas = FigureCanvasTkAgg (self.fig, master = self.master)
		canvas.show()
		canvas.get_tk_widget().pack (side = TOP, fill = BOTH, expand = 1)

		toolbar = QNavigationToolbar2TkAgg (canvas, self.master)
		toolbar.update()
		canvas._tkcanvas.pack(side = TOP, fill = BOTH, expand=1)

		toolbar.homeCB (self.homeCB)
		toolbar.panCB (self.panCB)
		toolbar.zoomCB (self.zoomCB)
		toolbar.set_logx_cb (self.logx_cb)
		toolbar.set_logy_cb (self.logy_cb)
		toolbar.set_grid_cb (self.grid_cb)

		toolbar.pack (fill = BOTH)

		self.plt.autoscale (True)
		self._damaged   = True
		self.last_style = None
		self.logx       = False
		self.logy       = False
		self.grid       = False

	def damage (self):
		self._damaged = True

	def damaged (self):
		return self._damaged

	def xlabel (self, label):
		self.select_this()
		self.plt.set_xlabel (label.decode ('utf-8'))

	def ylabel (self, label):
		self.select_this()
		self.plt.set_ylabel (label.decode ('utf-8'))

	def title (self, title):
		self.select_this()
		self.plt.set_title (title.decode ('utf-8'))

	def xscale (self, scale = 'linear'): # 'linear' or 'log'
		self.select_this()
		self.plt.set_xscale (scale)
		self.logx = False if scale == 'linear' else True

	def yscale (self, scale = 'linear'): # 'linear' or 'log'
		self.select_this()
		self.plt.set_yscale (scale)
		self.logy = False if scale == 'linear' else True

	def new_dataset (self, style = None, label = None):
		'''
		r: red
		g: green
		b: blue
		c: cyan
		m: magenta
		k: black
		'''

		if style == None:
			styles = ['r-', 'g-', 'b-', 'c-', 'm-', 'k-']
			style = self.last_style = styles[
				0 if self.last_style == None
				else (styles.index (self.last_style) + 1)]

		self.select_this()
		blank_dataset = []
		self.plt.plot (blank_dataset, blank_dataset, style, label = label)
		if label: self.plt.legend()
		return len (self.fig.gca().lines) - 1

	def add_datapoint (self, traceId, x, y):
		self.select_this()
		trace = self.fig.gca().lines[traceId]
		trace.set_xdata (np.append (trace.get_xdata(), x))
		trace.set_ydata (np.append (trace.get_ydata(), y))

	def add_dataset (self, traceId, x, y):
		self.select_this()
		trace = self.fig.gca().lines[traceId]
		trace.set_xdata (np.append (trace.get_xdata(), x))
		trace.set_ydata (np.append (trace.get_ydata(), y))

	def clear_dataset (self, traceId):
		self.select_this()
		blank_dataset = []
		trace = self.fig.gca().lines[traceId]
		trace.set_data (blank_dataset, blank_dataset)

	def redraw (self):
		self.select_this()

		if self.plt.get_autoscale_on():
			self.plt.relim()
			self.plt.autoscale_view()

		self.fig.canvas.draw()
		self._damaged = False

	def clear (self):
		self.select_this()
		self.plt.cla()
		self.last_style = None
		self.logx       = False
		self.logy       = False
		self.grid       = False

	def enable_grid (self, enable = True):
		self.select_this()
		self.plt.grid (enable)
		self.grid = True if enable else False

	def select_this (self):
		self.fig.add_subplot (1, 1, 1)

	def homeCB (self):
		self.plt.autoscale()
		self.redraw()

	def panCB (self):
		self.plt.autoscale (False)

	def zoomCB (self):
		self.plt.autoscale (False)

	def logx_cb (self):
		self.select_this()
		self.logx = not self.logx
		self.plt.set_xscale ('log' if self.logx else 'linear')
		self.redraw()

	def logy_cb (self):
		self.select_this()
		self.logy = not self.logy
		self.plt.set_yscale ('log' if self.logy else 'linear')
		self.redraw()

	def grid_cb (self):
		self.select_this()
		self.grid = not self.grid
		self.plt.grid (True if self.grid else False)
		self.redraw()

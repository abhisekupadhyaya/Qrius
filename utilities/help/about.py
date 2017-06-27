# About Qrius App.#

import os
from Tkinter import *
from PIL import Image
from PIL import ImageTk
import tkMessageBox

__version__ = '2.3.1'

iconpath = os.path.join('apps', 'icons')
qtlogo = os.path.join(iconpath, 'qtlogo.jpg')

ack = [ 'Qrius ' + __version__ + ' \nPrecision Quazar Tech Pvt. Ltd. \nwww.quazartech.com \nsupport@quazartech.com', \
	]

strCreditsQT = 'Joshua Mathew\nDr. Krishnendu Chatterjee'
strCreditOthers =  'Prof. Ashok K. Rastogi (JNU)\nProf. D. Sahdev (IITK)'

def about(master, oMenubar=None):
    oAbout = About(master, oMenubar)
    return

class About:
	def __init__(self, master, oMenuBar):
	    self.oMenuBar = oMenuBar
	    self.aGroup = master
	    self._createAwindow()
	    return

	def _createAwindow(self):
		self.__createImages()
		self._createAwidgets()
		return

	def __createImages(self):
		global qtlogoim
		qtlogoim = ImageTk.PhotoImage(file=qtlogo)
		return

	def _createAwidgets(self):
		"""
		Creates Canvas widgets for displaying scan images
		"""
		self.aGroup.title('About Qrius')
		self.LFDevProd = LabelFrame(self.aGroup, \
					text='Developed and Produced by', \
					)
		self.LFDevProd.grid(row=0, column=0, sticky=N+E+W+S)
		self.BtnAbout = Button(self.LFDevProd, \
					relief=FLAT, \
					compound=TOP, \
					text=ack[0], \
					fg = 'blue', \
					command=self.vCreditsQT, \
					justify=CENTER, \
					image = qtlogoim)
		self.BtnAbout.grid(row=0, column=0, sticky=N+E+W+S)
		self.LFContributors = LabelFrame(self.aGroup, \
					text='Contributors', \
					)
		self.LFContributors.grid(row=1, column=0, sticky=N+E+W+S)
		self.BtnContributors = Button(self.LFContributors, \
					#relief=FLAT, \
					compound=TOP, \
					text='Special thanks to...', \
					fg = 'blue', \
					command=self.vCreditOthers, \
					)
		self.BtnContributors.grid(row=0, column=0, sticky=N+E+W+S)

		'''
		self.BtnAboutIITK = Button(self.LFContributors, \
					relief=FLAT, \
					compound=TOP, \
					text=ack[2], \
					command=self.vCreditsIITK, \
					image = iitklogoim)
		self.BtnAboutIITK.grid(row=0, column=1, sticky=N+E+W+S)
		'''
		self.BtnClose = Button(self.aGroup, \
				command=self.vCloseAppAboutCB, \
				fg='red', \
				text='Close')
		self.BtnClose.grid(row=2, column=0, sticky=N+E+W+S)
		self.aGroup.protocol('WM_DELETE_WINDOW',self.vCloseAppAboutCB)

	def vCreditsQT(self):
		tkMessageBox.showinfo('Authors @ QT', \
				message=strCreditsQT, \
				parent = self.aGroup \
				)
		return

	def vCreditOthers(self):
		tkMessageBox.showinfo('Special thanks to', \
				message=strCreditOthers, \
				parent = self.aGroup \
				)
		return


	def vCloseAppAboutCB(self):
	    if self.oMenuBar:
		self.oMenuBar.About_Instance = 0
	    self.aGroup.destroy()


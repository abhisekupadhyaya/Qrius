from Tkinter import *
import app_kbsc
import os

kbscfile = os.path.join('docs', 'qrius_shortcuts.txt')

def kbsc(f=None, oMenubar=None):
	"""
	Creates KBSC Interface
	"""
	if not f :
		root = Tk()
		#f = Frame(root).grid()
		oAppKBSC = app_kbsc.app_kbsc()
		oAppKBSC.createKBSCwindow(root)
		oKBSC = KBSC(oAppKBSC, oMenubar)
		root.title(title)
		root.mainloop()
	else:
		oAppKBSC = app_kbsc.app_kbsc()
		oAppKBSC.createKBSCwindow(f)
		oKBSC = KBSC(oAppKBSC, oMenubar)
		return oKBSC

class KBSC:
    """
    def vParseFile(self):
	no_of_sections = self.strText.count('\r')
	self.anSecLoc = [0] * no_of_sections
	lines = self.strText
 	for i in range(no_sections):
	    self.anSecLoc[i] = lines.index('\r')
	    lines = lines[self.anSecLoc[i]+1:]
	return

    def vDisplayShortcuts(self):
	LFSection = []
	for count in range(len(self.anSecLoc)-1):
	    astrSectionText = self.strText[self.anSecLoc[count]: self.anSecLoc[count+1]]
	    LFSection.append(LabelFrame(self.oAppKBSC.kbscGroup, \
	    	text = self.astrSectionText
	return
    """

    def __init__(self, oAppKBSC, oMenubar):
	self.oAppKBSC = oAppKBSC
	self.oMenubar = oMenubar
	self._configureKBSCwindow()
	self.vDisplayShortcuts()
	return

    def _configureKBSCwindow(self):
	self.oAppKBSC.kbscGroup.title('Qrius Keyboard Shortcuts')
	self.oAppKBSC.kbscGroup.protocol('WM_DELETE_WINDOW',self.vCloseAppKBSCCB)
	return

    def vDisplayShortcuts(self):
	fd = open(kbscfile)
	if not fd:
	    print 'Cannot find KeyBoard Shortcuts file: ', kbsc
	    return
	strText = fd.read()
	fd.close()
	strKBSCText = strText.replace('\r', '')
	self.oAppKBSC.TBKeys.delete(1.0,END)
	self.oAppKBSC.TBFunctions.delete(1.0,END)
	for line in strKBSCText.split('\n'):
	    if line == '':
		func, key = '', ''
		#self.oAppKBSC.TBFunctions.tag_add('sec', END)
		#self.oAppKBSC.TBFunctions.tag_config('sec', foreground='black', justify=RIGHT)
	        #self.oAppKBSC.TBFunctions.insert(END,'\n')
	        #self.oAppKBSC.TBKeys.insert(END,'\n')
	    else:
	        try:
		    func, key = line.split('\t')
		    self.oAppKBSC.TBFunctions.tag_add('sec', END)
		    self.oAppKBSC.TBFunctions.tag_config('sec', foreground='black', justify=RIGHT)
	        except:
		    self.oAppKBSC.TBFunctions.tag_add('sec', END)
		    self.oAppKBSC.TBFunctions.tag_config('sec', foreground='red', justify=CENTER)
		    func = line
		    key = ''
	    self.oAppKBSC.TBFunctions.insert(END, func+'\n', 'sec')
	    self.oAppKBSC.TBKeys.insert(END, key+'\n')
	self.oAppKBSC.TBFunctions.config(state=DISABLED)
	self.oAppKBSC.TBKeys.config(state=DISABLED)
	return

    def vCloseAppKBSCCB(self):
	if not self.oMenubar:
	    self.oMenubar.KBSC_Instance = 0
	self.oAppKBSC.kbscGroup.destroy()


from Tkinter import *

class ValidatingEntry(Entry):
    # base class for validating entry widgets

    def __init__(self, master, value="", **kw):
        apply(Entry.__init__, (self, master), kw)
        self.__value = value
	self.__limits = None
        self.__variable = StringVar()
        self.__variable.set(value)
        self.__variable.trace("w", self.__callback)
        self.config(textvariable=self.__variable)
	self.nTrackVar = IntVar()	# Extra Tracker Variable that can be used outside
	self.nCount = 0

    def __callback(self, *dummy):
        value = self.__variable.get()
	if value == "":
	    return
        newvalue = self.validate(value)
        if newvalue is None:
            self.__variable.set(self.__value)
        elif newvalue != value:
            self.__value = newvalue
            self.__variable.set(self.newvalue)
        else:
            self.__value = value

    def validate(self, value):
        # override: return value, new value, or None if invalid
        return value

class IntegerEntry(ValidatingEntry):

    def validate(self, value=None):
	try:
	    limits = self.__limits
	except:
	    limits = None
        try:
            if value:
                v = int(value)
        except ValueError:
	    if value == '-':
		return value
	    else:
                return None
	if limits:
	    if v < limits[0]:
		return None
	    if v > limits[1]:
		return None
	self.nCount += 1
	self.nTrackVar.set(self.nCount)
        return value

    def limits(self, range_=None):
	self.__limits = range_
	return

class FloatEntry(ValidatingEntry):

    def validate(self, value):
	try:
	    limits = self.__limits
	except:
	    limits = None
        try:
            if value:
                v = float(value)
            return value
        except ValueError:
	    if value == '-':
		return value
	    else:
                return None
	if limits:
	    if v < limits[0]:
		return None
	    if v > limits[1]:
		return None
	self.nCount += 1
	self.nTrackVar.set(self.nCount)
        return value


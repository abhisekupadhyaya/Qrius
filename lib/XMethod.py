from cPickle import dump

class XMethodError (AttributeError) : pass

class _XMethod (dict):

	def __init__ (self):
		dict.__init__ (self)

	def save (self, fd):
		dump (self, fd)

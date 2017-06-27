from cPickle import load, dump, UnpicklingError

class XDictError (Exception) : pass

class _XDictBase:

	def __init__ (self, d = None):
		self._dict = d if (d != None) else {}

	def keys (self):
		return self._dict.keys()

	def set (self, key, val):
		self._dict[key] = val

	def get (self, key, default = None):
		return self._dict.get (key, default)

	def version (self):
		return self.get ('__version__', 0)

	def save (self, fd):
		dump (self._dict, fd)

class _XDict0 (_XDictBase):

	def __init__ (self, d = None):
		_XDictBase.__init__ (self, d)

	def sample (self, default = None):
		return self.get ('Sample', default)

	def set_sample (self, val):
		self.set ('Sample', val)

	def events (self, default = None):
		return self.get ('Events', default)

	def set_events (self, val):
		self.set ('Events', val)

	def data_keys (self, omit_zeros = True):

		keys = []
		for key in self.keys():

			if key == 'Sample':
				continue

			if key == 'Events':
				continue

			if 'Unit' in key:
				continue

			"""
			Do not consider a data if it is empty or all zero
			"""
			if omit_zeros and all (v == 0 for v in self.get (key)):
				continue

			keys.append (key)

		return sorted (keys)

	def set_data (self, key, data, unit):
		self.set (key, data)
		self.set (key + 'Unit', unit)

	def get_data (self, key):
		data = self.get (key)
		unit = self.get (key + 'Unit')
		return (data, unit)


class _XDict1 (_XDictBase):

	def __init__ (self, d = None):
		_XDictBase.__init__ (self, d)
		self.set ('__version__', 1)

	def sample (self, default = None):
		return self.get ('__sample__', default)

	def set_sample (self, val):
		self.set ('__sample__', val)

	def events (self, default = None):
		return self.get ('__events__', default)

	def set_events (self, val):
		self.set ('__events__', val)

	def data_keys (self, omit_zeros = True):

		keys = []
		for key in self.keys():

			"""
			All private keys have __ at their start and end. Omit them.
			"""
			if key[0:2] == '__' and key[-2:] == '__':
				continue

			data, unit = self.get (key)

			"""
			Do not consider a data if it is empty or all zero
			"""
			if omit_zeros and all (v == 0 for v in data):
				continue

			keys.append (key)

		return sorted (keys)

	def set_data (self, key, data, unit):
		self.set (key, (data, unit))

	def get_data (self, key):
		return self.get (key)

def XDict (fd = None):

	if fd == None:
		return _XDict1()

	else:
		try:
			dict = load (fd)
			ver = _XDictBase (dict).version()
			if   ver == 0 : return _XDict0 (dict)
			elif ver == 1 : return _XDict1 (dict)
			else: raise XDictError ('Unsupported XDict version ' + str (ver))

		except (UnpicklingError, AttributeError,
		  EOFError, ImportError, IndexError):
			raise XDictError ('Not a valid XDict')

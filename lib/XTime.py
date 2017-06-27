import time, copy

class XTime:

	def __init__ (self, t0 = None, t = None):
		self._t  = float (t  if t  is not None else time.time())
		self._t0 = float (t0 if t0 is not None else self._t)

	def t0 (self):
		return self._t0

	def t (self):
		return self._t

	def relative_time (self):
		return self.t() - self.t0()

	def __add__ (self, dt):
		o = copy.copy (self)
		o._t += dt
		return o

	def __sub__ (self, dt):
		o = copy.copy (self)
		o._t -= dt
		return o

	def __gt__ (self, t):
		return self.relative_time() > t.relative_time()

	def __ge__ (self, t):
		return self.relative_time() >= t.relative_time()

	def __lt__ (self, t):
		return self.relative_time() < t.relative_time()

	def __le__ (self, t):
		return self.relative_time() <= t.relative_time()

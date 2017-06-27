from collections import deque
from threading import RLock, Thread, current_thread, Event
from copy import copy
from time import time as systime, sleep

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class XEvent:

	def __init__ (self):
		self._value = None
		self._event = Event()

	def wait (self):
		self._event.wait()
		return self._value

	def set (self, value):
		self._value = value
		self._event.set()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class XTaskQueue:

	def __init__ (self):
		self._lock = RLock()
		self._taskq = deque()

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++

	def push (self, task, *args, **kwargs):
		try:
			self._lock.acquire()
			done_flag = XEvent()
			self._taskq.append ((task, args, kwargs, done_flag))

		finally:
			self._lock.release()

		return done_flag

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++

	def pop (self):

		try:
			self._lock.acquire()
			(task, args, kwargs, done_flag) = self._taskq.popleft()

		finally:
			self._lock.release()

		# Executes the task
		done_flag.set (task (*args, **kwargs))

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++

	def empty (self):
		try:
			self._lock.acquire()
			empty = (len (self._taskq) == 0)

		finally:
			self._lock.release()

		return empty

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++

	def process (self):
		try:
			self._lock.acquire()
			while not self.empty() : self.pop()

		finally:
			self._lock.release()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class XTerminate (Exception) : pass

class XThreadModule:

	def __init__ (self, master):
		self.master = master
		self._taskq = XTaskQueue()

	# ++++ Task queue functions ++++

	def schedule_task (self, task, *args, **kwargs):
		self._taskq.push (task, *args, **kwargs)

	def schedule_task_n_wait (self, task, *args, **kwargs):
		return self._taskq.push (task, *args, **kwargs).wait()

	def do_tasks (self, bg_task = None, *bg_tasks):
		self._taskq.process()
		if bg_task: bg_task()
		for task in bg_tasks:
			if task: task()

	def schedule_termination (self):
		self.schedule_task (self.terminate)

	def terminate (self):
		raise XTerminate

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class XThread:

	def __init__ (self, daemon = False):
		self._taskq = XTaskQueue()
		self._oThread = Thread (target = self._thread)
		self._oThread.daemon = daemon
		self._atexit = None

	def atexit (self, cb):
		self._atexit = cb

	def _thread (self):
		self.thread()
		if self._atexit : self._atexit ()

	def thread (self) : pass

	# ++++ Thread control functions ++++

	def start (self):
		self._oThread.start()

	def schedule_termination (self):
		self.schedule_task (self.terminate)

	def terminate (self):
		raise XTerminate

	def join (self, timeout = None):
		self._oThread.join (timeout)

	def has_started (self):
		return self._oThread.ident != None

	def is_alive (self):
		return self._oThread.is_alive()

	def is_dead (self):
		return self.has_started() and not self.is_alive()

	# ++++ Task queue functions ++++

	def schedule_task (self, task, *args, **kwargs):
		self._taskq.push (task, *args, **kwargs)

	def schedule_task_n_wait (self, task, *args, **kwargs):
		return self._taskq.push (task, *args, **kwargs).wait()

	def do_tasks (self, bg_task = None, *bg_tasks):
		self._taskq.process()
		if bg_task: bg_task()
		for task in bg_tasks:
			if task: task()

import Queue
import threading
import FuncThread as FT
import time
from threading import Lock

class ThreadHandler():
	def __init__(self, *args, **kwargs):
		self.queue = Queue.Queue()
		self._run = True
		self.lock = Lock()

	def startNext(self):
		func = self.queue.get()
		try:
			func()
		except:
			pass
		self.queue.task_done()

	def start(self):
		while self._run:
			if not self.queue.empty():
				self.startNext()

	def stop(self):
		self.queue.join()
		self._run = False

	def put(self, func):
		self.lock.acquire()
		self.queue.put(func)
		self.lock.release()

if __name__ == "__main__":
	TH = ThreadHandler()
	print TH




 

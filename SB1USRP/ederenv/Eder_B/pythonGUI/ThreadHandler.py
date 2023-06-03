import Queue
import threading
import FuncThread as FT
import time

class ThreadHandler():
	def __init__(self, *args, **kwargs):
		self.queue = Queue.Queue()
		self._run = True

	def startNext(self):
		func = self.queue.get()
		func()

	def start(self):
		while self._run:
			if not self.queue.empty():
				self.startNext()


	def stop(self):
		self._run = False

	def put(self, func):
		self.queue.put(func)

if __name__ == "__main__":
	TH = ThreadHandler()
	print TH




 

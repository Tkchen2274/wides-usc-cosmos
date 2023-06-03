import threading
 
class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        self._is_running = True
        threading.Thread.__init__(self)
 
    def run(self):
        self._target(*self._args)

    def stop(self):
    	self._is_running = False

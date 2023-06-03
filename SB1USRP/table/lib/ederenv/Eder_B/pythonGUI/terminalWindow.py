import Tkinter as Tk
import sys
import threading
import Queue



class Std_redirector(object):
    def __init__(self,widget, TH):
        self.widget = widget
        self.TH = TH
        self.q = Queue.Queue()

    def write(self,string):
        try:
            self.q.put(lambda:self.widget.insert(Tk.END,string))
            self.q.put(lambda:self.widget.see(Tk.END))
        except:
            pass

    def clear(self):
        try:
            self.q.put(lambda:self.widget.delete('1.0', Tk.END))
        except:
            pass

    def log_info(self, string, indentation=0):
        try:
            self.q.put(lambda:self.widget.insert(Tk.END,' '*indentation + string + '\n'))
            self.q.put(lambda:self.widget.see(Tk.END))
        except:
            pass

    def update(self):
        while not self.q.empty():
            func = self.q.get()
            func()
            self.q.task_done()
#

import Tkinter as Tk
import sys
import threading



class Std_redirector(object):
    def __init__(self,widget):
        self.widget = widget

    def write(self,string):
       # if not exit_thread:
        self.widget.insert(Tk.END,string)
        self.widget.see(Tk.END)

    def clear(self):
        self.widget.delete('1.0', Tk.END)
   

    def log_info(self, string, indentation=0):
        self.widget.insert(Tk.END,' '*indentation + string + '\n')
        self.widget.see(Tk.END)
#

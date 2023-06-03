'''
A GUI for controlling registers
'''
__author__= "Pontus Brink"
__version__ = 1.4

import sys
import os
sys.path.append('.')
import Tkinter as tk
import tkFont as tkfont
import tkFileDialog
import ttk
#s = ttk.Style()
from shutil import copyfile
import os
from Chip import Chip
from threading import Thread
import controller
import terminalWindow
import FuncThread as FT
import graphplot
import ThreadHandler as TH
#currentChip = 'currentChip.txt'
currentRxChip = 'RxChip.txt'
currentTxChip =  'TxChip.txt'
import time
import Variables as var
import RxTxView as rt
import Page as p


serial_number = ''
board_type = ''


# This class controls the entire program.
class MainView(tk.Frame):
	def __init__(self, root,RxChip, TxChip, *args, **kwargs):
		tk.Frame.__init__(self,*args,**kwargs)

		self.rxController = controller.Controller(RxChip, TxChip, self, board_type, serial_number, eder_gen, "RX")
		#self.txController = controller.Controller(TxChip, self, board_type, serial_number, "TX")
		self.chipsConnected = self.rxController.eder.check() #and self.txController.eder.check()
		self.root = root
                if serial_number != None:
		    self.root.title("TRX-BF01 EVK    " + serial_number)
                else:
                    self.root.title("TRX-BF01 EVK    ")
		self.root.protocol('WM_DELETE_WINDOW', self.close)
		self.TH = TH.ThreadHandler()
		self.queueThread = FT.FuncThread(lambda:self.TH.start()) # DOESNT STOP???
		self.queueThread.start()
		# print(chip).
		self.quit = False

		# Add menubar, this is the controls of the top that are general for every chip. Controls which chip to use and so on.
		self.menubar = tk.Menu(root)
		menu = tk.Menu(self.menubar, tearoff=0)
		self.menubar.add_cascade(label="Help", menu=menu)
		switcherRx = lambda: PictureShower(newWindow(self,"Block Diagram"),var._RXBLOCKDIAGRAM, background="orange")
		switcherTx = lambda: PictureShower(newWindow(self,"Block Diagram"),var._TXBLOCKDIAGRAM, background="orange")
		menu.add_command(label="Show Rx Block Diagram", command=switcherRx)
		menu.add_command(label="Show Tx Block Diagram", command=switcherTx)
		self.master.config(menu=self.menubar)


		
		# Tx Rx notebook
		self.nb = ttk.Notebook(root)
		RxPage = p.Page(self.nb)
		self.RxView = rt.RxTxView(RxPage, self.rxController, self.TH, "RX")
		self.nb.add(RxPage, text="RX")
		TxPage = p.Page(self.nb)
		#self.TxView = rt.RxTxView(TxPage, self.txController, self.TH, "TX")
                self.TxView = rt.RxTxView(TxPage, self.rxController, self.TH, "TX")
		self.nb.add(TxPage, text="TX")

		self.TxView.setMainView(self)
		self.RxView.setMainView(self)


		# Siversima logo
		self.logoPage = p.Page(root, background=var._BACKGROUND)
		verLabel = tk.Label(self.logoPage, text="v" + str(__version__), background=var._BACKGROUND)
		verLabel.pack(side="top", anchor="ne")
		logo = PictureShower(self.logoPage,"SiversPic.GIF")
		
		# Graph plotter.
		#self.grapher = graphplot.PlotFrame(root, self.rxController, self.txController)
                self.grapher = graphplot.PlotFrame(root, self.rxController, self.rxController)
	
		# Pack it up.
		self.logoPage.pack(side="top", fill="x", anchor="n")
		self.grapher.pack(side="bottom", fill="x")			
		self.nb.pack(side="top",fill="both", expand=True)
		
		
		# start readers
		#self.graphThread = FT.FuncThread(self.grapher.startPlotThread).start()
		self.grapher.startPlotThread()

		self.TxView.poll(root)
		self.RxView.poll(root)
			
		

	def close(self):
		##print "BYEBYE"
		##print "Thread joined!!!", self.TH
		##self.grapher.ani.event_source.stop()
		#self.quit = True
		self.grapher.close()
		self.nb.destroy()
		self.TH.stop()
		self.queueThread.join()
		##print "All things stopped", self.queueThread
		##time.sleep(1000)
		#
		## Destroy each nb in the notebook.
		
		#
		self.menubar.destroy()
		self.root.quit()
		self.master.destroy()

        def setMainViewTitle(self, titleAddition=None):
            if serial_number != None:
                if titleAddition == None:
                    self.root.title("TRX-BF01 EVK    " + serial_number)
                else:
                    self.root.title("TRX-BF01 EVK    " + serial_number + titleAddition)
            else:
                if titleAddition == None:
                    self.root.title("TRX-BF01 EVK    ")
                else:
                    self.root.title("TRX-BF01 EVK    " + titleAddition)

def newWindow(parent, title):
	newWindow = tk.Toplevel(parent)
	newWindow.wm_title(title)
	return newWindow

class PictureShower(p.Page):
	def __init__(self, parent, photoLocation, *args, **kwargs):
		p.Page.__init__(self,parent,*args,**kwargs)
		# Picture
		photo = tk.PhotoImage(file=photoLocation)
		self.label = tk.Label(parent, image=photo, *args, **kwargs)
		self.label.photo=photo
		self.label.pack()


def getPrevChip():
	if os.path.isfile(currentRxChip):
		RxChip =  Chip(currentRxChip)
		if os.path.isfile(currentTxChip):
			TxChip = Chip(currentTxChip)
		else:
			raise Exception('Missing file TxChip.txt')
	else:
		raise Exception('Missing file RxChip.txt')
	return RxChip, TxChip




def startApp(root, RxChip, TxChip):
	app=MainView(root, RxChip, TxChip)
	app.pack(side="top", fill="both", expand=True)
	app.mainloop()

def get_args():
    import argparse
    parser = argparse.ArgumentParser(description='Command line options.')
    parser.add_argument('--board', '-b', dest='board_type', choices=['MB0', 'MB1'], default='MB0',
                         help='Specify type of motherboard')
    parser.add_argument('--unit', '-u', dest='unit_name', metavar='UNIT', default=None,
                         help='Specify unit name')
    parser.add_argument('--ederver', '-v', dest='eder_ver', metavar='EDERVER', default='2',
                         help='Specify Eder generation')
    return parser.parse_args()


if __name__ == "__main__":
        args = get_args()
        board_type = args.board_type
        serial_number = args.unit_name
        eder_gen = args.eder_ver
        print '  Using settings for Eder Gen {0}'.format(args.eder_ver)
	RxChip, TxChip = getPrevChip()
	root = tk.Tk()
	w = 1150 # width for the Tk root
	h = 900 # height for the Tk root

	# get screen width and height
	ws = root.winfo_screenwidth() # width of the screen
	hs = root.winfo_screenheight() # height of the screen

	# calculate x and y coordinates for the Tk root window
	x = (ws/2) - (w/2)
	y = (hs/2) - (h/2)

	# set the dimensions of the screen 
	# and where it is placed
	#root.geometry('%dx%d+%d+%d' % (w, h, x, y))
	root.geometry('%dx%d+%d+%d' % (w, hs*0.9, 0, 0))
	startApp(root,RxChip, TxChip)



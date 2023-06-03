'''
A GUI for controlling registers
'''
import sys
sys.path.insert(0, '../')
import version
__author__= "Pontus Brink"
__version__ = version.version_num

import sys
import os
sys.path.append('.')

import Tkinter as tk
import tkFont as tkfont
import tkFileDialog
import ttk
from shutil import copyfile
import os
from Chip import Chip
from threading import Thread
import controller
import terminalWindow
import FuncThread as FT
import graphplot
import ThreadHandler as TH
currentRxChip = 'RxChip.txt'
currentTxChip =  'TxChip.txt'
import time
import Variables as var
import RxTxView as rt
import Page as p
import GuiCmdHist
import RegisterWindow


serial_number = ''
board_type = ''
rfm_type = ''

# This class controls the entire program.
class MainView(tk.Frame):
	def __init__(self, root,RxChip, TxChip, *args, **kwargs):
		tk.Frame.__init__(self,*args,**kwargs)

		self.root = root
		self.root.protocol('WM_DELETE_WINDOW', self.close)
		self.TH = TH.ThreadHandler()
		self.queueThread = FT.FuncThread(lambda:self.TH.start())
		self.queueThread.start()
		self.quit = False

		# Add menubar, this is the controls of the top that are general for every chip. Controls which chip to use and so on.
		self.menubar = tk.Menu(root)

		config_menu = tk.Menu(self.menubar, tearoff=0)
		self.menubar.add_cascade(label="File", menu=config_menu)
		LoadFile = lambda: self.loadGainSettings()
		SaveFile = lambda: self.saveRegisterSettings()
		config_menu.add_command(label="Load TX and RX gain setting", command=LoadFile)
		config_menu.add_command(label="Save register setting", command=SaveFile)

		menu = tk.Menu(self.menubar, tearoff=0)
		self.menubar.add_cascade(label="Help", menu=menu)
		switcherRx = lambda: PictureShower(newWindow(self,"Block Diagram"),var._RXBLOCKDIAGRAM, background="orange")
		switcherTx = lambda: PictureShower(newWindow(self,"Block Diagram"),var._TXBLOCKDIAGRAM, background="orange")
		menu.add_command(label="Show Rx Block Diagram", command=switcherRx)
		menu.add_command(label="Show Tx Block Diagram", command=switcherTx)

		self.master.config(menu=self.menubar)

		self.root.title("TRX-BF01 EVK    ")

		global serial_number
		if serial_number == None:
			try:
				import mb1
				devlist = mb1.listdevs()
			except:
				devlist = None
			
			rfm_type_list = ['rfm_3.0', 'rfm_2.5']
			d = ConnectDialog(root, devlist, rfm_type_list)
			root.wait_window(d.top)
			if (serial_number == None) or (serial_number == ''):
				self.close()

		if serial_number != None:
			self.root.title("TRX-BF01 EVK    " + serial_number)
		else:
			self.root.title("TRX-BF01 EVK    ")

		self.rxController = controller.Controller(RxChip, TxChip, self, board_type, serial_number, "RX", rfm_type)
		self.chipsConnected = self.rxController.eder.check()

		# Tx Rx notebook
		self.nb = ttk.Notebook(root)
		RxPage = p.Page(self.nb)
		self.RxView = rt.RxTxView(RxPage, self.rxController, self.TH, "RX")

		self.nb.add(RxPage, text="RX")
		TxPage = p.Page(self.nb)
		self.TxView = rt.RxTxView(TxPage, self.rxController, self.TH, "TX")
		self.nb.add(TxPage, text="TX")

		self.TxView.setMainView(self)
		self.RxView.setMainView(self)

		self.cmdhist = GuiCmdHist.GuiCmdHist()
		#TerminalWindow
		terminalPage = p.Page(root)
		text = tk.Text(terminalPage)
		text.configure(height=50)
		self.terminal = terminalWindow.Std_redirector(text, self.TH)

		# Terminal input.
		self.ederInput = tk.StringVar()
		inputFrame = tk.Frame(terminalPage)
		self.CommandCombobox = ttk.Combobox(inputFrame, textvariable=self.ederInput)
		self.ederInput.set("eder.")
		self.CommandCombobox.configure(values=self.cmdhist.load_cmd_history())
		self.CommandCombobox.bind('<Return>', self.enterKeyPressed)
		self.CommandCombobox.bind('<Up>', self.upKeyPressed)

		regwinFrame = tk.Frame(terminalPage)
		self.regwin = RegisterWindow.RegisterWindow(regwinFrame, self.rxController.eder)

		sendCommandButton = tk.Button(inputFrame, text="Run", width=10, command=lambda :self.TH.put(lambda:self.runEder()))
		clearButton = tk.Button(inputFrame, text="Clear", width=10, command=lambda :self.TH.put(lambda:self.clearWindow()))

		self.CommandCombobox.pack(side="left", fill="both", expand="true")
		clearButton.pack(side="right")
		sendCommandButton.pack(side="right")
		inputFrame.pack(side="bottom", fill="x")
		regwinFrame.pack(side="right", fill="y")
		text.pack(side="bottom", fill="both", expand="true")

		self.rxController.eder.logger.log_info = lambda string, indent=0: self.terminal.log_info(string, indent)

		sys.stderr = self.terminal
		sys.stdout = self.terminal

		# Siversima logo
		self.logoPage = p.Page(root, background=var._BACKGROUND)
		verLabel = tk.Label(self.logoPage, text="v" + str(__version__), background=var._BACKGROUND)
		verLabel.pack(side="top", anchor="ne")
		logo = PictureShower(self.logoPage,"SiversPic.GIF")
		
		# Graph plotter.
		self.grapher = graphplot.PlotFrame(root, self.rxController, self.rxController, self.TH)
	
		# Pack it up.
		self.logoPage.pack(side="top", fill="x", anchor="n")
		self.grapher.pack(side="bottom", fill="both", expand=True)
		self.nb.pack(side="top",fill="both", expand=True)

		terminalPage.pack(side="top", fill="both", expand="true")

		self.grapher.startPlotThread()
		root.after(1000, self.PollStarter)
		root.after(1000, self.guiUpdateTrigger)
		root.after(1000, self.termUpdateTrigger)

	def guiUpdateTrigger(self):
		self.RxView.buttonBar.UpdateGuiTxRx()
		self.TxView.buttonBar.UpdateGuiTxRx()
		root.after(1000, self.guiUpdateTrigger)

	def termUpdateTrigger(self):
		self.terminal.update()
		root.after(500, self.termUpdateTrigger)

	def poll(self):
		if self.group == 'RX':
			if self.RxView.configPage.pollVar.get():
				self.RxView.controller.getRegisterValues(self.RxView)
		elif self.group == 'TX':
			if self.TxView.configPage.pollVar.get():
				self.TxView.controller.getRegisterValues(self.TxView)
		else:
			print '!!'
			print group

		self.regwin.poll()

	def viewUpdater(self):
		try:
			group = self.nb.tab(self.nb.select(), "text")
		except:
			root.after(4000, self.PollStarter)
			return
		if group == 'RX':
			if self.RxView.configPage.pollVar.get():
				self.RxView.controller.updateRegisters(self.RxView)
		elif group == 'TX':
			if self.TxView.configPage.pollVar.get():
				self.TxView.controller.updateRegisters(self.TxView)

		self.regwin.updateView()

	def PollStarter(self):
		try:
			self.group = self.nb.tab(self.nb.select(), "text")
		except:
			print '*****!!!!!*****'
			root.after(4000, self.PollStarter)
			return
		if self.group == 'RX':
			if self.RxView.configPage.pollVar.get():
				self.RxView.controller.updateRegisters(self.RxView)
		elif self.group == 'TX':
			if self.TxView.configPage.pollVar.get():
				self.TxView.controller.updateRegisters(self.TxView)

		self.regwin.updateView()

		self.TH.put(lambda:self.poll())
		root.after(4000, self.PollStarter)

	def enterKeyPressed(self, event):
		self.TH.put(lambda:self.runEder())

	def upKeyPressed(self, event):
		try:
			self.CommandCombobox.current(self.CommandCombobox.current() + 1)
		except:
			pass

	def loadGainSettings(self):
		filename = tkFileDialog.askopenfilename(initialdir = "../config",title = "Select file",filetypes = (("json files","*.json"),("all files","*.*")))
		if filename != '':
			self.rxController.eder.loadGainSettings(filename)

	def saveRegisterSettings(self):
		filename = tkFileDialog.asksaveasfilename(initialdir = "../config",title = "Select file",defaultextension=".json",filetypes = (("json files","*.json"),("all files","*.*")))
		if filename != '':
			self.rxController.eder.saveRegisterSettings(filename)
			
	def runEder(self):
		code = self.ederInput.get()
		sys.stdout = self.terminal
		#sys.stderr = self.terminal
		self.CommandCombobox.configure(values=self.cmdhist.add_to_cmd_history(code))
		self.rxController.runPythonCode(code)
		self.CommandCombobox.current(0)

	def clearWindow(self):
		self.terminal.clear()

	def close(self):
		try:
			self.cmdhist.save_cmd_history()
		except:
			pass

		try:
			self.grapher.close()
		except:
			pass
		try:
			self.nb.destroy()
		except:
			pass
		self.TH.stop()
		self.queueThread.join()
		#
		self.menubar.destroy()
		self.root.quit()
		self.master.destroy()
		exit(0)

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

class ConnectDialog:
	def __init__(self, parent, dev_list, rfm_type_list):
		self.ser_num = tk.StringVar()
		self.rfm_type = tk.StringVar()
		self.top = tk.Toplevel(parent)
		self.top.transient(parent)
		self.top.grab_set()
		self.top.title('EVK Selector')
		self.top.geometry('+%d+%d' % (440, 300))
		tk.Label(self.top, text='Device').pack()
		self.top.bind("<Return>", self.connect)

		self.SerNumCombobox = ttk.Combobox(self.top)
		self.SerNumCombobox.configure(values=dev_list)
		self.SerNumCombobox.configure(textvariable=self.ser_num)
		self.SerNumCombobox.configure(takefocus="")
		if dev_list != None:
			if len(dev_list) > 0:
				self.SerNumCombobox.current(0)
		self.SerNumCombobox.pack(padx=15)

		self.RfmTypeCombobox = ttk.Combobox(self.top)
		self.RfmTypeCombobox.configure(values=rfm_type_list)
		self.RfmTypeCombobox.configure(textvariable=self.rfm_type)
		self.RfmTypeCombobox.configure(takefocus="")
		if rfm_type_list != None:
			if len(rfm_type_list) > 0:
				self.RfmTypeCombobox.current(0)
		self.RfmTypeCombobox.pack(padx=15)

		b = tk.Button(self.top, text="Connect", command=self.connect)
		b.pack(pady=5)
 
	def connect(self, event=None):
		global serial_number
		serial_number = self.ser_num.get()
		global rfm_type
		rfm_type = self.rfm_type.get()
		self.top.destroy()

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
    parser.add_argument('--board', '-b', dest='board_type', choices=['MB0', 'MB1'], default='MB1',
                         help='Specify type of motherboard')
    parser.add_argument('--unit', '-u', dest='unit_name', metavar='UNIT', default=None,
                         help='Specify unit name')
    parser.add_argument('-r', '--rfm', dest='rfm_type', choices=['rfm_2.5','rfm_3.0'], default='rfm_3.0',
                         help='Specify type of RFM')

    return parser.parse_args()

def connect_button_pressed():
	print('evk_selector_support.connect_button_pressed')
	sys.stdout.flush()

if __name__ == "__main__":
	args = get_args()
	board_type = args.board_type
	serial_number = args.unit_name
	rfm_type = args.rfm_type
	RxChip, TxChip = getPrevChip()
	root = tk.Tk()

	#w = 1300 # width for the Tk root
	w = 1050
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
	root.geometry('%dx%d+%d+%d' % (w, hs*0.8, 0, 0))

	# Make the main window non-resizable
	#root.resizable(0,0)

	# Set main window minimum size
	root.update()
	root.minsize(root.winfo_width(), root.winfo_height())

	startApp(root,RxChip, TxChip)



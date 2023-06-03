import Page as p
import Tkinter as tk
import ttk
import Variables as var
import terminalWindow
import sys
import time
sys.path.insert(0, '..')
sys.path.insert(0,'../')

MAINVIEW = 0
BUSY = False

def _postPoll(func):
	def postPollWrapper(*args, **kwargs):
		func(*args, **kwargs)
		MAINVIEW.poll()
		MAINVIEW.viewUpdater()
	return postPollWrapper

class RxTxView(p.Page):
	def __init__(self, parent, controller, TH, mode, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)
		self.parent = parent
		self.mode = mode
		self.lastPressed = None
		self.TH = TH
		self.controller = controller
		upper = p.Page(parent)
		regpage = p.Page(upper)
		#self.nb = ttk.Notebook(regpage, width=295)
		self.nb = ttk.Notebook(regpage, width=410)
		
		# Navbar.
		# self.navFrame = NavFrame(self, self.groups, background='green').
		# self.navFrame.pack(in_=root,side="top", fill="both", expand=False).
		# Add frames for each page in the notebook.
		# Contains each frame in the notebook with the key as the groups name.
		self.pages = {} 				
		# Contains each frame in the notebook that the controls are to be packed into.
		self.controlsFrame= {}			
		# Contains each frame that the buttons are placed. Dict of dicts, a button is found with [groupName][buttonName].
		self.pageButtons = {}			
		# Contains each frame that a page in the notebook uses to hide the controls. packed into the pages frame. Found with [groupName].
		self.hidePages = {}
		# Contains each control for each register
		self.regControlFrames = {}
		#Add registers to notebook
		self.createRegisters(self.nb)



		# Config box
		self.configPage = ConfigPage(regpage, bd=2, relief=tk.GROOVE)

		# Add buttonbar to the left of everything
		self.buttonBar = ModePage(upper, self.controller, self.TH, self.mode, self.configPage, bd=2, relief='groove')


		# Pack it up!
		
		self.buttonBar.pack(side="left", fill="x")
		self.configPage.pack(side="top", anchor="e")
		self.nb.pack(side="right",fill="y")

		regpage.pack(side="top", fill="x")
		upper.pack(side="top", fill="x")

		self.controller.updateRegisters(self)


	def setMainView(self, mainview):
		global MAINVIEW
		MAINVIEW = mainview

	def createRegisters(self, nb):
		for groupName in self.controller.getGroups(self.mode):
			page = p.Page(nb)
			self.pages[groupName] = page
			self.pageButtons[groupName] = {}
			self.controlsFrame[groupName] = {}
			self.regControlFrames[groupName] = {}
			nb.add(page, text=groupName)
			i = 0
			# Add registers to each page.
			for registerName in self.controller.getRegisters(self.mode, groupName):
				self.regControlFrames[groupName][registerName] = {}
				# Create a registerFrame, places it in the pages, adds the frame to pageButtons.
				registerFrame = RegFrame(self.mode, groupName, registerName,self.pages[groupName], lambda groupName=groupName, regName=registerName: self.showFrame(groupName, regName), self.controller, self.TH)
				self.pageButtons[groupName][registerName] = registerFrame
				# packs the frame to the left side decreasing order.
				registerFrame.grid(row=i, column=0, sticky="nsew")
				# Add a frame for each registers control.
				controlPage = p.Page(self.pages[groupName])
				controlPage.grid(row=i, column=2, sticky="nsew", rowspan=len(self.controller.getRegisters(self.mode, groupName)))
				self.controlsFrame[groupName][registerName] = controlPage
				# Add a space between the regButtons and the controls.
				space = ValueShower(self.pages[groupName])
				space.grid(row=i, column=1, sticky="nsew")
				self.pages[groupName].grid_columnconfigure(1, weight=1)
				i = i+1
				# Add Control Buttons to each page.
				for controlName in self.controller.getControls(self.mode, groupName, registerName):
					regControlFrame = RegControlFrame(self.mode, groupName, registerName, controlName,self.controlsFrame[groupName][registerName], self.pageButtons[groupName][registerName], self.controller)
					regControlFrame.pack(side="top", anchor="nw")
					self.regControlFrames[groupName][registerName][controlName] = regControlFrame
			# Create a empty page for each page.
			emptyReg = p.Page(self.pages[groupName])
			emptyReg.grid(row=0, column=2, sticky="nsew", rowspan=len(self.controller.getRegisters(self.mode, groupName)))
			self.hidePages[groupName]=emptyReg


	def updateRegisters(self):
		if self.configPage.pollVar.get():
			self.controller.updateRegisters(self)

	def hideFrame(self, groupName):
		self.lastPressed.config(relief="flat")
		self.lastPressed = None
		# print("showing empty page").
		self.hidePages[groupName].show()

	def showFrame(self, groupName, registerName):
		#print registerName
		controlName = self.controller.getControls(self.mode, groupName, registerName)
		self.regControlFrames[groupName][registerName][controlName[0]].hexUpdate(self.controller)
		buttonFrame = self.pageButtons[groupName][registerName]
		button = buttonFrame.getButton()
		if (self.lastPressed is not None) and (self.lastPressed != button) :
			self.lastPressed.config(relief="flat")
                        self.hideFrame(groupName)
                        controlName = self.controller.getControls(self.lastMode, self.lastGroupName, self.lastRegisterName)
                        self.regControlFrames[self.lastGroupName][self.lastRegisterName][controlName[0]].hexUpdate(self.controller)
		if self.lastPressed == button:
			self.hideFrame(groupName)
			return
		button.config(relief="groove")
		#print(self.controlsFrame[groupName][registerName], ' was raised')
		self.controlsFrame[groupName][registerName].show()
		self.lastPressed = button
		self.lastGroupName = groupName
		self.lastRegisterName = registerName
		self.lastMode = self.mode

class ConfigPage(p.Page):
	def __init__(self, parent, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)
		self.pollVar = tk.BooleanVar()
		self.checkButton = tk.Checkbutton(self, text="Auto update", variable=self.pollVar, onvalue=True, offvalue=False)
		self.checkButton.pack()
		self.pollVar.set(True)

		
class ModePage(p.Page):

	def __init__(self, parent, controller, TH, RXTXMODE, configPage, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)
		# Frequency input.
		self.TH = TH
		self.controller = controller
		self.mode = RXTXMODE
		self.configPage = configPage
		FreqModePage = p.Page(self, borderwidth=10)
		TopPage = p.Page(FreqModePage)
		self.TopPage = TopPage
		self.guiState = None

		self.alcEnabled = False

		self.state_str = tk.StringVar()
		self.state_str.set("State: IDLE")
		self.state_lable = tk.Label(TopPage)
		self.state_lable.configure(textvariable=self.state_str)
		self.state_lable.configure(relief=tk.RAISED)
		self.state_lable.configure(font="-weight bold")
		
		self.freq = tk.StringVar()
		self.freqLabel = tk.Label(TopPage,text="WiGig Channel:")
		if controller.eder.regs.device_info.get_attrib('rfm_type') == 'rfm_3.0':
			self.frequencies = [
				"1: 58.32 GHz",
				"2: 60.48 GHz",
				"3: 62.64 GHz",
				"4: 64.80 GHz",
				"5: 66.96 GHz",
				"6: 69.12 GHz"

			]
			self.dict = {
				self.frequencies[0] : 58.32e9,
				self.frequencies[1] : 60.48e9,
				self.frequencies[2] : 62.64e9,
				self.frequencies[3] : 64.80e9,
				self.frequencies[4] : 66.96e9,
				self.frequencies[5] : 69.12e9
			}
		else:
			self.frequencies = [
				"1: 58.32 GHz",
				"2: 60.48 GHz",
				"3: 62.64 GHz",
				"4: 64.80 GHz"
			]
			self.dict = {
				self.frequencies[0] : 58.32e9,
				self.frequencies[1] : 60.48e9,
				self.frequencies[2] : 62.64e9,
				self.frequencies[3] : 64.80e9
			}
		self.state_lable.pack(side="top")
		self.freqLabel.pack(side="left")
		#for text, mode in frequencies:
		#	bpage = p.Page(TopPage)
		#	btext = tk.Label(bpage,text = text)
		#	b = tk.Radiobutton(bpage, variable=self.freq, value=mode)
		#	b.pack(side="bottom")
		#	btext.pack(side="top")
		#	bpage.pack(side="left", fill="both", expand=True)
		self.freqDropDown = tk.OptionMenu(TopPage, self.freq, *self.frequencies)
		self.freqDropDown.pack(side="left", fill="x",expand=True)
		self.freq.set(self.frequencies[1])
		
		TopPage.pack(side="top",  fill="both", expand=True)
		FreqModePage.pack(side="right", anchor="w", fill="both")

		# Buttons
		Buttonpage = p.Page(self, pady=5)
		if RXTXMODE == "RX":
			self.Button = tk.Button(Buttonpage, text="Enable RX", command= lambda: self.rxSetup())
			self.CalButton = tk.Button(Buttonpage, text="RX DCO Calib.", command = lambda : self.rxBbDcCal())
		else:
			self.Button = tk.Button(Buttonpage, text="Enable TX", command= lambda : self.txSetup())
			self.CalButton = tk.Button(Buttonpage, text="TX DCO Calib.", command = lambda : self.txLoLeakCal())
		self.resetButton = tk.Button(Buttonpage, text="Reset", command= lambda : self.ederReset())
		self.regDumpButton = tk.Button(Buttonpage, text="List registers", command= lambda : self.regDump())


		self.resetButton.pack(side="left", anchor="n", fill = "x", expand=True)
		self.regDumpButton.pack(side="left", anchor="n", fill = "x", expand=True)
		self.Button.pack(side="left", anchor="n", fill = "x", expand=True)
		self.CalButton.pack(side="left", anchor="n", fill = "x", expand=True)
		Buttonpage.pack(side="top", fill="x")
               
		# Infomation page
		# Temporarily disabled
		#if RXTXMODE == "TX":
		#	infopage = p.Page(self, borderwidth=2, relief=tk.GROOVE)
		#	self.updatePowerButton = tk.Button(infopage, text="Measure TX power", command= lambda: TH.put(lambda : self.txPowerMeasurement()))
		#	self.updatePowerButton.pack(side="left", anchor="n", fill = tk.NONE, expand=False)
		#	self.powerLabel = tk.Label(infopage, text="Total TX Power _ dBm", justify=tk.RIGHT)
		#	self.powerLabel.pack(side="left", fill="both", anchor="n", padx=20)
		#	infopage.pack(side="top", fill="both", anchor="n")
		
		# Beambook stearing with slider
		beambookPage = p.Page(self)
		self.stearingVal = tk.DoubleVar()

		BfSwLabelframe = tk.LabelFrame(beambookPage)
		BfSwLabelframe.place(relx=0.1, rely=0.133, relheight=0.4, relwidth=0.4)
		BfSwLabelframe.configure(relief='groove')
		BfSwLabelframe.configure(foreground="black")
		BfSwLabelframe.configure(text='''SW BF''')
		BfSwLabelframe.configure(width=260)


		titleLabel = tk.Label(BfSwLabelframe, text="Beam angle Control (degrees)")
		self.scale = tk.Scale(BfSwLabelframe, orient="horizontal", from_=-45, to = 45, tickinterval=15, variable = self.stearingVal, resolution=var._BEAMBOOKSLIDERRESOLUTION, digits=var._BEAMBOOKSLIDERPRECISION)
		self.beamStearingButton = tk.Button(BfSwLabelframe, text="Set beam angle", command=lambda : self.setBeambook())
		self.beamResetButton = tk.Button(BfSwLabelframe, text="Reset beam angle", command=lambda : self.resetBeam())



		titleLabel.pack(side="top", fill="both", anchor="n")
		self.scale.pack(side="top", fill="both", padx=5, anchor="n")
		self.beamStearingButton.pack(side="left", fill="both", pady=10, padx=5, anchor="n")
		self.beamResetButton.pack(side="right", fill="both", pady=10, padx=5, anchor="n")
		BfSwLabelframe.pack(side="top", fill="both", anchor="n")
		beambookPage.pack(side="top", fill="both", anchor="n")

		# HW Beamforming controls
		gpioBeambookPage = p.Page(self)

		BfGpioLabelframe = tk.LabelFrame(gpioBeambookPage)
		BfGpioLabelframe.place(relx=0.1, rely=0.133, relheight=0.4, relwidth=0.4)
		BfGpioLabelframe.configure(relief='groove')
		BfGpioLabelframe.configure(foreground="black")
		BfGpioLabelframe.configure(text='''HW BF''')
		BfGpioLabelframe.configure(width=260)
		
		self.beamBfRstButton = tk.Button(BfGpioLabelframe, text="BF RST", command=lambda : self.bfRst(), width=8)
		self.beamBfRtnButton = tk.Button(BfGpioLabelframe, text="BF RTN", command=lambda : self.bfRtn(), width=8)
		self.beamBfIncButton = tk.Button(BfGpioLabelframe, text="BF INC", command=lambda : self.bfInc(), width=8)
		self.beamBfRstButton.pack(side="left", fill="both", pady=10, padx=40, anchor="n")
		self.beamBfRtnButton.pack(side="left", fill="both", pady=10, padx=40, anchor="n")
		self.beamBfIncButton.pack(side="left", fill="both", pady=10, padx=40, anchor="n")
		BfGpioLabelframe.pack(side="top", fill="both", anchor="n")
		gpioBeambookPage.pack(side="top", fill="both", anchor="n")

		# AGC controls
		if RXTXMODE == "RX":
			agcPage = p.Page(self)

			AgcLabelframe = tk.LabelFrame(agcPage)
			AgcLabelframe.place(relx=0.1, rely=0.133, relheight=0.4, relwidth=0.4)
			AgcLabelframe.configure(relief='groove')
			AgcLabelframe.configure(foreground="black")
			AgcLabelframe.configure(text='Internal AGC')
			AgcLabelframe.configure(width=360)

			AgcFirstRowFrame = tk.Frame(AgcLabelframe)

			if self.controller.eder.rx.agc.internal_agc_on == False:
				self.agcEnableButtonText = 'Enable'
			else:
				self.agcEnableButtonText = 'Disable'
			self.agcEnableButton = tk.Button(AgcFirstRowFrame, text=self.agcEnableButtonText, command=lambda : self.agcEnable(), width=8)
			self.agcStartButton = tk.Button(AgcFirstRowFrame, text="Start", command=lambda : self.agcStart(), width=8)
			self.agcClkCheckboxChecked = tk.IntVar()
			self.agcClkCheckbox = tk.Checkbutton(AgcFirstRowFrame, text='Reduced clk freq.', variable=self.agcClkCheckboxChecked)
			canvas_width = 20
			canvas_height = 20
			radius = 6
			self.AgcLedCanvas = tk.Canvas(AgcFirstRowFrame, width=canvas_width, height=canvas_height)
			x0 = (canvas_width / 2) - radius
			y0 = (canvas_height / 2) - radius
			x1 = (canvas_width / 2) + radius
			y1 = (canvas_height / 2) + radius
			self.AgcLedCircle = self.AgcLedCanvas.create_oval(x0, y0, x1, y1, width=1, fill='black')

			self.agcEnableButton.pack(side="left", pady=5, padx=4, anchor="w")
			self.agcStartButton.pack(side="left", pady=5, padx=4, anchor="w")
			self.agcClkCheckbox.pack(side="left", pady=5, padx=4, anchor="w")
			self.AgcLedCanvas.pack(side="left", pady=5, padx=4, anchor="w")
			AgcFirstRowFrame.pack(side='top', anchor="w")
			AgcLabelframe.pack(side="top", fill="both", anchor="n")
			agcPage.pack(side="top", fill="both", anchor="n")

		# ALC controls
		if RXTXMODE == "TX":
			alcPage = p.Page(self)

			AlcLabelframe = tk.LabelFrame(alcPage)
			AlcLabelframe.place(relx=0.1, rely=0.133, relheight=0.4, relwidth=0.4)
			AlcLabelframe.configure(relief='groove')
			AlcLabelframe.configure(foreground="black")
			AlcLabelframe.configure(text='ALC')
			AlcLabelframe.configure(width=260)

			FirstRowFrame = tk.Frame(AlcLabelframe)

			self.alcEnableButton = tk.Button(FirstRowFrame, text="Enable", command=lambda : self.alcEnable(), width=8)
			self.alcInitButton = tk.Button(FirstRowFrame, text="Init", command=lambda : self.alcInit(), width=8)
			alcPdetLabel = tk.Label(FirstRowFrame, text='Power Detector')
			self.AlcPdetCombobox = ttk.Combobox(FirstRowFrame, width=2)
			self.AlcPdetCombobox.configure(values=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
			self.AlcPdetCombobox.configure(takefocus="")
			self.AlcPdetCombobox.current(8)

			self.alcEnableButton.pack(side="left", pady=5, padx=4, anchor="w")
			self.alcInitButton.pack(side='left', pady=5, padx=4, anchor="n")
			alcPdetLabel.pack(side="left", pady=5)
			self.AlcPdetCombobox.pack(side="left", pady=5, padx=1)
			FirstRowFrame.pack(side='top', anchor="w")

			self.alcStartButton = tk.Button(AlcLabelframe, text="Start", command=lambda : self.alcStart(), width=8)
			self.alcStopButton = tk.Button(AlcLabelframe, text="Stop", command=lambda : self.alcStop(), width=8)
			self.alcTrimLowButton = tk.Button(AlcLabelframe, text="Trim Low", command=lambda : self.alcTrimLow(), width=8)
			self.alcTrimHighButton = tk.Button(AlcLabelframe, text="Trim High", command=lambda : self.alcTrimHigh(), width=8)
			self.alcPauseButton = tk.Button(AlcLabelframe, text="Pause", command=lambda : self.alcPause(), width=8)
			self.alcResumeButton = tk.Button(AlcLabelframe, text="Resume", command=lambda : self.alcResume(), width=8)
			self.alcStartButton.pack(side="left", fill="x", pady=5, padx=4, anchor="n")
			self.alcStopButton.pack(side="left", fill="x", pady=5, padx=4, anchor="n")
			self.alcTrimLowButton.pack(side="left", fill="x", pady=5, padx=4, anchor="n")
			self.alcTrimHighButton.pack(side="left", fill="x", pady=5, padx=4, anchor="n")
			self.alcPauseButton.pack(side="left", fill="x", pady=5, padx=4, anchor="n")
			self.alcResumeButton.pack(side="left", fill="x", pady=5, padx=4, anchor="n")

			AlcLabelframe.pack(side="top", fill="both", anchor="n")
			alcPage.pack(side="top", fill="both", anchor="n")


		self.controller.eder.check()

	def _getFreqVar(self):
		try:
			var = float(self.dict[self.freq.get()])
			return var
		except:
			print "Invalid output"
			return 0


	def setButtonStates(self, button_state):
		self.Button.config(state=button_state)
		self.CalButton.config(state=button_state)
		self.resetButton.config(state=button_state)
		self.beamStearingButton.config(state=button_state)
		self.beamResetButton.config(state=button_state)
		self.regDumpButton.config(state=button_state)
		self.freqDropDown.config(state=button_state)
		self.beamBfIncButton.config(state=button_state)
		self.beamBfRstButton.config(state=button_state)
		self.beamBfRtnButton.config(state=button_state)
		if self.mode == 'RX':
			self.agcEnableButton.config(state=button_state)
			self.agcStartButton.config(state=button_state)
			self.agcClkCheckbox.config(state=button_state)
		elif self.mode == 'TX':
			self.alcInitButton.config(state=button_state)
			self.alcEnableButton.config(state=button_state)
			self.alcStartButton.config(state=button_state)
			self.alcStopButton.config(state=button_state)
			self.alcTrimHighButton.config(state=button_state)
			self.alcTrimLowButton.config(state=button_state)
			self.AlcPdetCombobox.config(state=button_state)
			self.alcPauseButton.config(state=button_state)
			self.alcResumeButton.config(state=button_state)
		try:
			self.updatePowerButton.config(state=button_state)
		except:
			pass

	def UpdateGuiTxRx(self, guiState=None):
		global MAINVIEW
		tabs = MAINVIEW.nb.tabs()
		if guiState == None:
			if self.guiState != None:
				guiState = self.guiState
			else:
				return
		if guiState == 'RX':
			MAINVIEW.nb.hide(tabs[1])
			self.state_str.set("State: RX Enabled")
			self.Button.config(text='Disable RX')
			self.setButtonStates('normal')
		elif guiState == 'TX':
			MAINVIEW.nb.hide(tabs[0])
			self.state_str.set("State: TX Enabled")
			self.Button.config(text='Disable TX')
			self.setButtonStates('normal')
		elif guiState == 'WAIT':
			self.setButtonStates('disabled')
			if self.mode == 'RX':
				MAINVIEW.nb.hide(tabs[1])
			elif self.mode == 'TX':
				MAINVIEW.nb.hide(tabs[0])
		elif guiState == 'WAIT_LO_CALIB':
			self.setButtonStates('disabled')
			if self.mode == 'RX':
				MAINVIEW.nb.hide(tabs[1])
			elif self.mode == 'TX':
				self.state_str.set("State: TX Calib.")
				MAINVIEW.nb.hide(tabs[0])
		elif guiState == 'DISABLED':
			MAINVIEW.nb.add(tabs[0])
			MAINVIEW.nb.add(tabs[1])
			self.state_str.set("State: IDLE")
			if self.mode == 'RX':
				self.Button.config(text='Enable RX')
				self.resetAgcGui()
			elif self.mode == 'TX':
				self.Button.config(text='Enable TX')
			self.setButtonStates('normal')

	def setGuiState(self, state):
		self.guiState = state

	@_postPoll
	def ederReset(self):
		self.TH.put(lambda : self.setGuiState('WAIT'))
		self.TH.put(lambda : self.controller.ederReset())
		self.TH.put(lambda : time.sleep(3))
		self.TH.put(lambda : self.setGuiState('DISABLED'))

	@_postPoll
	def rxSetup(self):
		global BUSY
		BUSY = True
		self.controller.setMode('RX')
		if self.controller.eder.mode == None:
			self.TH.put(lambda : self.setGuiState('WAIT'))
			freq = self._getFreqVar()
			self.TH.put(lambda : self.controller.rxSetup(freq))
			self.TH.put(lambda : self.controller.rxEnable())
			self.TH.put(lambda : self.setGuiState('RX'))
		elif self.controller.eder.mode == 'RX':
			self.TH.put(lambda : self.setGuiState('DISABLED'))
			self.TH.put(lambda : self.controller.rxDisable())
		BUSY = False

	@_postPoll
	def txSetup(self):
		self.controller.setMode('TX')
		if self.controller.eder.mode == None:
			self.TH.put(lambda : self.setGuiState('TX'))
			freq = self._getFreqVar()
			self.TH.put(lambda : self.controller.txSetup(freq))
			self.TH.put(lambda : self.controller.txEnable())
		elif self.controller.eder.mode == 'TX':
			self.TH.put(lambda : self.setGuiState('DISABLED'))
			self.TH.put(lambda : self.controller.txDisable())

	def setBeambook(self):
		angle = self.stearingVal.get()
		print 'Beam angle set to ' + str(angle) + ' deg'
		if self.mode == 'TX':
			self.controller.beambookStearTx(angle)
		elif self.mode == 'RX':
			self.controller.beambookStearRx(angle)

	def resetBeam(self):
		print 'Beam angle set to ' + str(0) + ' deg'
		self.stearingVal.set(0)
		if self.mode == 'TX':
			self.controller.beambookStearTx(0)
		elif self.mode == 'RX':
			self.controller.beambookStearRx(0)

	def bfRst(self):
		self.controller.bfRst()

	def bfInc(self):
		self.controller.bfInc()

	def bfRtn(self):
		self.controller.bfRtn()

	@_postPoll
	def agcEnable(self):
		if self.agcClkCheckboxChecked.get():
			self.controller.eder.rx.agc.reduced_ref_clk(True)
		else:
			self.controller.eder.rx.agc.reduced_ref_clk(False)

		if self.controller.eder.rx.agc.internal_agc_on == False:
			self.controller.eder.rx.agc.enable_int(True)
			self.AgcLedCanvas.itemconfig(self.AgcLedCircle, fill='red')
			self.agcClkCheckbox.configure(state='disabled')
			self.agcEnableButtonText = 'Disable'
		else:
			self.controller.eder.rx.agc.enable_int(False)
			self.AgcLedCanvas.itemconfig(self.AgcLedCircle, fill='black')
			self.agcClkCheckbox.configure(state='normal')
			self.agcEnableButtonText = 'Enable'
		self.agcEnableButton.configure(text=self.agcEnableButtonText)

	def agcStart(self):
		self.controller.eder.rx.agc.start_int()

	def resetAgcGui(self):
		self.agcEnableButton.configure(text='Enable')
		self.AgcLedCanvas.itemconfig(self.AgcLedCircle, fill='black')

	def alcInit(self):
		self.controller.alcInit()
		self.controller.alcPdetSrcSet(self.AlcPdetCombobox.current())

	def alcEnable(self):
		if not self.alcEnabled:
			self.alcEnabled = True
			self.controller.alcEnable()
			self.controller.alcPdetSrcSet(self.AlcPdetCombobox.current())
			self.alcEnableButton.configure(text='Disable')
		else:
			self.alcEnabled = False
			self.controller.alcDisable()
			self.alcEnableButton.configure(text='Enable')

	def alcStart(self):
		self.controller.alcStart()

	def alcStop(self):
		self.controller.alcStop()

	def alcTrimHigh(self):
		if self.controller.getMode() == 'TX':
			self.TH.put(lambda : self.setGuiState('WAIT'))
			pdetNum = self.AlcPdetCombobox.current()
			self.TH.put(lambda : self.controller.alcTrimHigh(pdetNum, 1000))
			self.TH.put(lambda : self.setGuiState('TX'))

	def alcTrimLow(self):
		if self.controller.getMode() == 'TX':
			self.TH.put(lambda : self.setGuiState('WAIT'))
			pdetNum = self.AlcPdetCombobox.current()
			self.TH.put(lambda : self.controller.alcTrimLow(pdetNum, 1000))
			self.TH.put(lambda : self.setGuiState('TX'))

	def alcPause(self):
		self.controller.alcPause()

	def alcResume(self):
		self.controller.alcResume()

	@_postPoll
	def rxBbDcCal(self):
		global BUSY
		BUSY = True
		self.TH.put(lambda : self.setGuiState('WAIT'))
		self.TH.put(lambda : self.controller.rxBbDcCal())
		trx_ctrl = self.controller.eder.regs.rd('trx_ctrl')
		if trx_ctrl & 0x01:
			self.mode = 'RX'
		else:
			self.mode = 'DISABLED'
		if self.mode == 'RX':
			self.TH.put(lambda : self.setGuiState('RX'))
		else:
			self.TH.put(lambda : self.setGuiState('DISABLED'))
		BUSY = False

	@_postPoll
	def txLoLeakCal(self):
		global BUSY
		BUSY = True
		self.TH.put(lambda : self.setGuiState('WAIT_LO_CALIB'))
		if self.controller.txEnabled() == False:
			print 'TX must be Enabled prior to TX LO leakage calibration'
			self.TH.put(lambda : self.setGuiState('DISABLED'))
		else:
			self.TH.put(lambda : self.controller.txLoLeakCal())
			self.TH.put(lambda : self.setGuiState('TX'))
		BUSY = False

	def regDump(self):
		self.controller.registerDump()

	def txPowerMeasurement(self):
		powerStr = 'Total TX Power ' + str(self.controller.txPowerMeasurement()) + ' dBm'
		self.powerLabel.config(text=powerStr)

class ValueShower(p.Page):
	def __init__(self, parent, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)


# This class is a button within a frame, this button brings up the connected registers controls.
class RegFrame(p.Page):
	def __init__(self, mode, groupName, registerName, parent,  callback, controller, TH, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)
                self.mode = mode
		self.name = registerName
		self.groupName = groupName
		self.variable = tk.StringVar()
		self.variable.set(hex(controller.getRegisterValue(mode, groupName, registerName)))
		self.button = tk.Button(self, text=registerName, anchor="w", command=callback, relief = "flat",overrelief="groove",  pady =2)
		#self.button = tk.Button(self, text=registerName, anchor="w", command=lambda: TH.put(lambda : callback), relief = "flat",overrelief="groove",  pady =2) # $$$
		self.text = tk.Label(self, textvariable=self.variable, anchor="e")
		self.button.pack(side="left",  fill="both")
		self.text.pack(side="right")

	def getButton(self):
		return self.button

	def updateValue(self, controller):
		#print(self.register.calculateValue())
		self.variable.set(hex(controller.getRegisterValue(self.mode, self.groupName, self.name)))



# This class is responsible for showing register controls.
class RegControlFrame(p.Page):
	def __init__(self, mode, groupName, registerName, controlName, parent, registerFrame, controller):
		p.Page.__init__(self, parent)
                self.mode = mode
		self.name = controlName
		self.registerName = registerName
		self.groupName = groupName
		self.registerFrame = registerFrame
		self.var = tk.IntVar()
		self.hexVar = tk.StringVar()
		self.controller = controller
		self.var.set(controller.getControlValue(mode, groupName, registerName, controlName))
		self.text = str(self.name) + ", Bit: " + str(controller.getControlEndBit(mode, groupName, registerName, self.name))
                self.just_started = True
		if controller.getControlEndBit(mode, groupName, registerName, controlName) == controller.getControlStartBit(mode, groupName, registerName, controlName):
			self.check = tk.Checkbutton(self, text=self.text, variable=self.var, anchor="w", command=lambda controller : self.updateValue(controller)) # $$$ FIXED
		else:
			self.text += ":" + str(controller.getControlStartBit(mode, groupName, registerName, controlName))
			self.check = tk.Entry(self, text=self.text, textvariable=self.hexVar)
			self.check.bind('<Return>', self.enterKeyPressed)
			label=tk.Label(self,text=self.text, anchor="e")
			label.grid(row=0,column=1,sticky="nsew")
			#self.hexVar.trace('w', lambda name, idx, mode, control=controller: self.hexUpdate(controller))
			self.hexVar.set("0x")
		self.check.grid(row=0, column=0, sticky="nsew")

	def enterKeyPressed(self, event):
		self.hexUpdate(self.controller)

	def hexUpdate(self, controller):
		# Calculates the value of the register and updates the text.
		# print("Updating value of register", registerFrame).
		number = self.hexVar.get()
		if number == "0x":
			self.var.set(0)
		else:
			self.var.set(int(number, 16))
                if self.just_started == False:
			controller.setControlValue(self.mode, self.groupName, self.registerName, self.name, self.var.get())
                else:
			self.just_started = False
		self.registerFrame.updateValue(controller)

	def updateValue(self, controller):
		# Calculates the value of the register and updates the text.
		# print("Updating value of register", registerFrame).
		controller.setControlValue(self.groupName, self.registerName, self.name, self.var.get())
		self.registerFrame.updateValue(controller)

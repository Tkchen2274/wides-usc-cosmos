import Page as p
import Tkinter as tk
import ttk
import Variables as var
import terminalWindow
import sys
sys.path.insert(0, '..')
sys.path.insert(0,'../')

MAINVIEW = 0


class RxTxView(p.Page):
	def __init__(self, parent, controller, TH, mode, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)
		self.mode = mode
		self.lastPressed = None
		self.TH = TH
		self.controller = controller
		upper = p.Page(parent)
		self.nb = ttk.Notebook(upper)

		
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

		#TerminalWindow
		terminalPage = p.Page(parent)
		text = tk.Text(terminalPage, height=100)
		self.terminal = terminalWindow.Std_redirector(text)

		# Add buttonbar to the left of everything
		buttonBar = ModePage(upper, self.controller, self.TH, self.mode, self.terminal)


		# Terminal input.
		self.ederInput = tk.StringVar()
		inputFrame = tk.Frame(terminalPage)
		inputField = tk.Entry(inputFrame, textvariable = self.ederInput)
		self.ederInput.set("Type command here and press Run")
		sendCommandButton = tk.Button(inputFrame, text="Run", width=10, command=lambda :self.TH.put(lambda:self.runEder()))
                clearButton = tk.Button(inputFrame, text="Clear", width=10, command=lambda :self.TH.put(lambda:self.clearWindow()))


		# Polling checkbox
		#self.pollCheck = PollCheckbox(upper)
                registerUpdateButton = tk.Button(upper, text="Refresh registers", width=12, command=lambda :self.TH.put(lambda:self.controller.updateRegisters(self)))


		# Pack it up!
		

		self.nb.pack(side="right",fill="both")
		buttonBar.pack(side="left", fill="x")
		#self.pollCheck.pack(side="right", anchor="n")

		inputField.pack(side="left", fill="both", expand="true")
                clearButton.pack(side="right")
		sendCommandButton.pack(side="right")
		inputFrame.pack(side="bottom", fill="x")
		text.pack(side="bottom", fill="both", expand="true")

		upper.pack(side="top", fill="x")
		terminalPage.pack(side="bottom", fill="both", expand="true")

                registerUpdateButton.pack(side=tk.RIGHT)

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
				registerFrame = RegFrame(self.mode, groupName, registerName,self.pages[groupName], lambda groupName=groupName, regName=registerName: self.showFrame(groupName, regName), self.controller)
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

	def poll(self, root):
		pass
		#if self.pollCheck.pollVar.get():
		#	self.controller.updateRegisters(self)
		#else:
		#	root.after(5000, lambda root = root: self.poll(root))

	def hideFrame(self, groupName):
		self.lastPressed.config(relief="flat")
		self.lastPressed = None
		# print("showing empty page").
		self.hidePages[groupName].show()

	def showFrame(self, groupName, registerName):
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

	def runEder(self): 
		code = self.ederInput.get()
		#print "Running code"
		sys.stdout = self.terminal
		sys.stderr = self.terminal

		self.ederInput.set('')
		self.controller.runPythonCode(code)

        def clearWindow(self):
            self.terminal.clear()

class PollCheckbox(p.Page):
	def __init__(self, parent, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)
		self.pollVar = tk.BooleanVar()
		self.checkButton = tk.Checkbutton(self, text="Polling", variable=self.pollVar, onvalue=True, offvalue=False)
		self.checkButton.pack()
		self.pollVar.set(False)

		
class ModePage(p.Page):
	def __init__(self, parent, controller, TH, RXTXMODE, terminal, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)
		# Frequency input.
		self.terminal = terminal
		self.controller = controller
                self.mode = RXTXMODE
		FreqModePage = p.Page(self, borderwidth=1)
		TopPage = p.Page(FreqModePage)
		self.freq = tk.StringVar()
		self.freqLabel = tk.Label(TopPage,text="WiGig Channel:")
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
		FreqModePage.pack(side="top", anchor="w", fill="both")

		# Buttons
		Buttonpage = p.Page(self, pady=5)
		if RXTXMODE == "RX":
			self.Button = tk.Button(Buttonpage, text="Enable RX", command= lambda: TH.put(lambda : self.rxSetup()))
			self.CalButton = tk.Button(Buttonpage, text="RX BB DC Offset Cal", command = lambda: TH.put(lambda : self.rxBbDcCal()))
		else:
			self.Button = tk.Button(Buttonpage, text="Enable TX", command= lambda: TH.put(lambda : self.txSetup()))
			self.CalButton = tk.Button(Buttonpage, text="LO Leakage Cal", command = lambda: TH.put(lambda : self.txLoLeakCal()))
		self.resetButton = tk.Button(Buttonpage, text="Reset TRX-BF01", command= lambda: TH.put(lambda : self.ederReset()))
                self.regDumpButton = tk.Button(Buttonpage, text="List registers", command= lambda: TH.put(lambda : self.regDump()))


		self.resetButton.pack(side="left", anchor="n", fill = "x", expand=True)
                self.regDumpButton.pack(side="left", anchor="n", fill = "x", expand=True)
		self.Button.pack(side="left", anchor="n", fill = "x", expand=True)
		self.CalButton.pack(side="left", anchor="n", fill = "x", expand=True)
		Buttonpage.pack(side="top", fill="x")
               
                # Infomation page
                if RXTXMODE == "TX":
                    infopage = p.Page(self, borderwidth=2, relief=tk.GROOVE)
                    self.updatePowerButton = tk.Button(infopage, text="Measure TX power", command= lambda: TH.put(lambda : self.txPowerMeasurement()))
                    self.updatePowerButton.pack(side="left", anchor="n", fill = tk.NONE, expand=False)
                    self.powerLabel = tk.Label(infopage, text="Total TX Power _ dBm", justify=tk.RIGHT)
                    self.powerLabel.pack(side="left", fill="both", anchor="n", padx=20)
                    infopage.pack(side="top", fill="both", anchor="n")
		
		# Beambook stearing with slider
		beambookPage = p.Page(self)
		self.stearingVal = tk.DoubleVar()
		titleLabel = tk.Label(beambookPage, text="Beam angle Control (degrees)")
		self.scale = tk.Scale(beambookPage, orient="horizontal", from_=-45, to = 45, tickinterval=15, variable = self.stearingVal, resolution=var._BEAMBOOKSLIDERRESOLUTION, digits=var._BEAMBOOKSLIDERPRECISION)
		self.beamStearingButton = tk.Button(beambookPage, text="Set beam angle", command=lambda: TH.put(lambda : self.setBeambook()))



		titleLabel.pack(side="top", fill="both", anchor="n")
		self.scale.pack(side="top", fill="both", anchor="n")
		self.beamStearingButton.pack(side="top", fill="both", anchor="n")
		beambookPage.pack(side="top", fill="both", anchor="n")

                self.setOutput()
                self.controller.eder.check()

	def _getFreqVar(self):
		try:
			
			var = float(self.dict[self.freq.get()])
			return var
		except:
			print "Invalid output"
			return 0

	def setOutput(self):
		self.controller.eder.logger.log_info = lambda string, indent=0: self.terminal.log_info(string, indent)
		sys.stderr = self.terminal
		sys.stdout = self.terminal

        def setButtonStates(self, button_state):
            self.Button.config(state=button_state)
            self.CalButton.config(state=button_state)
            self.resetButton.config(state=button_state)
            self.beamStearingButton.config(state=button_state)
            self.regDumpButton.config(state=button_state)
            self.freqDropDown.config(state=button_state)
            try:
                self.updatePowerButton.config(state=button_state)
            except:
                pass

        def UpdateGuiTxRx(self, mode):
		global MAINVIEW
                tabs = MAINVIEW.nb.tabs()            
		if mode == 'RX':
                    MAINVIEW.nb.hide(tabs[1])
                    MAINVIEW.setMainViewTitle("   *** RX enabled ***")
                    self.Button.config(text='Disable RX')
                    self.setButtonStates('normal')
                elif mode == 'TX':
                    MAINVIEW.nb.hide(tabs[0])
                    MAINVIEW.setMainViewTitle("   *** TX enabled ***")
                    self.Button.config(text='Disable TX')
                    self.setButtonStates('normal')
                elif mode == 'WAIT':
                    self.setButtonStates('disabled')
                    if self.mode == 'RX':
                        MAINVIEW.nb.hide(tabs[1])
                    elif self.mode == 'TX':
                        MAINVIEW.nb.hide(tabs[0])
                elif mode == 'WAIT_LO_CALIB':
                    self.setButtonStates('disabled')
                    if self.mode == 'RX':
                        MAINVIEW.nb.hide(tabs[1])
                    elif self.mode == 'TX':
                        MAINVIEW.setMainViewTitle("   *** TX LO Leakage Calibration Running ***")
                        MAINVIEW.nb.hide(tabs[0])
                elif mode == 'DISABLED':
                    MAINVIEW.nb.add(tabs[0])
                    MAINVIEW.nb.add(tabs[1])
                    MAINVIEW.setMainViewTitle()
                    if self.mode == 'RX':
                        self.Button.config(text='Enable RX')
                    elif self.mode == 'TX':
                        self.Button.config(text='Enable TX')
                    self.setButtonStates('normal')

	def ederReset(self):
                self.UpdateGuiTxRx('WAIT')
		self.setOutput()
		self.controller.ederReset()
                self.UpdateGuiTxRx('DISABLED')

	def rxSetup(self):
            self.controller.setMode('RX')
            if self.controller.eder.mode == None:
                self.UpdateGuiTxRx('WAIT')
                self.setOutput()
		freq = self._getFreqVar()
		self.controller.rxSetup(freq)
                self.controller.rxEnable()
                self.UpdateGuiTxRx('RX')
            elif self.controller.eder.mode == 'RX':
                self.UpdateGuiTxRx('DISABLED')
		self.setOutput()
		self.controller.rxDisable()


	def txSetup(self):
            self.controller.setMode('TX')
            if self.controller.eder.mode == None:
                self.UpdateGuiTxRx('TX')
		self.setOutput()
		freq = self._getFreqVar()
		self.controller.txSetup(freq)
                self.controller.txEnable()
            elif self.controller.eder.mode == 'TX':
                self.UpdateGuiTxRx('DISABLED')
		self.setOutput()
		self.controller.txDisable()

	def setBeambook(self):
		self.setOutput()
		angle = self.stearingVal.get()
                print 'Beam angle set to ' + str(angle) + ' deg'
                if self.mode == 'TX':
		    self.controller.beambookStearTx(angle)
                elif self.mode == 'RX':
		    self.controller.beambookStearRx(angle)

	def rxBbDcCal(self):
                self.UpdateGuiTxRx('WAIT')
		self.setOutput()
		self.controller.rxBbDcCal()
                tx_rx_sw_ctrl = self.controller.eder.regs.rd('tx_rx_sw_ctrl')
                if tx_rx_sw_ctrl & 0x02:
                    self.mode = 'RX'
                else:
                    self.mode = 'DISABLED'
                if self.mode == 'RX':
                    self.UpdateGuiTxRx('RX')
                else:
                    self.UpdateGuiTxRx('DISABLED')

	def txLoLeakCal(self):
                self.UpdateGuiTxRx('WAIT_LO_CALIB')
		self.setOutput()
		if self.controller.txLoLeakCal() == False:
                    print 'TX must be Enabled prior to TX LO leakage calibration'
                    self.UpdateGuiTxRx('DISABLED')
                else:
                    self.UpdateGuiTxRx('TX')

        def regDump(self):
		self.setOutput()
		self.controller.registerDump()

        def txPowerMeasurement(self):
            self.setOutput()
            powerStr = 'Total TX Power ' + str(self.controller.txPowerMeasurement()) + ' dBm'
            self.powerLabel.config(text=powerStr)

class ValueShower(p.Page):
	def __init__(self, parent, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)


# This class is a button within a frame, this button brings up the connected registers controls.
class RegFrame(p.Page):
	def __init__(self, mode, groupName, registerName, parent,  callback, controller, *args, **kwargs):
		p.Page.__init__(self, parent, *args, **kwargs)
                self.mode = mode
		self.name = registerName
		self.groupName = groupName
		self.variable = tk.StringVar()
		self.variable.set(hex(controller.getRegisterValue(mode, groupName, registerName)))
		self.button = tk.Button(self, text=registerName, anchor="w", command=callback, relief = "flat",overrelief="groove",  pady =2)
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
		self.var.set(controller.getControlValue(mode, groupName, registerName, controlName))
		self.text = str(self.name) + ", Bit: " + str(controller.getControlEndBit(mode, groupName, registerName, self.name))
                self.just_started = True
		if controller.getControlEndBit(mode, groupName, registerName, controlName) == controller.getControlStartBit(mode, groupName, registerName, controlName):
			self.check = tk.Checkbutton(self, text=self.text, variable=self.var, anchor="w", command=lambda: self.updateValue(controller))
		else:
			self.text += ":" + str(controller.getControlStartBit(mode, groupName, registerName, controlName))
			self.check = tk.Entry(self, text=self.text, textvariable=self.hexVar)
			label=tk.Label(self,text=self.text, anchor="e")
			label.grid(row=0,column=1,sticky="nsew")
			#self.hexVar.trace('w', lambda name, idx, mode, control=controller: self.hexUpdate(controller))
			self.hexVar.set("0x")
		self.check.grid(row=0, column=0, sticky="nsew")

	def hexUpdate(self, controller):
		# Calculates the value of the register and updates the text.
		# print("Updating value of register", registerFrame).
		number = self.hexVar.get()
		if number == "0x":
			self.var.set(0)
		else:
			self.var.set(int(number[2:], 16))
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

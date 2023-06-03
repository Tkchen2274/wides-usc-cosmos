import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../')

import eder
import eeprom
import FuncThread as FT
from random import randint
import re
import eder_logger

PAUSE_TEMP_MEAS = False

class Controller():
    def __init__(self, chipRx, chipTx, view, mbtype, sn, mode):
      logFile = eder_logger.EderLogger("eder.info")
      self.mode = mode
      self.chipRx = chipRx
      self.chipTx = chipTx
      self.mbtype = mbtype
      self.eder = eder.Eder(unit_name=sn, board_type=mbtype)
      self.eder.temp.init()
      self.unsafe = re.compile('__.+__')
      self.function = re.compile('.+\(.+(,.+)*\)')
      self.params = re.compile('\(.+(,.+)*\)')
      self.savedVariables = {}
      self.pauseTempMeas = False

    def setMode(self, mode):
        self.mode = mode
        

    def ederReset(self):
        return self.eder.reset() 

    def getPcbTemp(self):
        global PAUSE_TEMP_MEAS
        if PAUSE_TEMP_MEAS == True:
            return self.oldPcbTemp
       # return randint(270,300)
        self.oldPcbTemp = int(self.eder.eeprom.read_pcb_temp())
        return self.oldPcbTemp
       # return randint(0,300)

    def getTemp(self):
        global PAUSE_TEMP_MEAS
        if PAUSE_TEMP_MEAS == True:
          return self.oldChipTemp
      #  return randint(270,300)
        self.oldChipTemp = int(self.eder.temp.run())
        return self.oldChipTemp

    def _getControl(self,groupName, registerName, controlName, mode):
        if mode == 'TX':
            return self.chipTx.getGroup(groupName).getRegister(registerName).getControl(controlName)
        elif mode == 'RX':
            return self.chipRx.getGroup(groupName).getRegister(registerName).getControl(controlName)

    def setControlValue(self, mode, groupName, registerName, controlName, value):
        control = self._getControl(groupName, registerName, controlName, mode)
        regValue = int(value)
        self.eder.regs.wr(registerName, regValue)
        newValue = self.eder.regs.rd(registerName)
        control.setValue(newValue)
        # Set controlFrame variable value

    def getControlValue(self, mode, groupName, registerName, controlName):
        control = self._getControl(groupName, registerName, controlName, mode)
        return control.getValue()

    def getControlStartBit(self, mode, groupName, registerName, controlName):
        control = self._getControl(groupName, registerName, controlName, mode)
        return control.getStartBit()

    def getControlEndBit(self, mode, groupName, registerName, controlName):
        control = self._getControl(groupName, registerName, controlName, mode)
        return control.getEndBit() - 1

    def getRegisterValue(self, mode, groupName, registerName):
        if mode == 'RX':
            register = self.chipRx.getGroup(groupName).getRegister(registerName)
        elif mode == 'TX':
            register = self.chipTx.getGroup(groupName).getRegister(registerName)
        return register.calculateValue()

    def getGroup(self, mode, groupName):
        if mode == 'RX':
            return self.chipRx.getGroup(groupName)
        elif mode == 'TX':
            return self.chipTx.getGroup(groupName)

    def getGroups(self, mode):
        if mode == 'RX':
            groups = self.chipRx.getGroups()
        elif mode == 'TX':
            groups = self.chipTx.getGroups()
        nameList = []
        for group in groups:
            nameList.append(group.getName())
        return nameList

    def getRegisters(self, mode, groupName):
        if mode == 'RX':
            group = self.chipRx.getGroup(groupName)
        elif mode == 'TX':
            group = self.chipTx.getGroup(groupName)
        nameList = []
        for name in group.getRegisters():
            nameList.append(name)
        return nameList

    def getRegister(self, mode, groupName, registerName):
        if mode == 'RX':
            group = self.chipRx.getGroup(groupName)
        elif mode == 'TX':
            group = self.chipTx.getGroup(groupName)
        register = group.getRegister(registerName)
        return register.getName()

    def getControls(self, mode, groupName, registerName):
        if mode == 'RX':
            group = self.chipRx.getGroup(groupName)
        elif mode == 'TX':
            group = self.chipTx.getGroup(groupName)
        register = group.getRegister(registerName)
        nameList = []
        for name in register.getControls():
            nameList.append(name)
        return nameList

    def setRegisterValue(self, mode, groupName, registerName, value, view):

        group = self.getGroup(mode, groupName)
        
        
        register = group.getRegister(registerName)
        for controlKey in register.getControls():
            control = register.getControl(controlKey)
            stringBits = "0"
            startBit = control.getEndBit()
            for x in range(0, control.getStartBit()):
                stringBits += "0"
            while(startBit > control.getStartBit()):
                stringBits += "1"
                startBit -= 1
            
            wantedBits = int(stringBits, 2)
            controlValue = value & wantedBits
            control.setValue(controlValue)
            if view.regControlFrames[groupName][registerName][controlKey].check != view.regControlFrames[groupName][registerName][controlKey].focus_get():
                view.regControlFrames[groupName][registerName][controlKey].hexVar.set(hex(controlValue))

    def updateRegisters(self, view):
        #print "Updating registers"
        if view.mode == 'RX':
            chip = self.chipRx
        else:
            chip = self.chipTx
        for group in chip.getGroups():
            for registerKey in group.getRegisters():
                register = group.getRegister(registerKey)
                value = self.eder.regs.rd(register.getName())
                self.setRegisterValue(view.mode, group.getName(), register.getName(), value, view)
                #print "Updated register value"
                view.pageButtons[group.getName()][registerKey].variable.set(hex(value))

    #Button stuff
    def rxSetup(self, freq):
        #print "Initialising RX mode"
        global PAUSE_TEMP_MEAS
        PAUSE_TEMP_MEAS = True
        self.eder.rx_setup(freq)
        PAUSE_TEMP_MEAS = False

    def rxEnable(self):
        self.eder.rx_enable() 

    def rxDisable(self):
        #print "Disabling RX mode"
        self.eder.rx_disable()

    def txSetup(self, freq):
        #print "Initialising TX mode"
        self.eder.tx_setup(freq)

    def txEnable(self):
        self.eder.tx_enable()

    def txDisable(self):
        #print "Disabling TX mode"
        self.eder.tx_disable()

    def beambookStear(self, angle):
      angle = int( round((0.711111111111111*angle)+31) )
      if angle < 0: angle = 0
      if self.mode=="RX":
       self. eder.rx.set_beam(angle)
      else:
        self.eder.tx.set_beam(angle)

    def beambookStearTx(self, angle):
        angle = int( round((0.711111111111111*angle)+31) )
        if angle < 0: angle = 0
        self.eder.tx.set_beam(angle)

    def beambookStearRx(self, angle):
        angle = int( round((0.711111111111111*angle)+31) )
        if angle < 0: angle = 0
        self.eder.tx.set_beam(angle)
    
    def rxBbDcCal(self):
      global PAUSE_TEMP_MEAS
      PAUSE_TEMP_MEAS = True
      self.eder.rx.dco.run()
      PAUSE_TEMP_MEAS = False

    def txLoLeakCal(self):
      global PAUSE_TEMP_MEAS
      PAUSE_TEMP_MEAS = True
      if self.eder.regs.rd('trx_ctrl') & 0x2 == 0x2: 
          self.eder.tx.dco.run()
          PAUSE_TEMP_MEAS = False
          return True
      else:
          return False

    def registerDump(self):
        self.eder.regs.dump()

    def txPdetBias(self):
        return self.eder.pdet_bias

    def txPowerMeasurement(self):
        return self.eder.tx_pdet()

    def runPythonCode(self, code):
        #print "Running code..."
        if self.unsafe.match(code):
            return
        try:
            code = re.sub('eder', 'self.eder', code, 1)
            # Function is run, fix input variables:
            functionMatch = self.function.match(code)
            if functionMatch:
                paramMatch = self.params.search(code)
                if paramMatch:
                    paramsfull = paramMatch.group().replace('(','').replace(')','')
                    params = paramsfull.split(",")
                    newParams = ''
                    for param in params:
                        if param.strip() in self.savedVariables:
                            newParams += self.savedVariables[param]+","
                        else:
                            newParams+= param+","
                    newParams = str(newParams[:-1])
                    code = code.replace(str(paramsfull),newParams)
                    print code
                    code = 'exec_output =' + str(code)
                    variable, value = code.split("=",1)
                    variable = variable.strip()
                    value = value.strip()
                    exec('exec_output =' + str(code))
                    self.savedVariables.update({variable:exec_output})
                    print exec_output
            elif "=" in code:
                variable, value = code.split("=",1)
                variable = variable.strip()
                value = value.strip()
                exec('ret = "{}"'.format(value))
                self.savedVariables.update({variable:ret})
                print variable, "=", ret
            # Not a function or declaration, print it...
            elif '()' in code:
                exec('res = ' + code)
                print code
                if res != None:
                    print res
            else:
                print self.savedVariables[code.strip()]
        except Exception as e:
            print e
            print "Code could not be run. Check your syntax or the command is not yet supported"
        #print "Code run"


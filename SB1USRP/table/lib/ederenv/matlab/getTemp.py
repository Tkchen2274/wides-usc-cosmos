#!/usr/bin/python
import sys, os
import ast
import time
#sys.path.append('..//')
sys.path.append('/home/pi/projects/evaldrpi')
import eder
import argparse

#block printout
sys.stdout = open(os.devnull, 'w')

eder = eder.Eder()
#eder.adc.start(0x83)  # select amux #3 which is temperature
#time.sleep(0.01)
eder.temp.init()
temp = eder.temp.run()
#temp2 = eder.adc.mean(eder.adc.dump(16))
#enable printout
sys.stdout = sys.__stdout__
print temp
#print temp2
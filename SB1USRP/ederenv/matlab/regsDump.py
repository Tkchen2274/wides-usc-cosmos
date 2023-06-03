#!/usr/bin/python
import sys
import ast
#sys.path.append('..//')
sys.path.append('/home/pi/projects/eder')
import eder
import argparse

eder = eder.Eder()
dumper = eder.regs.dump(False)

for item in dumper:
    data = dumper[item]['value']
    width = 2*eder.regs.size(item)
    print '{:<22}: {:>18}'.format(item,'0x{:0{}X}'.format(data, width))

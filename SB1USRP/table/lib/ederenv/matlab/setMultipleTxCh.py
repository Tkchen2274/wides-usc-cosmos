#!/usr/bin/python

import sys
#sys.path.append('..//')
sys.path.append('/home/pi/projects/eder')
import eder
import argparse

eder = eder.Eder()

parser = argparse.ArgumentParser()
parser.add_argument("n",nargs="+" ,help = "Set 1 digit", type = int)
args = parser.parse_args()

print 'Selected channels: ',args.n
regs_val = 0
for i in range(0, len(args.n)):
    regs_val += 2**((args.n[i])-1)
regs_val += 2**16

eder.regs.wr('bias_ctrl_tx', regs_val)
print 'register read :', bin(eder.regs.rd('bias_ctrl_tx'))



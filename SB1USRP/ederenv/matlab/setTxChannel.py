#!/usr/bin/python

import sys, os
#sys.path.append('..//')
sys.path.append('/home/pi/projects/eder')
import eder
import argparse
sys.stdout = open(os.devnull, 'w')
eder = eder.Eder()

parser = argparse.ArgumentParser()
parser.add_argument("channel", help = "Set 1 digit", type = str)


input = parser.parse_args()


n=int(input.channel, 16)


eder.regs.wr('bias_ctrl_tx', (2**(n-1) + 2**16) )
sys.stdout = sys.__stdout__
print 'channel', n , ' active'
print 'channel', bin(eder.regs.rd('bias_ctrl_tx')) , ' active'


